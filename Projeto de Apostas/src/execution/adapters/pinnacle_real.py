"""
Pinnacle Sports API — Real implementation with Basic authentication,
dynamic market limits, and straight bet execution.

Docs: https://pinnacleapi.github.io/
"""
from __future__ import annotations

import base64
import logging
import time
from typing import Any, Dict, List, Optional

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger("pinnacle_real")

# ---------------------------------------------------------------------------
# Pinnacle API endpoints
# ---------------------------------------------------------------------------
PINNACLE_BASE_URL = "https://api.pinnacle.com"
PINNACLE_SPORT_URL = f"{PINNACLE_BASE_URL}/sports/v1"
PINNACLE_BET_URL = f"{PINNACLE_BASE_URL}/v1/bets"

# Sport IDs
SPORT_IDS = {
    "football": 29,
    "basketball": 4,
    "nba": 4,
    "mma": 7,
    "ufc": 7,
    "tennis": 33,
    "baseball": 3,
    "hockey": 6,
    "soccer": 29,
}


class PinnacleAPIError(Exception):
    """Raised when the Pinnacle API returns an error."""
    def __init__(self, error_code: str, error_message: str, response: Optional[Dict] = None):
        self.error_code = error_code
        self.error_message = error_message
        self.response = response
        super().__init__(f"PinnacleAPIError({error_code}): {error_message}")


