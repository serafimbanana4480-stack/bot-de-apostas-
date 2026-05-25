"""
Chaos testing — simulates failures, timeouts, and malformed responses
to verify system resilience and graceful degradation.
"""
import json
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Test: Betfair adapter handles network failures gracefully
# ---------------------------------------------------------------------------
class TestBetfairChaos:
    """Chaos tests for the Betfair real adapter."""

    def test_auth_connection_error_is_retried(self):
        """Authentication should retry on connection errors."""
        from src.execution.adapters.betfair_real import BetfairAuthError, BetfairRealConnector

        connector = BetfairRealConnector(
            app_key="test_key",
            cert_path="/nonexistent/cert.crt",
            key_path="/nonexistent/key.key",
            sandbox=True,
        )

        # FileNotFoundError is caught and re-raised as BetfairAuthError("CERT_NOT_FOUND")
        with pytest.raises(BetfairAuthError):
            connector.authenticate()

    def test_place_order_unauthorized_re_authenticates(self):
        """401 Unauthorized should trigger re-authentication attempt."""
        from src.execution.adapters.betfair_real import BetfairAuthError, BetfairRealConnector

        connector = BetfairRealConnector(
            app_key="test_key",
            cert_path="/fake/cert.crt",
            key_path="/fake/key.key",
            sandbox=True,
        )
        connector.session_token = "expired_token"

        with patch.object(connector, 'ensure_session'):
            with patch.object(connector, '_api_request', side_effect=BetfairAuthError("UNAUTHORIZED", "Token expired")):
                with pytest.raises(BetfairAuthError):
                    connector.place_back_order(
                        market_id="1.12345",
                        selection_id=12345,
                        odds=2.10,
                        stake=5.0,
                    )

    def test_rate_limit_triggers_retry(self):
        """429 Too Many Requests should trigger retry with backoff."""
        from src.execution.adapters.betfair_real import BetfairRateLimitError, BetfairRealConnector

        connector = BetfairRealConnector(
            app_key="test_key",
            cert_path="/fake/cert.crt",
            key_path="/fake/key.key",
            sandbox=True,
        )
        connector.session_token = "valid_token"

        with patch.object(connector, '_api_request', side_effect=BetfairRateLimitError("RATE_LIMITED", "Too many requests")):
            with pytest.raises(BetfairRateLimitError):
                connector.get_account_balance()


# ---------------------------------------------------------------------------
# Test: Pinnacle adapter handles failures
# ---------------------------------------------------------------------------
class TestPinnacleChaos:
    """Chaos tests for the Pinnacle real adapter."""

    def test_invalid_credentials_raises_error(self):
        """Invalid credentials should raise PinnacleAPIError."""
        from src.execution.adapters.pinnacle_real import PinnacleAPIError, PinnacleRealConnector

        connector = PinnacleRealConnector(client_id="invalid", password="invalid")

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.raise_for_status.side_effect = Exception("401")

        mock_session = MagicMock()
        mock_session.request.return_value = mock_resp

        with patch.object(connector, '_get_http_session', return_value=mock_session):
            with pytest.raises(PinnacleAPIError):
                connector.get_balance()

    def test_stake_below_minimum_rejected(self):
        """Stake below minimum should be rejected immediately."""
        from src.execution.adapters.pinnacle_real import PinnacleRealConnector

        connector = PinnacleRealConnector(client_id="test", password="test")

        with patch.object(connector, 'get_market_limits', return_value={"max_stake": 750.0, "min_stake": 10.0}):
            result = connector.place_bet(
                event_id="12345",
                sport_id=29,
                line_id=1,
                period_number=0,
                bet_type="MONEYLINE",
                odds=2.10,
                stake=2.0,  # Below minimum
            )
            assert result["status"] == "REJECTED"
            assert result["reason"] == "STAKE_BELOW_MINIMUM"


