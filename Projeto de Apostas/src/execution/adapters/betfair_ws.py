"""
Betfair Stream API — WebSocket client for real-time odds updates.

Connects to Betfair's streaming API to receive live market data
without polling, reducing latency from seconds to milliseconds.

Docs: https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betfair+Stream+API
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

import websockets

logger = logging.getLogger("betfair_ws")

# ---------------------------------------------------------------------------
# Betfair Stream API endpoints
# ---------------------------------------------------------------------------
STREAM_URL_PRODUCTION = "stream-api.betfair.com:443"
STREAM_URL_SANDBOX = "stream-api-sandbox.betfair.com:443"

# ---------------------------------------------------------------------------
# Message types
# ---------------------------------------------------------------------------
MSG_CONNECTION = "status"
MSG_AUTH = "status"
MSG_SUBSCRIPTION = "status"
MSG_MARKET_UPDATE = "mcm"
MSG_ORDER_UPDATE = "ocm"


class BetfairStreamClient:
    """
    Async WebSocket client for Betfair Stream API.

    Receives real-time market data (odds changes, market status)
    and order updates (fill notifications).

    Usage:
        client = BetfairStreamClient(app_key="...", session_token="...")
        client.on_market_update = my_callback  # called with market data
        await client.connect()
        await client.subscribe_to_markets(market_ids=["1.23456789"])
        # runs until disconnected
    """

    def __init__(
        self,
        app_key: str,
        session_token: str,
        sandbox: bool = True,
        on_market_update: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_order_update: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_connection_lost: Optional[Callable[[], None]] = None,
    ):
        self.app_key = app_key
        self.session_token = session_token
        self.sandbox = sandbox
        self.on_market_update = on_market_update
        self.on_order_update = on_order_update
        self.on_connection_lost = on_connection_lost

        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._connected = False
        self._authenticated = False
        self._subscribed_market_ids: List[str] = []
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._running = False
        self._last_message_time: float = 0.0
        self._heartbeat_interval = 30  # seconds

        self._stream_url = STREAM_URL_SANDBOX if sandbox else STREAM_URL_PRODUCTION
        logger.info(
            "Betfair WebSocket client initialized (%s mode)",
            "SANDBOX" if sandbox else "PRODUCTION",
        )

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------
    async def connect(self) -> bool:
        """Connect to Betfair Stream API and authenticate."""
        try:
            self._ws = await websockets.connect(
                f"wss://{self._stream_url}",
                ping_interval=self._heartbeat_interval,
                ping_timeout=10,
                close_timeout=5,
            )
            self._connected = True
            self._reconnect_attempts = 0
            logger.info("WebSocket connected to %s", self._stream_url)

            # Wait for connection confirmation
            msg = await asyncio.wait_for(self._ws.recv(), timeout=10)
            conn_msg = json.loads(msg)
            if conn_msg.get("op") == "connection":
                logger.info("WebSocket connection confirmed: %s", conn_msg.get("connectionId"))
            return True

        except Exception as e:
            logger.error("WebSocket connection failed: %s", e)
            self._connected = False
            return False

    async def authenticate(self) -> bool:
        """Authenticate the WebSocket connection with session token."""
        if not self._ws or not self._connected:
            logger.error("Cannot authenticate: not connected")
            return False

        auth_msg = {
            "op": "authentication",
            "id": 1,
            "appKey": self.app_key,
            "session": self.session_token,
        }
        await asyncio.wait_for(self._ws.send(json.dumps(auth_msg)), timeout=10)

        # Wait for auth response
        try:
            msg = await asyncio.wait_for(self._ws.recv(), timeout=10)
            auth_response = json.loads(msg)
            status_code = auth_response.get("statusCode", "")

            if status_code == "SUCCESS":
                self._authenticated = True
                logger.info("WebSocket authenticated successfully")
                return True
            else:
                logger.error("WebSocket auth failed: %s", auth_response)
                self._authenticated = False
                return False

        except asyncio.TimeoutError:
            logger.error("WebSocket auth timeout")
            return False

    async def disconnect(self) -> None:
        """Gracefully disconnect from the stream."""
        self._running = False
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
        self._connected = False
        self._authenticated = False
        logger.info("WebSocket disconnected")

    # ------------------------------------------------------------------
    # Market subscriptions
    # ------------------------------------------------------------------
    async def subscribe_to_markets(
        self,
        market_ids: List[str],
        market_data_filter: Optional[Dict] = None,
    ) -> bool:
        """
        Subscribe to real-time market data for given market IDs.

        Args:
            market_ids: List of Betfair market IDs to monitor
            market_data_filter: Custom filter (default: EX_ALL_OFFERS + SP_TRADED)
        """
        if not self._authenticated:
            logger.error("Cannot subscribe: not authenticated")
            return False

        if market_data_filter is None:
            market_data_filter = {
                "fields": ["EX_ALL_OFFERS", "EX_TRADED", "SP_TRADED"],
            }

        sub_msg = {
            "op": "marketSubscription",
            "id": 2,
            "marketFilter": {
                "marketIds": market_ids,
            },
            "marketDataFilter": market_data_filter,
            "initialClip": True,
        }

        await asyncio.wait_for(self._ws.send(json.dumps(sub_msg)), timeout=10)
        # Dedup: only add IDs that aren't already subscribed
        existing = set(self._subscribed_market_ids)
        new_ids = [m for m in market_ids if m not in existing]
        self._subscribed_market_ids.extend(new_ids)
        logger.info("Subscribed to %d markets (new: %d)", len(market_ids), len(new_ids))
        return True

    async def subscribe_to_orders(self) -> bool:
        """Subscribe to real-time order updates (fill notifications)."""
        if not self._authenticated:
            return False

        order_msg = {
            "op": "orderSubscription",
            "id": 3,
            "orderFilter": {"includeOverallPosition": True},
        }
        await asyncio.wait_for(self._ws.send(json.dumps(order_msg)), timeout=10)
        logger.info("Subscribed to order updates")
        return True

    async def unsubscribe_from_markets(self, market_ids: List[str]) -> None:
        """Unsubscribe from specific markets."""
        # Betfair doesn't have a direct unsubscribe — resubscribe without those IDs
        remaining = [m for m in self._subscribed_market_ids if m not in market_ids]
        self._subscribed_market_ids = remaining
        if remaining:
            await self.subscribe_to_markets(remaining)

    # ------------------------------------------------------------------
    # Message processing loop
    # ------------------------------------------------------------------
    async def listen(self) -> None:
        """
        Main loop: receive and dispatch messages.
        Runs until disconnect() is called or connection is lost.
        """
        self._running = True

        while self._running:
            try:
                if not self._ws or not self._connected:
                    await self._reconnect()
                    continue

                msg_raw = await asyncio.wait_for(
                    self._ws.recv(),
                    timeout=self._heartbeat_interval + 10,
                )
                self._last_message_time = time.time()
                self._process_message(msg_raw)

            except asyncio.TimeoutError:
                # No message received — check if connection is alive
                if time.time() - self._last_message_time > self._heartbeat_interval * 2:
                    logger.warning("No messages for extended period — connection may be stale")
                    await self._reconnect()

            except websockets.ConnectionClosed as e:
                logger.warning("WebSocket connection closed: code=%s reason=%s", e.code, e.reason)
                self._connected = False
                if self.on_connection_lost:
                    self.on_connection_lost()
                if self._running:
                    await self._reconnect()

            except Exception as e:
                logger.error("WebSocket listen error: %s", e)
                if self._running:
                    await asyncio.sleep(1)

    def _process_message(self, raw_msg: str) -> None:
        """Parse and dispatch a WebSocket message."""
        try:
            msg = json.loads(raw_msg)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON received: %s", raw_msg[:200])
            return

        op = msg.get("op", "")
        msg_type = msg.get("ct", "")

        # Connection status messages
        if op == "status":
            status_code = msg.get("statusCode", "")
            if status_code == "FAILURE":
                logger.error("Stream status failure: %s", msg.get("errorMessage", ""))
            return

        # Market change messages
        if msg_type == MSG_MARKET_UPDATE or op == "mcm":
            self._handle_market_update(msg)
            return

        # Order change messages
        if msg_type == MSG_ORDER_UPDATE or op == "ocm":
            self._handle_order_update(msg)
            return

    def _handle_market_update(self, msg: Dict[str, Any]) -> None:
        """Process a market change message and call callback."""
        market_changes = msg.get("mc", [])
        if not market_changes:
            return

        for change in market_changes:
            market_id = change.get("id", "")
            market_status = change.get("marketDefinition", {}).get("status", "")

            # Extract runner changes (price updates)
            runner_changes = change.get("rc", [])
            update_data = {
                "market_id": market_id,
                "status": market_status,
                "timestamp": msg.get("pt", 0),
                "runners": [],
            }

            for rc in runner_changes:
                runner_data = {
                    "selection_id": rc.get("id"),
                    "back": [
                        {"price": b[0], "size": b[1]}
                        for b in (rc.get("batb") or [])
                    ],
                    "lay": [
                        {"price": l[0], "size": l[1]}
                        for l in (rc.get("batl") or [])
                    ],
                    "traded_volume": rc.get("tv", 0),
                    "last_price_traded": rc.get("ltp"),
                }
                update_data["runners"].append(runner_data)

            if self.on_market_update:
                try:
                    self.on_market_update(update_data)
                except Exception as e:
                    logger.error("Market update callback error: %s", e)

    def _handle_order_update(self, msg: Dict[str, Any]) -> None:
        """Process an order change message (fills, cancellations)."""
        order_changes = msg.get("oc", [])
        if not order_changes:
            return

        for change in order_changes:
            update_data = {
                "market_id": change.get("id", ""),
                "timestamp": msg.get("pt", 0),
                "orders": [],
            }

            for order in change.get("orc", []):
                order_data = {
                    "bet_id": order.get("id"),
                    "selection_id": order.get("sid"),
                    "side": order.get("side"),
                    "status": order.get("status"),
                    "size_matched": order.get("sm", 0),
                    "size_remaining": order.get("sr", 0),
                    "average_price_matched": order.get("avp", 0),
                }
                update_data["orders"].append(order_data)

            if self.on_order_update:
                try:
                    self.on_order_update(update_data)
                except Exception as e:
                    logger.error("Order update callback error: %s", e)

    # ------------------------------------------------------------------
    # Reconnection
    # ------------------------------------------------------------------
    async def _reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.critical(
                "Max reconnect attempts (%d) reached — giving up",
                self._max_reconnect_attempts,
            )
            self._running = False
            if self.on_connection_lost:
                self.on_connection_lost()
            return

        self._reconnect_attempts += 1
        backoff = min(2 ** self._reconnect_attempts, 60)  # Cap at 60s

        logger.info(
            "Reconnecting in %ds (attempt %d/%d)",
            backoff, self._reconnect_attempts, self._max_reconnect_attempts,
        )
        await asyncio.sleep(backoff)

        # Clean up old connection
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
        self._connected = False
        self._authenticated = False

        # Reconnect + re-auth + re-subscribe
        if await self.connect():
            if await self.authenticate():
                if self._subscribed_market_ids:
                    await self.subscribe_to_markets(self._subscribed_market_ids)
                logger.info("Reconnection successful")

    # ------------------------------------------------------------------
    # Sync wrapper for convenience
    # ------------------------------------------------------------------
    def run(self, market_ids: List[str]) -> None:
        """Blocking entry point: connect, subscribe, and listen."""
        async def _main():
            if not await self.connect():
                return
            if not await self.authenticate():
                return
            if market_ids:
                await self.subscribe_to_markets(market_ids)
            await self.listen()

        asyncio.run(_main())
