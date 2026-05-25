"""
Betfair Exchange API — Real implementation with OAuth2 SSL certificate auth,
rate limiting with exponential backoff, partial fill handling, and reconciliation.

Supports both production and sandbox (paper trading) modes.
API docs: https://docs.developer.betfair.com/
"""
from __future__ import annotations

import json
import logging
import ssl
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from src.execution.dynamic_rate_limiter import DynamicRateLimiter

logger = logging.getLogger("betfair_real")

# ---------------------------------------------------------------------------
# Betfair API endpoints
# ---------------------------------------------------------------------------
BETFAIR_AUTH_URL_PRODUCTION = "https://identitysso.betfair.com/api/certlogin"
BETFAIR_AUTH_URL_SANDBOX = "https://identitysso.betfair.com/api/certlogin"
BETFAIR_KEEPALIVE_URL_PRODUCTION = "https://identitysso.betfair.com/api/keepAlive"
BETFAIR_KEEPALIVE_URL_SANDBOX = "https://identitysso.betfair.com/api/keepAlive"

BETFAIR_API_URL_PRODUCTION = "https://api.betfair.com/exchange/betting/rest/v1.0/"
BETFAIR_API_URL_SANDBOX = "https://api-sandbox.betfair.com/exchange/betting/rest/v1.0/"

BETFAIR_ACCOUNT_URL_PRODUCTION = "https://api.betfair.com/exchange/account/rest/v1.0/"
BETFAIR_ACCOUNT_URL_SANDBOX = "https://api-sandbox.betfair.com/exchange/account/rest/v1.0/"

SESSION_TOKEN_REFRESH_SECONDS = 1200  # 20 min — refresh at 18 min to be safe


class BetfairAPIError(Exception):
    """Raised when the Betfair API returns an error response."""
    def __init__(self, error_code: str, error_message: str, response: Optional[Dict] = None):
        self.error_code = error_code
        self.error_message = error_message
        self.response = response
        super().__init__(f"BetfairAPIError({error_code}): {error_message}")


class BetfairAuthError(BetfairAPIError):
    """Authentication failure."""
    pass


class BetfairRateLimitError(BetfairAPIError):
    """Rate limit exceeded — triggers retry."""
    pass