class PinnacleRealConnector:
    """
    Real Pinnacle Sports API client with:
    - Basic authentication (Base64 client_id:password)
    - Dynamic market limit fetching
    - Straight bet execution with partial fill handling
    - Rate limiting with exponential backoff via tenacity
    """

    def __init__(
        self,
        client_id: str,
        password: str,
        commission_rate: float = 0.0,
    ):
        self.client_id = client_id
        self.password = password
        self.commission_rate = commission_rate  # Pinnacle doesn't charge commission

        self._auth_header: Optional[str] = None
        self._last_call_time: float = 0.0
        self._min_call_interval: float = 1.0  # 1 req/s for Pinnacle

        # Connection pooling via requests.Session
        self._http_session: Optional[requests.Session] = None

        if not client_id or not password:
            raise ValueError(
                "Pinnacle credentials missing: set PINNACLE_CLIENT_ID and PINNACLE_PASSWORD"
            )
        self._build_auth_header()
        logger.info("Pinnacle API client initialized")

    # ------------------------------------------------------------------
    # HTTP session (connection pooling)
    # ------------------------------------------------------------------
    def _get_http_session(self) -> requests.Session:
        """Lazy-init a requests.Session for connection pooling."""
        if self._http_session is None:
            self._http_session = requests.Session()
            self._http_session.headers.update(self._build_headers())
        return self._http_session

    def close(self) -> None:
        """Close the HTTP session and release connections."""
        if self._http_session:
            self._http_session.close()
            self._http_session = None

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def _build_auth_header(self) -> str:
        """Build Base64 Basic authentication header."""
        credentials = f"{self.client_id}:{self.password}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        self._auth_header = f"Basic {encoded}"
        return self._auth_header

    @property
    def auth_header(self) -> str:
        if not self._auth_header:
            self._build_auth_header()
        return self._auth_header

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------
    def _build_headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _enforce_rate_limit(self) -> None:
        """Client-side rate limiting (1 req/s for Pinnacle)."""
        now = time.time()
        elapsed = now - self._last_call_time
        if elapsed < self._min_call_interval:
            time.sleep(self._min_call_interval - elapsed)
        self._last_call_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=30, jitter=2),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated API request with rate limiting and retry."""
        self._enforce_rate_limit()
        url = f"{PINNACLE_SPORT_URL}/{endpoint}" if not endpoint.startswith("http") else endpoint
        headers = self._build_headers()

        response = self._get_http_session().request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
            timeout=30,
        )

        if response.status_code == 401:
            raise PinnacleAPIError("UNAUTHORIZED", "Invalid credentials")

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 5))
            logger.warning("Rate limited — retrying after %ds", retry_after)
            time.sleep(retry_after)
            raise PinnacleAPIError("RATE_LIMITED", "Too many requests")

        if response.status_code == 500:
            raise PinnacleAPIError("SERVER_ERROR", "Pinnacle API server error")

        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=30, jitter=2),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _bet_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a bet placement request to the bets endpoint."""
        self._enforce_rate_limit()
        headers = self._build_headers()

        response = self._get_http_session().post(
            PINNACLE_BET_URL + "/straight",
            headers=headers,
            json=data,
            timeout=30,
        )

        if response.status_code == 401:
            raise PinnacleAPIError("UNAUTHORIZED", "Invalid credentials")

        if response.status_code == 400:
            error_data = response.json()
            raise PinnacleAPIError(
                error_data.get("code", "BAD_REQUEST"),
                error_data.get("message", "Bad request"),
                response=error_data,
            )

        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Market data operations
    # ------------------------------------------------------------------
    def get_sports(self) -> List[Dict[str, Any]]:
        """Get list of available sports."""
        result = self._api_request("GET", "sports")
        return result if isinstance(result, list) else []

    def get_leagues(self, sport_id: int) -> List[Dict[str, Any]]:
        """Get available leagues for a sport."""
        result = self._api_request("GET", "leagues", params={"sportId": sport_id})
        return result if isinstance(result, list) else []

    def get_fixtures(
        self,
        sport_id: int,
        league_ids: Optional[List[int]] = None,
        since: Optional[int] = None,
        is_live: bool = False,
    ) -> Dict[str, Any]:
        """
        Get fixtures (events) for a sport.

        Args:
            sport_id: Pinnacle sport ID (e.g., 29 for soccer)
            league_ids: Optional filter by league IDs
            since: Only return fixtures modified after this timestamp
            is_live: If True, only return live fixtures
        """
        params: Dict[str, Any] = {"sportId": sport_id}
        if league_ids:
            params["leagueIds"] = ",".join(str(l) for l in league_ids)
        if since:
            params["since"] = since
        if is_live:
            params["isLive"] = "true"

        return self._api_request("GET", "fixtures", params=params)

    def get_odds(
        self,
        sport_id: int,
        league_ids: Optional[List[int]] = None,
        event_ids: Optional[List[str]] = None,
        since: Optional[int] = None,
        is_live: bool = False,
    ) -> Dict[str, Any]:
        """
        Get odds for events.

        Args:
            sport_id: Pinnacle sport ID
            event_ids: Optional specific event IDs
            since: Only return odds modified after this timestamp
        """
        params: Dict[str, Any] = {"sportId": sport_id}
        if league_ids:
            params["leagueIds"] = ",".join(str(l) for l in league_ids)
        if event_ids:
            params["eventIds"] = ",".join(event_ids)
        if since:
            params["since"] = since
        if is_live:
            params["isLive"] = "true"

        return self._api_request("GET", "odds", params=params)

    def get_market_limits(
        self,
        event_id: str,
        sport_id: int,
        period_number: int = 0,
        bet_type: str = "MONEYLINE",
    ) -> Dict[str, float]:
        """
        Get dynamic maximum/minimum stake limits for a market.
        Limits change rapidly close to kickoff.
        """
        params = {
            "sportId": sport_id,
            "eventId": event_id,
            "periodNumber": period_number,
            "betType": bet_type,
        }
        try:
            result = self._api_request("GET", "marketdata/limits", params=params)
            limits = result.get("limits", [{}])
            if limits:
                limit = limits[0]
                return {
                    "max_stake": float(limit.get("maxAmount", 750.0)),
                    "min_stake": float(limit.get("minAmount", 10.0)),
                }
        except Exception as e:
            logger.warning("Could not fetch market limits: %s — using defaults", e)

        return {"max_stake": 750.0, "min_stake": 10.0}

    # ------------------------------------------------------------------
    # Bet execution
    # ------------------------------------------------------------------
    def place_bet(
        self,
        event_id: str,
        sport_id: int,
        line_id: int,
        period_number: int,
        bet_type: str,
        odds: float,
        stake: float,
        team: Optional[str] = None,
        side: Optional[str] = None,
        accept_better_odds: bool = True,
        customer_reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Place a straight wager on Pinnacle.

        Args:
            event_id: Pinnacle event ID
            sport_id: Sport ID (e.g., 29 for soccer)
            line_id: Line ID from odds response
            period_number: Period (0 = full match, 1 = 1st half, etc.)
            bet_type: "MONEYLINE", "SPREAD", "TOTAL_POINTS"
            odds: Decimal odds (e.g., 2.10)
            stake: Stake amount in account currency
            team: "TEAM1" or "TEAM2" (for moneyline)
            side: "OVER" or "UNDER" (for totals)
            accept_better_odds: Accept if odds improve
            customer_reference: Custom tracking reference

        Returns:
            Dict with execution result
        """
        start_time = time.time()

        # Validate stake against limits
        limits = self.get_market_limits(event_id, sport_id, period_number, bet_type)
        if stake < limits["min_stake"]:
            return {
                "event_id": event_id,
                "status": "REJECTED",
                "reason": "STAKE_BELOW_MINIMUM",
                "filled_stake": 0.0,
                "latency_ms": 0,
            }

        # Build bet request
        bet_data: Dict[str, Any] = {
            "sportId": sport_id,
            "eventId": int(event_id),
            "lineId": line_id,
            "periodNumber": period_number,
            "betType": bet_type,
            "odds": odds,
            "stake": stake,
            "acceptBetterOdds": accept_better_odds,
        }

        if team:
            bet_data["team"] = team
        if side:
            bet_data["side"] = side
        if customer_reference:
            bet_data["customerReference"] = customer_reference

        # Cap stake at max limit
        if stake > limits["max_stake"]:
            bet_data["stake"] = limits["max_stake"]
            logger.warning(
                "Stake capped from %.2f to max limit %.2f",
                stake, limits["max_stake"],
            )

        try:
            result = self._bet_request(bet_data)
            latency_ms = (time.time() - start_time) * 1000

            return self._parse_bet_result(
                event_id=event_id,
                requested_stake=stake,
                actual_stake=bet_data["stake"],
                result=result,
                latency_ms=latency_ms,
            )

        except PinnacleAPIError as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error("Bet placement failed: %s", e)
            return {
                "event_id": event_id,
                "status": "REJECTED",
                "reason": e.error_code,
                "filled_stake": 0.0,
                "latency_ms": latency_ms,
            }

    # ------------------------------------------------------------------
    # Result parsing
    # ------------------------------------------------------------------
    def _parse_bet_result(
        self,
        event_id: str,
        requested_stake: float,
        actual_stake: float,
        result: Dict[str, Any],
        latency_ms: float,
    ) -> Dict[str, Any]:
        """Parse Pinnacle bet placement response."""
        bet_id = result.get("betId")
        status = result.get("status", "NOT_ACCEPTED")
        better_odds_accepted = result.get("betterOddsAccepted", False)
        price = float(result.get("price", 0))

        if status == "ACCEPTED":
            fill_status = "FULLY_FILLED"
            filled_stake = actual_stake
            avg_odds = price if price > 0 else 0.0
        elif status == "NOT_ACCEPTED":
            fill_status = "REJECTED"
            filled_stake = 0.0
            avg_odds = 0.0
        else:
            fill_status = "UNKNOWN"
            filled_stake = 0.0
            avg_odds = 0.0

        result_payload = {
            "event_id": event_id,
            "status": fill_status,
            "filled_stake": filled_stake,
            "average_odds": avg_odds,
            "unfilled_stake": requested_stake - filled_stake,
            "latency_ms": latency_ms,
            "bet_id": bet_id,
            "better_odds_accepted": better_odds_accepted,
            "pinnacle_status": status,
        }

        logger.info(
            "Pinnacle order: event=%s status=%s filled=%.2f@%.2f latency=%.1fms",
            event_id, fill_status, filled_stake, avg_odds, latency_ms,
        )
        return result_payload

    # ------------------------------------------------------------------
    # Account operations
    # ------------------------------------------------------------------
    def get_balance(self) -> Dict[str, Any]:
        """Get current account balance."""
        return self._api_request("GET", "client/balance")

    # ------------------------------------------------------------------
    # P&L calculations
    # ------------------------------------------------------------------
    def calculate_net_profit(self, filled_stake: float, odds: float, won: bool) -> float:
        """Calculate net PnL (Pinnacle has no commission)."""
        if not won:
            return -filled_stake
        return filled_stake * (odds - 1.0)

    # ------------------------------------------------------------------
    # Convenience: get sport ID
    # ------------------------------------------------------------------
    @staticmethod
    def get_sport_id(sport_name: str) -> int:
        """Get Pinnacle sport ID by name."""
        return SPORT_IDS.get(sport_name.lower(), 29)  # default to soccer
