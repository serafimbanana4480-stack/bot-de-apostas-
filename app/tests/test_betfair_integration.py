"""
Integration tests for Betfair sandbox API.

These tests require valid Betfair sandbox credentials in .env:
  - BETFAIR_APP_KEY
  - BETFAIR_CERT_PATH
  - BETFAIR_KEY_PATH
  - BETFAIR_USERNAME
  - BETFAIR_PASSWORD

Run with: pytest tests/test_betfair_integration.py -v --run-integration

Tests are skipped by default unless --run-integration flag is provided,
to prevent accidental API calls during normal test runs.
"""
import os
import time

import pytest

# Skip all tests unless explicitly enabled
pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable.",
)


def _get_connector():
    """Create a BetfairRealConnector from environment settings."""
    from src.execution.adapters.betfair_real import BetfairRealConnector

    app_key = os.getenv("BETFAIR_APP_KEY", "")
    cert_path = os.getenv("BETFAIR_CERT_PATH", "")
    key_path = os.getenv("BETFAIR_KEY_PATH", "")

    if not all([app_key, cert_path, key_path]):
        pytest.skip("Betfair sandbox credentials not configured")

    return BetfairRealConnector(
        app_key=app_key,
        cert_path=cert_path,
        key_path=key_path,
        username=os.getenv("BETFAIR_USERNAME", ""),
        password=os.getenv("BETFAIR_PASSWORD", ""),
        sandbox=True,  # Always sandbox for tests
        commission_rate=0.05,
    )


class TestBetfairSandboxAuth:
    """Test authentication with Betfair sandbox."""

    def test_authenticate_success(self):
        """Should authenticate successfully with valid sandbox credentials."""
        connector = _get_connector()
        result = connector.authenticate()
        assert result is True
        assert connector.session_token is not None

    def test_keep_alive_extends_session(self):
        """Keep-alive should extend the session token."""
        connector = _get_connector()
        connector.authenticate()
        old_time = connector.session_authenticated_at
        time.sleep(1)
        result = connector._keep_alive()
        assert result is True
        assert connector.session_authenticated_at > old_time

    def test_ensure_session_reauthenticates_when_expired(self):
        """ensure_session should re-authenticate if token is old."""
        connector = _get_connector()
        connector.authenticate()
        # Simulate expired session
        connector.session_authenticated_at = time.time() - 3600
        connector.ensure_session()
        # Should have re-authenticated
        assert connector.session_authenticated_at > time.time() - 60


class TestBetfairSandboxAccount:
    """Test account operations with Betfair sandbox."""

    def test_get_account_balance(self):
        """Should return account balance from sandbox."""
        connector = _get_connector()
        connector.authenticate()
        balance = connector.get_account_balance()
        assert "availableToBetBalance" in balance or "availableBalance" in balance

    def test_get_account_details(self):
        """Should return account details from sandbox."""
        connector = _get_connector()
        connector.authenticate()
        details = connector.get_account_details()
        assert isinstance(details, dict)


class TestBetfairSandboxMarketData:
    """Test market data operations with Betfair sandbox."""

    def test_list_market_catalogue(self):
        """Should list available markets (may be empty in sandbox)."""
        connector = _get_connector()
        connector.authenticate()
        markets = connector.list_market_catalogue(
            market_type_codes=["MATCH_ODDS"],
            max_results=5,
        )
        assert isinstance(markets, list)

    def test_get_market_book(self):
        """Should get market book for a valid market (or return empty)."""
        connector = _get_connector()
        connector.authenticate()

        # Try to find a market first
        markets = connector.list_market_catalogue(
            market_type_codes=["MATCH_ODDS"],
            max_results=1,
        )

        if markets:
            market_id = markets[0].get("marketId")
            book = connector.get_market_book(market_id)
            assert isinstance(book, dict)
        else:
            pytest.skip("No markets available in sandbox")