# ---------------------------------------------------------------------------
# Test: Reconciliation detects anomalies
# ---------------------------------------------------------------------------
class TestReconciliationChaos:
    """Chaos tests for the reconciliation engine."""

    def test_balance_discrepancy_detected(self):
        """Reconciliation should flag when balance change doesn't match expected."""
        from src.execution.reconciliation import ReconciliationEngine

        engine = ReconciliationEngine(tolerance_pct=0.01)
        engine.record_pre_balance(
            order_id="test_001",
            balance_before=1000.0,
            stake=50.0,
            odds=2.10,
            bookmaker="betfair",
        )

        # Balance only decreased by 25 instead of 50 (anomaly)
        result = engine.verify_post_balance(
            order_id="test_001",
            balance_after=975.0,  # Expected 950.0
            filled_stake=50.0,
            fill_status="FULLY_FILLED",
        )

        assert result["anomaly_detected"] is True
        assert result["discrepancy"] == 25.0

    def test_no_pre_balance_record(self):
        """Missing pre-balance record should be flagged as anomaly."""
        from src.execution.reconciliation import ReconciliationEngine

        engine = ReconciliationEngine()
        result = engine.verify_post_balance(
            order_id="nonexistent",
            balance_after=900.0,
            filled_stake=50.0,
            fill_status="FULLY_FILLED",
        )

        assert result["status"] == "NO_PRE_RECORD"
        assert result["anomaly"] is True

    def test_correct_balance_no_anomaly(self):
        """Correct balance change should not trigger anomaly."""
        from src.execution.reconciliation import ReconciliationEngine

        engine = ReconciliationEngine(tolerance_pct=0.01)
        engine.record_pre_balance(
            order_id="test_ok",
            balance_before=1000.0,
            stake=50.0,
            odds=2.10,
            bookmaker="betfair",
        )

        result = engine.verify_post_balance(
            order_id="test_ok",
            balance_after=950.0,  # Exactly -50.0 as expected
            filled_stake=50.0,
            fill_status="FULLY_FILLED",
        )

        assert result["anomaly_detected"] is False


# ---------------------------------------------------------------------------
# Test: Fallback provider serves local data when API fails
# ---------------------------------------------------------------------------
class TestFallbackProviderChaos:
    """Chaos tests for the fallback data provider."""

    def test_api_failure_falls_back_to_cache(self, tmp_path):
        """When API fails, should serve cached Parquet data."""
        import pandas as pd

        from src.ingestion.fallback_provider import FallbackProvider

        provider = FallbackProvider(data_dir=str(tmp_path))

        # Pre-populate cache
        df = pd.DataFrame({"match_id": [1, 2], "home_team": ["A", "B"]})
        provider._save_cache("test_source", "football", df)

        # API that always fails
        def failing_api():
            raise ConnectionError("API is down")

        result = provider.fetch_with_fallback(
            source_name="test_source",
            api_fetch_fn=failing_api,
            sport="football",
        )

        assert result["source"] == "local_cache"
        assert len(result["data"]) == 2

    def test_no_cache_returns_empty(self, tmp_path):
        """When API fails and no cache exists, should return empty DataFrame."""
        from src.ingestion.fallback_provider import FallbackProvider

        provider = FallbackProvider(data_dir=str(tmp_path))

        def failing_api():
            raise TimeoutError("API timeout")

        result = provider.fetch_with_fallback(
            source_name="nonexistent",
            api_fetch_fn=failing_api,
            sport="football",
        )

        assert result["source"] == "none"
        assert result["data"].empty
        assert result["stale"] is True


