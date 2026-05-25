"""
Polymarket / Augur execution adapter — web3-based prediction market integration.

Enables betting on prediction markets via smart contracts using AMM
(Automated Market Maker). Benefits: no stake limits, low commissions,
access to unique markets (politics, crypto, weather).

Uses web3.py for blockchain interaction. Falls back gracefully if
web3 is not installed.

Usage:
    from src.execution.adapters.polymarket import PolymarketAdapter

    adapter = PolymarketAdapter(private_key="0x...", rpc_url="https://...")
    markets = adapter.list_markets(tag="sports")
    result = adapter.place_bet(market_id="123", outcome="YES", stake_usd=10.0)
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("polymarket")

# ---------------------------------------------------------------------------
# Polymarket API endpoints
# ---------------------------------------------------------------------------
POLYMARKET_API_BASE = "https://clob.polymarket.com"
POLYMARKET_GAMMA_API = "https://gamma-api.polymarket.com"

# Chain IDs
CHAIN_POLYGON = 137
CHAIN_ETHEREUM = 1

# CTF Exchange contract (Polygon)
CTF_EXCHANGE_ADDRESS = "0x4bFb41C5E2A7B7e3877C7341e8535979a75c3a3C"


@dataclass
class PolymarketMarket:
    """Represents a Polymarket prediction market."""
    market_id: str
    question: str
    outcomes: List[str]
    outcome_prices: List[float]  # Current AMM prices (0-1)
    volume: float
    liquidity: float
    end_date: str
    active: bool = True
    tags: List[str] = None


class PolymarketAPIError(Exception):
    """Raised when the Polymarket API returns an error."""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"PolymarketAPIError({code}): {message}")


class PolymarketAdapter:
    """
    Polymarket prediction market adapter with:
    - REST API for market data and order placement
    - web3.py for direct smart contract interaction (optional)
    - AMM price impact simulation
    - Polygon/Ethereum chain support
    """

    def __init__(
        self,
        private_key: str = "",
        rpc_url: str = "https://polygon-rpc.com",
        api_key: str = "",
        api_secret: str = "",
        chain_id: int = CHAIN_POLYGON,
        use_web3: bool = True,
    ):
        self.private_key = private_key
        self.rpc_url = rpc_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.chain_id = chain_id
        self.use_web3 = use_web3

        self._web3 = None
        self._session: Optional[requests.Session] = None

        # Try to init web3
        if use_web3 and private_key:
            try:
                from web3 import Web3
                self._web3 = Web3(Web3.HTTPProvider(rpc_url))
                if self._web3.is_connected():
                    logger.info("Web3 connected to chain %d", chain_id)
                else:
                    logger.warning("Web3 not connected — falling back to REST API only")
                    self._web3 = None
            except ImportError:
                logger.warning("web3.py not installed — REST API only. Install: pip install web3")
                self._web3 = None

    # ------------------------------------------------------------------
    # HTTP session (connection pooling)
    # ------------------------------------------------------------------
    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._session.headers.update(headers)
        return self._session

    def close(self) -> None:
        if self._session:
            self._session.close()
            self._session = None

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------
    def list_markets(
        self,
        tag: Optional[str] = None,
        active_only: bool = True,
        limit: int = 50,
    ) -> List[PolymarketMarket]:
        """List available prediction markets."""
        params: Dict[str, Any] = {"limit": limit, "active": active_only}
        if tag:
            params["tag"] = tag

        try:
            resp = self._get_session().get(
                f"{POLYMARKET_GAMMA_API}/markets",
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error("Failed to list markets: %s", e)
            return []

        markets = []
        for m in data:
            try:
                markets.append(PolymarketMarket(
                    market_id=m.get("id", ""),
                    question=m.get("question", ""),
                    outcomes=m.get("outcomes", "").split(",") if m.get("outcomes") else [],
                    outcome_prices=[
                        float(p) for p in (m.get("outcomePrices", "").split(",") if m.get("outcomePrices") else [])
                    ],
                    volume=float(m.get("volume", 0)),
                    liquidity=float(m.get("liquidity", 0)),
                    end_date=m.get("endDate", ""),
                    active=m.get("active", True),
                    tags=m.get("tags", []),
                ))
            except Exception as e:
                logger.warning("Failed to parse market: %s", e)
                continue

        return markets

    def get_market(self, market_id: str) -> Optional[PolymarketMarket]:
        """Get details for a specific market."""
        try:
            resp = self._get_session().get(
                f"{POLYMARKET_GAMMA_API}/markets/{market_id}",
                timeout=30,
            )
            resp.raise_for_status()
            m = resp.json()
            return PolymarketMarket(
                market_id=m.get("id", ""),
                question=m.get("question", ""),
                outcomes=m.get("outcomes", "").split(",") if m.get("outcomes") else [],
                outcome_prices=[
                    float(p) for p in (m.get("outcomePrices", "").split(",") if m.get("outcomePrices") else [])
                ],
                volume=float(m.get("volume", 0)),
                liquidity=float(m.get("liquidity", 0)),
                end_date=m.get("endDate", ""),
                active=m.get("active", True),
            )
        except Exception as e:
            logger.error("Failed to get market %s: %s", market_id, e)
            return None

    def get_market_price(self, market_id: str, outcome: str = "YES") -> float:
        """Get current AMM price for an outcome (0.0 to 1.0)."""
        market = self.get_market(market_id)
        if not market:
            return 0.5
        idx = 0 if outcome.upper() == "YES" else 1
        if idx < len(market.outcome_prices):
            return market.outcome_prices[idx]
        return 0.5

    # ------------------------------------------------------------------
    # AMM price impact simulation
    # ------------------------------------------------------------------
    def simulate_amm_impact(
        self,
        current_price: float,
        stake_usd: float,
        liquidity_usd: float,
        outcome: str = "YES",
    ) -> Dict[str, float]:
        """
        Simulate AMM price impact for a bet.

        Uses constant product formula: x * y = k
        Price impact increases with stake size relative to liquidity.

        Returns:
            Dict with effective_price, price_impact, avg_fill_price
        """
        if liquidity_usd <= 0:
            return {"effective_price": current_price, "price_impact": 0.0, "avg_fill_price": current_price}

        # Constant product AMM
        # For YES outcome: pool has (YES_tokens, NO_tokens)
        # k = YES * NO (constant)
        yes_tokens = liquidity_usd * current_price
        no_tokens = liquidity_usd * (1 - current_price)
        k = yes_tokens * no_tokens

        if outcome.upper() == "YES":
            # Buying YES tokens → YES price increases
            new_yes = yes_tokens + stake_usd
            new_no = k / new_yes
            new_price = 1.0 - (new_no / (new_yes + new_no))
        else:
            # Buying NO tokens → YES price decreases
            new_no = no_tokens + stake_usd
            new_yes = k / new_no
            new_price = new_yes / (new_yes + new_no)

        price_impact = abs(new_price - current_price)
        avg_fill_price = (current_price + new_price) / 2

        return {
            "effective_price": round(new_price, 6),
            "price_impact": round(price_impact, 6),
            "avg_fill_price": round(avg_fill_price, 6),
            "initial_price": current_price,
            "stake_usd": stake_usd,
            "liquidity_usd": liquidity_usd,
        }

    # ------------------------------------------------------------------
    # Order placement
    # ------------------------------------------------------------------
    def place_bet(
        self,
        market_id: str,
        outcome: str = "YES",
        stake_usd: float = 10.0,
        max_price: float = 0.99,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Place a bet on a prediction market.

        Args:
            market_id: Polymarket market ID
            outcome: "YES" or "NO"
            stake_usd: Stake amount in USD
            max_price: Maximum price willing to pay
            dry_run: If True, simulate without placing real order

        Returns:
            Order result with fill details
        """
        market = self.get_market(market_id)
        if not market:
            return {"status": "ERROR", "reason": "Market not found"}

        current_price = self.get_market_price(market_id, outcome)
        impact = self.simulate_amm_impact(current_price, stake_usd, market.liquidity, outcome)

        if impact["effective_price"] > max_price:
            return {
                "status": "REJECTED",
                "reason": f"Price impact too high: {impact['effective_price']:.4f} > {max_price}",
                "impact": impact,
            }

        if dry_run:
            return {
                "status": "DRY_RUN",
                "market_id": market_id,
                "outcome": outcome,
                "stake_usd": stake_usd,
                "current_price": current_price,
                "effective_price": impact["effective_price"],
                "price_impact": impact["price_impact"],
                "avg_fill_price": impact["avg_fill_price"],
            }

        # Real order placement via CLOB API
        if not self.api_key or not self.api_secret:
            return {"status": "ERROR", "reason": "API credentials required for live trading"}

        try:
            order_payload = {
                "market": market_id,
                "outcome": outcome,
                "amount": str(stake_usd),
                "price": str(impact["avg_fill_price"]),
                "side": "BUY",
                "type": "GTC",  # Good Till Cancelled
            }

            resp = self._get_session().post(
                f"{POLYMARKET_API_BASE}/order",
                json=order_payload,
                timeout=30,
            )

            if resp.status_code == 200:
                result = resp.json()
                logger.info("Order placed: %s", result.get("orderID", "unknown"))
                return {"status": "FILLED", "order": result, "impact": impact}
            else:
                return {"status": "REJECTED", "reason": resp.text, "impact": impact}

        except Exception as e:
            logger.error("Order placement failed: %s", e)
            return {"status": "ERROR", "reason": str(e)}

    # ------------------------------------------------------------------
    # Account / Balance
    # ------------------------------------------------------------------
    def get_balance(self) -> Dict[str, float]:
        """Get account balance (requires web3 or API auth)."""
        if self._web3 and self.private_key:
            try:
                address = self._web3.eth.account.from_key(self.private_key).address
                balance_wei = self._web3.eth.get_balance(address)
                balance_matic = float(self._web3.from_wei(balance_wei, "ether"))
                return {"address": address, "balance_matic": balance_matic, "chain_id": self.chain_id}
            except Exception as e:
                logger.error("Failed to get balance: %s", e)

        return {"address": "unknown", "balance_matic": 0.0, "chain_id": self.chain_id}

    @property
    def status(self) -> Dict[str, Any]:
        """Get adapter status."""
        return {
            "web3_connected": self._web3 is not None and self._web3.is_connected(),
            "chain_id": self.chain_id,
            "api_configured": bool(self.api_key),
            "has_private_key": bool(self.private_key),
        }

    # ------------------------------------------------------------------
    # CLOB (Central Limit Order Book) API
    # ------------------------------------------------------------------
    def get_order_book(
        self,
        market_id: str,
        side: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get the CLOB order book for a market.

        Returns bid/ask levels with price and size at each level.

        Args:
            market_id: Polymarket market ID (condition_id)
            side: Optional filter "buy" or "sell"

        Returns:
            Dict with "bids" and "asks" lists of {price, size} dicts.
        """
        try:
            params: Dict[str, Any] = {"token_id": market_id}
            if side:
                params["side"] = side

            resp = self._get_session().get(
                f"{POLYMARKET_API_BASE}/book",
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            bids = [
                {"price": float(b.get("price", 0)), "size": float(b.get("size", 0))}
                for b in data.get("bids", [])[:10]
            ]
            asks = [
                {"price": float(a.get("price", 0)), "size": float(a.get("size", 0))}
                for a in data.get("asks", [])[:10]
            ]

            return {"market_id": market_id, "bids": bids, "asks": asks}

        except Exception as e:
            logger.error("Failed to get order book for %s: %s", market_id, e)
            return {"market_id": market_id, "bids": [], "asks": []}

    def place_clob_order(
        self,
        market_id: str,
        outcome: str = "YES",
        stake_usd: float = 10.0,
        price_limit: float = 0.95,
        time_in_force: str = "GTC",
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Place a limit order on the CLOB (Central Limit Order Book).

        This is the preferred method for real order placement on Polymarket,
        as it provides better price control and fill visibility than the
        simple AMM-based place_bet().

        Args:
            market_id: Polymarket condition ID or token ID
            outcome: "YES" or "NO"
            stake_usd: Amount in USD to wager
            price_limit: Maximum price to pay (0-1)
            time_in_force: "GTC" (Good Till Cancel), "GTD" (Good Till Date), "FOK" (Fill or Kill)
            dry_run: If True, simulate without placing real order

        Returns:
            Dict with order details and fill status.
        """
        # Get current order book
        book = self.get_order_book(market_id)

        # Determine side
        side = "BUY" if outcome.upper() == "YES" else "SELL"

        # Check if price is available in the book
        best_ask = None
        total_available = 0.0
        for ask in book.get("asks", []):
            if ask["price"] <= price_limit:
                if best_ask is None:
                    best_ask = ask["price"]
                total_available += ask["size"]

        if best_ask is None and side == "BUY":
            return {
                "status": "NO_LIQUIDITY",
                "reason": f"No asks available at or below {price_limit}",
                "book": book,
            }

        # Simulate fill
        fill_price = best_ask or price_limit
        fill_amount = min(stake_usd, total_available)
        partial_fill = fill_amount < stake_usd

        if dry_run:
            return {
                "status": "DRY_RUN",
                "market_id": market_id,
                "side": side,
                "outcome": outcome,
                "stake_usd": stake_usd,
                "fill_price": fill_price,
                "fill_amount": fill_amount,
                "partial_fill": partial_fill,
                "book_depth": len(book.get("asks", [])),
            }

        # Real CLOB order placement
        if not self.api_key or not self.api_secret:
            return {"status": "ERROR", "reason": "API credentials required for CLOB trading"}

        try:
            # Build CLOB order payload
            order_payload = {
                "tokenID": market_id,
                "price": str(fill_price),
                "size": str(fill_amount),
                "side": side,
                "type": time_in_force,
            }

            # Sign the order if web3 is available
            if self._web3 and self.private_key:
                from eth_account import Account
                from eth_account.messages import encode_defunct

                message = json.dumps(order_payload, sort_keys=True)
                msg = encode_defunct(text=message)
                account = Account.from_key(self.private_key)
                signed = account.sign_message(msg)
                order_payload["signature"] = signed.signature.hex()
                order_payload["signer"] = account.address

            resp = self._get_session().post(
                f"{POLYMARKET_API_BASE}/order",
                json=order_payload,
                timeout=30,
            )

            if resp.status_code in (200, 201):
                result = resp.json()
                order_id = result.get("orderID", result.get("id", "unknown"))
                logger.info("CLOB order placed: %s", order_id)
                return {
                    "status": "FILLED" if not partial_fill else "PARTIALLY_FILLED",
                    "order_id": order_id,
                    "fill_price": fill_price,
                    "fill_amount": fill_amount,
                    "partial_fill": partial_fill,
                    "raw_response": result,
                }
            else:
                return {
                    "status": "REJECTED",
                    "reason": resp.text,
                    "status_code": resp.status_code,
                }

        except Exception as e:
            logger.error("CLOB order placement failed: %s", e)
            return {"status": "ERROR", "reason": str(e)}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an existing CLOB order."""
        if not self.api_key:
            return {"status": "ERROR", "reason": "API key required"}

        try:
            resp = self._get_session().delete(
                f"{POLYMARKET_API_BASE}/order/{order_id}",
                timeout=15,
            )
            resp.raise_for_status()
            return {"status": "CANCELLED", "order_id": order_id}
        except Exception as e:
            logger.error("Failed to cancel order %s: %s", order_id, e)
            return {"status": "ERROR", "reason": str(e)}

    def get_open_orders(self, market_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all open orders, optionally filtered by market."""
        if not self.api_key:
            return []

        try:
            params = {}
            if market_id:
                params["market"] = market_id

            resp = self._get_session().get(
                f"{POLYMARKET_API_BASE}/orders",
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("Failed to get open orders: %s", e)
            return []