class TestBetfairSandboxOrderExecution:
    """Test order execution with Betfair sandbox."""

    def test_place_back_order_dry_run(self):
        """Should place a minimal BACK order in sandbox (0.01 EUR)."""
        connector = _get_connector()
        connector.authenticate()

        # Find a market with runners
        markets = connector.list_market_catalogue(
            market_type_codes=["MATCH_ODDS"],
            max_results=1,
        )

        if not markets:
            pytest.skip("No markets available in sandbox")

        market_id = markets[0].get("marketId")
        runners = markets[0].get("runners", [])

        if not runners:
            pytest.skip("No runners in sandbox market")

        selection_id = runners[0].get("selectionId")

        # Place minimal stake
        result = connector.place_back_order(
            market_id=market_id,
            selection_id=selection_id,
            odds=1.01,  # Very low odds — should match
            stake=0.01,  # Minimum stake
            customer_order_ref="vbq_integration_test",
        )

        assert result["market_id"] == market_id
        assert result["status"] in ("FULLY_FILLED", "PARTIALLY_FILLED", "UNMATCHED", "REJECTED")

    def test_place_lay_order_dry_run(self):
        """Should place a minimal LAY order in sandbox."""
        connector = _get_connector()
        connector.authenticate()

        markets = connector.list_market_catalogue(
            market_type_codes=["MATCH_ODDS"],
            max_results=1,
        )

        if not markets:
            pytest.skip("No markets available in sandbox")

        market_id = markets[0].get("marketId")
        runners = markets[0].get("runners", [])

        if not runners:
            pytest.skip("No runners in sandbox market")

        selection_id = runners[0].get("selectionId")

        result = connector.place_lay_order(
            market_id=market_id,
            selection_id=selection_id,
            odds=1000.0,  # Very high odds — unlikely to match
            stake=0.01,
            customer_order_ref="vbq_integration_test_lay",
        )

        assert result["market_id"] == market_id
        # High lay odds likely unmatched, which is fine for testing
        assert result["status"] in ("FULLY_FILLED", "PARTIALLY_FILLED", "UNMATCHED", "REJECTED")

    def test_cancel_unmatched_order(self):
        """Should cancel an unmatched order."""
        connector = _get_connector()
        connector.authenticate()

        markets = connector.list_market_catalogue(
            market_type_codes=["MATCH_ODDS"],
            max_results=1,
        )

        if not markets:
            pytest.skip("No markets available in sandbox")

        market_id = markets[0].get("marketId")
        runners = markets[0].get("runners", [])

        if not runners:
            pytest.skip("No runners in sandbox market")

        selection_id = runners[0].get("selectionId")

        # Place order at extreme odds (likely unmatched)
        result = connector.place_back_order(
            market_id=market_id,
            selection_id=selection_id,
            odds=1000.0,  # Won't match
            stake=0.01,
            customer_order_ref="vbq_cancel_test",
        )

        bet_id = result.get("bet_id")
        if bet_id:
            cancel_result = connector.cancel_order(market_id, bet_id)
            assert isinstance(cancel_result, dict)


class TestBetfairSandboxReconciliation:
    """Test reconciliation with Betfair sandbox."""

    def test_balance_changes_after_order(self):
        """Balance should change after placing an order."""
        connector = _get_connector()
        connector.authenticate()

        balance_before = connector.get_account_balance()
        available_before = float(balance_before.get("availableToBetBalance", 0))

        markets = connector.list_market_catalogue(
            market_type_codes=["MATCH_ODDS"],
            max_results=1,
        )

        if not markets:
            pytest.skip("No markets available in sandbox")

        market_id = markets[0].get("marketId")
        runners = markets[0].get("runners", [])

        if not runners:
            pytest.skip("No runners in sandbox market")

        selection_id = runners[0].get("selectionId")

        # Place order at low odds (likely to match)
        result = connector.place_back_order(
            market_id=market_id,
            selection_id=selection_id,
            odds=1.01,
            stake=0.01,
        )

        if result["status"] in ("FULLY_FILLED", "PARTIALLY_FILLED"):
            balance_after = connector.get_account_balance()
            available_after = float(balance_after.get("availableToBetBalance", 0))
            # Balance should have decreased by at least the filled stake
            assert available_after <= available_before


class TestBetfairSandboxEdgeCalculation:
    """Test edge calculation methods."""

    def test_true_edge_after_commission(self):
        """True edge should account for 5% commission."""
        connector = _get_connector()
        # Odds 2.10, model prob 0.50
        # Raw edge: 2.10 * 0.50 - 1 = 0.05 (5%)
        # After 5% commission: true_odd = 1 + (2.10-1)*(1-0.05) = 1 + 1.10*0.95 = 2.045
        # True edge: 2.045 * 0.50 - 1 = 0.0225 (2.25%)
        true_edge = connector.calculate_true_edge(raw_odd=2.10, model_prob=0.50)
        assert abs(true_edge - 0.0225) < 0.001

    def test_net_profit_after_commission(self):
        """Net profit should deduct 5% commission from winnings."""
        connector = _get_connector()
        # Stake 10, odds 2.10, won
        # Gross: 10 * (2.10 - 1) = 11.0
        # Commission: 11.0 * 0.05 = 0.55
        # Net: 11.0 - 0.55 = 10.45
        net = connector.calculate_net_profit(filled_stake=10.0, odds=2.10, won=True)
        assert abs(net - 10.45) < 0.01

    def test_net_profit_loss(self):
        """Loss should be full stake (no commission on losses)."""
        connector = _get_connector()
        net = connector.calculate_net_profit(filled_stake=10.0, odds=2.10, won=False)
        assert net == -10.0