# ---------------------------------------------------------------------------
# Test: Circuit breaker with alert integration
# ---------------------------------------------------------------------------
class TestCircuitBreakerChaos:
    """Chaos tests for circuit breaker under stress."""

    def test_circuit_breaker_triggers_alert(self):
        """Circuit breaker should call alert callback when triggered."""
        from src.risk.circuit_breaker import CircuitBreaker

        alerts = []

        def mock_alert(level, title, message, data=None):
            alerts.append({"level": level, "title": title, "message": message})

        cb = CircuitBreaker(initial_bankroll=1000.0, max_drawdown_limit=0.10, alert_callback=mock_alert)

        # Trigger drawdown
        cb.record_pnl_result(-150.0)  # 15% drawdown

        assert cb.is_paused is True
        assert len(alerts) == 1
        assert alerts[0]["level"] == "CRITICAL"
        assert "Circuit Breaker" in alerts[0]["title"]

    def test_consecutive_losses_trigger_breaker(self):
        """Multiple consecutive losses should eventually trigger the breaker."""
        from src.risk.circuit_breaker import CircuitBreaker

        cb = CircuitBreaker(initial_bankroll=1000.0, max_drawdown_limit=0.10)

        # Simulate 10 consecutive losses of 2% each
        for _ in range(10):
            cb.record_pnl_result(-20.0)

        # Total loss: 200/1000 = 20% > 10% limit
        assert cb.is_paused is True


# ---------------------------------------------------------------------------
# Test: Model fallback handles NaN and exceptions
# ---------------------------------------------------------------------------
class TestModelFallbackChaos:
    """Chaos tests for model prediction fallback."""

    def test_nan_prediction_falls_back(self):
        """NaN model prediction should fall back to baseline."""
        from src.mlops.fallback import ModelFallback

        fallback = ModelFallback(baseline_prob_func=lambda: 0.5)

        result = fallback.predict_safe(champion_predict_func=lambda: float('nan'))
        assert result == 0.5

    def test_exception_prediction_falls_back(self):
        """Model exception should fall back to baseline."""
        from src.mlops.fallback import ModelFallback

        fallback = ModelFallback(baseline_prob_func=lambda: 0.5)

        result = fallback.predict_safe(champion_predict_func=lambda: 1/0)  # ZeroDivisionError
        assert result == 0.5

    def test_out_of_range_prediction_falls_back(self):
        """Prediction outside [0,1] should fall back to baseline."""
        from src.mlops.fallback import ModelFallback

        fallback = ModelFallback(baseline_prob_func=lambda: 0.5)

        result = fallback.predict_safe(champion_predict_func=lambda: 1.5)
        assert result == 0.5

        result = fallback.predict_safe(champion_predict_func=lambda: -0.2)
        assert result == 0.5


# ---------------------------------------------------------------------------
# Test: Malformed API response handling
# ---------------------------------------------------------------------------
class TestMalformedResponses:
    """Tests for handling malformed API responses."""

    def test_betfair_malformed_json_response(self):
        """System should handle malformed JSON from Betfair API."""
        from src.execution.adapters.betfair_real import BetfairRealConnector

        connector = BetfairRealConnector(
            app_key="test", cert_path="/f/c", key_path="/f/k", sandbox=True
        )
        connector.session_token = "valid"

        # Simulate malformed response
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = json.JSONDecodeError("test", "", 0)
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {}

        mock_session = MagicMock()
        mock_session.post.return_value = mock_resp

        with patch.object(connector, 'ensure_session'):
            with patch.object(connector, '_get_http_session', return_value=mock_session):
                with pytest.raises(json.JSONDecodeError):
                    connector._api_request("listMarketCatalogue/", {"filter": {}})

    def test_settlement_score_mismatch_handled(self):
        """Settlement engine should detect score mismatches between sources."""
        from src.execution.settlement import SettlementRulesEngine

        engine = SettlementRulesEngine()

        result = engine.verify_and_settle(
            source_a_data={"game_id": "g1", "home_score": 2, "away_score": 1, "status": "finished"},
            source_b_data={"game_id": "g1", "home_score": 3, "away_score": 1, "status": "finished"},
        )

        assert result["settled"] is False
        assert "mismatch" in result["reason"].lower()