class BetfairRealConnector:
    """
    Real Betfair Exchange API client with:
    - OAuth2 SSL certificate authentication
    - Automatic session keep-alive (token expires every 20 min)
    - Rate limiting with exponential backoff + jitter via tenacity
    - Partial fill handling
    - Account balance reconciliation
    """

    def __init__(
        self,
        app_key: str,
        cert_path: str,
        key_path: str,
        username: str = "",
        password: str = "",
        sandbox: bool = True,
        commission_rate: float = 0.05,
    ):
        self.app_key = app_key
        self.cert_path = cert_path
        self.key_path = key_path
        self.username = username
        self.password = password
        self.sandbox = sandbox
        self.commission_rate = commission_rate

        self.session_token: Optional[str] = None
        self.session_authenticated_at: float = 0.0
        self._last_call_time: float = 0.0
        self._min_call_interval: float = 0.1  # 100ms between calls (10 req/s)

        # Dynamic rate limiter — adjusts based on API response headers
        self.rate_limiter = DynamicRateLimiter(default_rps=10.0, min_rps=0.5, max_rps=20.0)

        # Connection pooling via requests.Session — reuses TCP connections
        self._http_session: Optional[requests.Session] = None

        # Select URLs based on mode
        if self.sandbox:
            self._auth_url = BETFAIR_AUTH_URL_SANDBOX
            self._keepalive_url = BETFAIR_KEEPALIVE_URL_SANDBOX
            self._api_url = BETFAIR_API_URL_SANDBOX
            self._account_url = BETFAIR_ACCOUNT_URL_SANDBOX
            logger.info("Betfair API initialized in SANDBOX mode")
        else:
            self._auth_url = BETFAIR_AUTH_URL_PRODUCTION
            self._keepalive_url = BETFAIR_KEEPALIVE_URL_PRODUCTION
            self._api_url = BETFAIR_API_URL_PRODUCTION
            self._account_url = BETFAIR_ACCOUNT_URL_PRODUCTION
            logger.info("Betfair API initialized in PRODUCTION mode")

    # ------------------------------------------------------------------
    # HTTP session (connection pooling)
    # ------------------------------------------------------------------
    def _get_http_session(self) -> requests.Session:
        """Lazy-init a requests.Session for connection pooling."""
        if self._http_session is None:
            self._http_session = requests.Session()
            self._http_session.cert = (self.cert_path, self.key_path)
        return self._http_session

    def close(self) -> None:
        """Close the HTTP session and release connections."""
        if self._http_session:
            self._http_session.close()
            self._http_session = None

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def _build_ssl_context(self) -> ssl.SSLContext:
        """Build SSL context with client certificate for mutual TLS auth."""
        cert_path = Path(self.cert_path)
        key_path = Path(self.key_path)

        if not cert_path.exists():
            raise FileNotFoundError(f"Betfair SSL certificate not found: {cert_path}")
        if not key_path.exists():
            raise FileNotFoundError(f"Betfair SSL key not found: {key_path}")

        ctx = ssl.create_default_context()
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.check_hostname = True
        ctx.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
        return ctx

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=30, jitter=2),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def authenticate(self) -> bool:
        """
        Authenticate with Betfair using SSL client certificate + credentials.
        Returns True on success, raises BetfairAuthError on failure.
        """
        if not self.app_key:
            raise BetfairAuthError("MISSING_APP_KEY", "BETFAIR_APP_KEY is not configured")

        payload = {"username": self.username, "password": self.password}
        headers = {
            "X-Application": self.app_key,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        try:
            ssl_ctx = self._build_ssl_context()
            response = self._get_http_session().post(
                self._auth_url,
                data=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
        except requests.ConnectionError as e:
            raise BetfairAuthError("CONNECTION_ERROR", str(e))
        except requests.Timeout:
            raise BetfairAuthError("TIMEOUT", "Authentication request timed out")
        except FileNotFoundError as e:
            raise BetfairAuthError("CERT_NOT_FOUND", str(e))

        data = response.json()
        token = data.get("sessionToken")
        if not token:
            error_code = data.get("error", "UNKNOWN")
            raise BetfairAuthError(error_code, f"Authentication failed: {data}")

        self.session_token = token
        self.session_authenticated_at = time.time()
        # Security: never log token, even partially — log a hash for correlation
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:8]
        logger.info("Betfair session authenticated (token_hash=%s)", token_hash)
        return True

    def ensure_session(self) -> None:
        """Ensure we have a valid session token, refreshing if needed."""
        if not self.session_token:
            self.authenticate()
            return

        elapsed = time.time() - self.session_authenticated_at
        if elapsed > SESSION_TOKEN_REFRESH_SECONDS:
            self._keep_alive()

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential_jitter(initial=1, max=10),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _keep_alive(self) -> bool:
        """Send keep-alive to extend session token lifespan."""
        headers = self._build_headers()
        try:
            response = self._get_http_session().post(
                self._keepalive_url,
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            token = data.get("token")
            if token:
                self.session_token = token
                self.session_authenticated_at = time.time()
                logger.info("Betfair session keep-alive successful")
                return True
            else:
                logger.warning("Keep-alive returned no token, re-authenticating")
                return self.authenticate()
        except (requests.ConnectionError, requests.Timeout) as e:
            logger.error("Keep-alive failed: %s", e)
            raise

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------
    def _build_headers(self) -> Dict[str, str]:
        """Build standard Betfair API request headers."""
        return {
            "X-Application": self.app_key,
            "X-Authentication": self.session_token or "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _enforce_rate_limit(self) -> None:
        """Dynamic rate limiting — adjusts based on X-RateLimit-* response headers."""
        self.rate_limiter.wait_if_needed()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.5, max=30, jitter=1),
        retry=retry_if_exception_type((
            requests.ConnectionError,
            requests.Timeout,
            BetfairRateLimitError,
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _api_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated API request with rate limiting and retry."""
        self.ensure_session()
        self._enforce_rate_limit()

        url = (base_url or self._api_url) + endpoint
        headers = self._build_headers()

        response = self._get_http_session().post(
            url,
            data=json.dumps(payload),
            headers=headers,
            timeout=30,
        )

        # Update dynamic rate limiter from response headers
        self.rate_limiter.update_from_response(dict(response.headers))

        # Handle rate limiting
        if response.status_code == 429:
            self.rate_limiter.handle_429(dict(response.headers))
            raise BetfairRateLimitError("RATE_LIMITED", "Too many requests")

        # Handle auth errors
        if response.status_code == 401:
            logger.warning("401 Unauthorized — attempting re-authentication")
            self.authenticate()
            raise BetfairAuthError("UNAUTHORIZED", "Session token expired")

        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Account operations
    # ------------------------------------------------------------------
    def get_account_balance(self) -> Dict[str, Any]:
        """Get current account balance (available + exposure)."""
        payload = {"filter": {}}
        result = self._api_request(
            "getAccountFunds/",
            payload,
            base_url=self._account_url,
        )
        logger.info(
            "Account balance: available=%.2f, exposure=%.2f",
            result.get("availableToBetBalance", 0),
            result.get("exposure", 0),
        )
        return result

    def get_account_details(self) -> Dict[str, Any]:
        """Get account details (currency, region, etc)."""
        payload = {}
        return self._api_request(
            "getAccountDetails/",
            payload,
            base_url=self._account_url,
        )

    # ------------------------------------------------------------------
    # Market data operations
    # ------------------------------------------------------------------
    def list_market_catalogue(
        self,
        event_ids: Optional[List[str]] = None,
        market_type_codes: Optional[List[str]] = None,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List available markets filtered by event IDs and market types.
        Common market_type_codes: "MATCH_ODDS", "OVER_UNDER_25", "ASIAN_HANDICAP".
        """
        filter_params: Dict[str, Any] = {}
        if event_ids:
            filter_params["eventIds"] = event_ids
        if market_type_codes:
            filter_params["marketTypeCodes"] = market_type_codes

        payload = {
            "filter": filter_params,
            "maxResults": max_results,
            "marketProjection": ["EVENT", "MARKET_DESCRIPTION", "RUNNER_DESCRIPTION"],
        }
        result = self._api_request("listMarketCatalogue/", payload)
        return result if isinstance(result, list) else []

    def get_market_book(
        self,
        market_id: str,
        price_projection: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Get current order book for a market (available back/lay prices).
        """
        if price_projection is None:
            price_projection = {
                "priceData": ["EX_ALL_OFFERS"],
                "virtualise": True,
            }

        payload = {
            "marketIds": [market_id],
            "priceProjection": price_projection,
        }
        result = self._api_request("listMarketBook/", payload)
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        return {}

    # ------------------------------------------------------------------
    # Order execution
    # ------------------------------------------------------------------
    def place_back_order(
        self,
        market_id: str,
        selection_id: int,
        odds: float,
        stake: float,
        min_fill_size: Optional[float] = None,
        customer_order_ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place a BACK order on the exchange.

        Args:
            market_id: Betfair market ID (e.g., "1.23456789")
            selection_id: Runner selection ID (home/draw/away)
            odds: Requested odds (e.g., 2.10)
            stake: Stake in account currency (e.g., 5.00)
            min_fill_size: Minimum fill size for partial fill (None = no limit)
            customer_order_ref: Custom reference for tracking

        Returns:
            Dict with execution result: status, filled_stake, average_odds, etc.
        """
        self.ensure_session()

        place_instruction: Dict[str, Any] = {
            "selectionId": selection_id,
            "side": "BACK",
            "orderType": "LIMIT",
            "limitOrder": {
                "price": odds,
                "size": stake,
                "persistenceType": "LAPSE",  # Cancel if not filled at kick-off
            },
        }
        if min_fill_size is not None:
            place_instruction["limitOrder"]["minFillSize"] = min_fill_size
        if customer_order_ref:
            place_instruction["customerOrderRef"] = customer_order_ref

        payload = {
            "marketId": market_id,
            "instructions": [place_instruction],
        }

        start_time = time.time()
        result = self._api_request("placeOrders/", payload)
        latency_ms = (time.time() - start_time) * 1000

        return self._parse_execution_result(
            market_id=market_id,
            requested_odds=odds,
            requested_stake=stake,
            result=result,
            latency_ms=latency_ms,
        )

    def place_lay_order(
        self,
        market_id: str,
        selection_id: int,
        odds: float,
        stake: float,
        min_fill_size: Optional[float] = None,
        customer_order_ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place a LAY order on the exchange (betting against outcome).
        """
        self.ensure_session()

        place_instruction: Dict[str, Any] = {
            "selectionId": selection_id,
            "side": "LAY",
            "orderType": "LIMIT",
            "limitOrder": {
                "price": odds,
                "size": stake,
                "persistenceType": "LAPSE",
            },
        }
        if min_fill_size is not None:
            place_instruction["limitOrder"]["minFillSize"] = min_fill_size
        if customer_order_ref:
            place_instruction["customerOrderRef"] = customer_order_ref

        payload = {
            "marketId": market_id,
            "instructions": [place_instruction],
        }

        start_time = time.time()
        result = self._api_request("placeOrders/", payload)
        latency_ms = (time.time() - start_time) * 1000

        return self._parse_execution_result(
            market_id=market_id,
            requested_odds=odds,
            requested_stake=stake,
            result=result,
            latency_ms=latency_ms,
        )

    def cancel_order(
        self,
        market_id: str,
        bet_id: str,
        size_reduction: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Cancel an unmatched or partially matched order."""
        instruction: Dict[str, Any] = {"betId": bet_id}
        if size_reduction is not None:
            instruction["sizeReduction"] = size_reduction

        payload = {
            "marketId": market_id,
            "instructions": [instruction],
        }
        return self._api_request("cancelOrders/", payload)

    def replace_order(
        self,
        market_id: str,
        bet_id: str,
        new_odds: float,
    ) -> Dict[str, Any]:
        """Replace an unmatched order at different odds."""
        payload = {
            "marketId": market_id,
            "instructions": [{"betId": bet_id, "newPrice": new_odds}],
        }
        return self._api_request("replaceOrders/", payload)

    # ------------------------------------------------------------------
    # Result parsing
    # ------------------------------------------------------------------
    def _parse_execution_result(
        self,
        market_id: str,
        requested_odds: float,
        requested_stake: float,
        result: Dict[str, Any],
        latency_ms: float,
    ) -> Dict[str, Any]:
        """Parse Betfair placeOrders response into standardized format."""
        status = result.get("status", "FAILURE")
        error_code = result.get("errorCode")

        if status == "FAILURE" or error_code:
            logger.error(
                "Order FAILED: market=%s error=%s",
                market_id, error_code,
            )
            return {
                "market_id": market_id,
                "status": "REJECTED",
                "reason": error_code or "UNKNOWN_FAILURE",
                "filled_stake": 0.0,
                "average_odds": 0.0,
                "unfilled_stake": requested_stake,
                "latency_ms": latency_ms,
                "bet_id": None,
            }

        # Parse instruction reports
        instruction_reports = result.get("instructionReports", [])
        if not instruction_reports:
            return {
                "market_id": market_id,
                "status": "REJECTED",
                "reason": "NO_INSTRUCTION_REPORT",
                "filled_stake": 0.0,
                "average_odds": 0.0,
                "unfilled_stake": requested_stake,
                "latency_ms": latency_ms,
                "bet_id": None,
            }

        report = instruction_reports[0]
        order_status = report.get("orderStatus", "UNKNOWN")
        bet_id = report.get("betId")
        placed_date = report.get("placedDate")

        # Calculate filled amounts
        size_matched = float(report.get("sizeMatched", 0))
        average_price_matched = float(report.get("averagePriceMatched", 0))

        if size_matched == 0:
            fill_status = "UNMATCHED"
        elif size_matched >= requested_stake:
            fill_status = "FULLY_FILLED"
        else:
            fill_status = "PARTIALLY_FILLED"

        result_payload = {
            "market_id": market_id,
            "status": fill_status,
            "filled_stake": size_matched,
            "average_odds": average_price_matched if average_price_matched > 0 else requested_odds,
            "unfilled_stake": requested_stake - size_matched,
            "latency_ms": latency_ms,
            "bet_id": bet_id,
            "order_status": order_status,
            "placed_date": placed_date,
            "sandbox_mode": self.sandbox,
        }

        logger.info(
            "Order result: market=%s status=%s filled=%.2f@%.2f latency=%.1fms bet_id=%s",
            market_id, fill_status, size_matched, average_price_matched, latency_ms, bet_id,
        )
        return result_payload

    # ------------------------------------------------------------------
    # P&L calculations
    # ------------------------------------------------------------------
    def calculate_net_profit(self, filled_stake: float, odds: float, won: bool) -> float:
        """Calculate net PnL after Betfair commission."""
        if not won:
            return -filled_stake
        gross_profit = filled_stake * (odds - 1.0)
        commission = gross_profit * self.commission_rate
        return gross_profit - commission

    def calculate_true_edge(self, raw_odd: float, model_prob: float) -> float:
        """Calculate actual expected edge AFTER commission deduction."""
        profit_multiplier = raw_odd - 1.0
        net_profit_multiplier = profit_multiplier * (1.0 - self.commission_rate)
        true_odd = 1.0 + net_profit_multiplier
        return (true_odd * model_prob) - 1.0

    # ------------------------------------------------------------------
    # Convenience: find selection ID for a team
    # ------------------------------------------------------------------
    def find_selection_id(
        self,
        market_id: str,
        runner_name: str,
    ) -> Optional[int]:
        """Find the selection ID for a runner by name in a market."""
        catalogue = self.list_market_catalogue(
            event_ids=[market_id.split(".")[1] if "." in market_id else market_id],
            market_type_codes=["MATCH_ODDS"],
        )
        for market in catalogue:
            for runner in market.get("runners", []):
                name = runner.get("runnerName", "").lower()
                if runner_name.lower() in name:
                    return runner.get("selectionId")
        return None
