import time

import pytest

from src.accounting.pnl import FinancialAccountingEngine
from src.execution.adapters.aggregator import OddsAggregator
from src.execution.adapters.betfair import BetfairAPIConnector
from src.execution.adapters.pinnacle import PinnacleAPIConnector
from src.execution.batcher import OrderBatcher
from src.execution.partial_fills import PartialFillManager
from src.ingestion.time_sync import TimeSyncCorrector
from src.market_microstructure.microstructure import LiquidityHeatmap, MarketMicrostructureEngine
from src.mlops.ab_testing.ab_engine import ThompsonSamplingBandit
from src.mlops.economic_learning.economic_learning import EconomicLearningLoop
from src.strategy_engine.portfolio import PortfolioRiskAllocator
from src.validation.causal_integrity.causal_lock import CausalIntegrityLock


def test_betfair_adapter():
    """Test Betfair sessions, heartbeats, BACK matching, and rate-limiting."""
    bf = BetfairAPIConnector("BF-ACC-77", commission_rate=0.05)
    
    # Needs session auth first
    res_no_auth = bf.place_back_order("MKT-01", odds=1.90, stake=100.0)
    assert res_no_auth["status"] == "REJECTED"
    
    assert bf.authenticate_session(app_key="my_key", cert_path="cert.pem", key_path="key.pem") is True
    assert bf.keep_alive_heartbeat() is True
    
    res = bf.place_back_order("MKT-01", odds=1.90, stake=300.0)
    assert res["status"] == "FULLY_FILLED"
    assert res["filled_stake"] == 300.0
    assert res["average_odds"] == ((200 * 1.95) + (100 * 1.92)) / 300.0

    net_win = bf.calculate_net_profit(filled_stake=100.0, odds=2.00, won=True)
    assert net_win == 100.0 * 0.95
    
    net_loss = bf.calculate_net_profit(filled_stake=100.0, odds=2.00, won=False)
    assert net_loss == -100.0


def test_pinnacle_adapter():
    """Test Pinnacle dynamic capping and Base64 basic authentication."""
    pin = PinnacleAPIConnector("PIN-ACC-11")
    
    assert pin.authenticate_session("secret_pass") is True
    
    res_capped = pin.place_bet("G-NBA-99", odds=1.95, stake=1000.0)
    assert res_capped["status"] == "PARTIALLY_FILLED"
    assert res_capped["filled_stake"] == 750.0
    assert res_capped["unfilled_stake"] == 250.0


def test_aggregator_and_latency_arbitrage():
    """Test normalizing odds formats and latency arbitrage detection."""
    agg = OddsAggregator()
    
    provider_odds = {"Pinnacle": 1.85, "Betfair_Back": 2.10, "Invalid": -1.0}
    normalized = agg.normalize_odds(provider_odds)
    
    assert normalized["Pinnacle"] == 1.85
    assert normalized["Betfair_Back"] == 2.10
    
    arbs = agg.detect_latency_arbitrage(normalized, reference_provider="Pinnacle", threshold=0.05)
    assert len(arbs) == 1
    assert arbs[0]["lagging_provider"] == "Betfair_Back"


def test_market_microstructure_and_heatmap():
    """Test order price impact drift, sharp money, and hours-to-kickoff heatmap."""
    me = MarketMicrostructureEngine()
    
    drift = me.estimate_price_impact(stake=200.0, market_liquidity=1000.0)
    assert drift > 0.0
    
    odds = [1.95, 1.93, 1.90, 1.88, 1.85]
    vols = [1000, 2000, 1000, 1500, 2000]
    
    flow = me.detect_sharp_money_flow(odds, vols)
    assert flow["sharp_flow_detected"] is True

    # Heatmap validation
    heatmap = LiquidityHeatmap()
    liq_far = heatmap.get_expected_liquidity(hours_to_kickoff=15.0, baseline_liquidity=1000.0)
    liq_near = heatmap.get_expected_liquidity(hours_to_kickoff=1.0, baseline_liquidity=1000.0)
    assert liq_far < liq_near
    assert liq_far == 150.0


def test_causal_integrity():
    """Test pre-game feature locking and validation deviation check."""
    lock = CausalIntegrityLock()
    
    features = {"elo_diff": 12.0, "rest_diff": 1.0}
    lock_hash = lock.lock_features("G-12", features, odds_at_lock=1.95)
    
    assert len(lock_hash) == 64
    
    assert lock.verify_causal_integrity("G-12", current_odds=1.95, lock_hash=lock_hash) is True
    assert lock.verify_causal_integrity("G-12", current_odds=1.75, lock_hash=lock_hash) is False


def test_portfolio_allocation():
    """Test correlation clustering and exposure caps balancing."""
    allocator = PortfolioRiskAllocator(max_portfolio_exposure=0.20, max_cluster_exposure=0.08)
    bankroll = 1000.0
    
    bets = [
        {"home_team": "Lakers", "requested_stake": 50.0},
        {"home_team": "Lakers", "requested_stake": 50.0},
        {"home_team": "Celtics", "requested_stake": 40.0}
    ]
    
    res = allocator.allocate_capital(bets, bankroll)
    
    lakers_bets = [b for b in res if b["home_team"] == "Lakers"]
    assert sum(b["allocated_stake"] for b in lakers_bets) == 80.0
    
    celtics_bets = [b for b in res if b["home_team"] == "Celtics"]
    assert celtics_bets[0]["allocated_stake"] == 40.0


def test_financial_accounting_fx():
    """Test multi-currency conversions, commissions, and tax simulation."""
    engine = FinancialAccountingEngine(tax_rate=0.15, base_currency="EUR", exchange_rates={"EUR": 1.0, "USD": 0.92})
    
    engine.record_transaction("T-01", stake=100.0, odds_predicted=2.0, odds_executed=1.95, won=True, provider="Pinnacle", currency="USD")
    
    summary = engine.get_portfolio_summary()
    assert summary["total_slippage_cost"] == pytest.approx(5.0 * 0.92)
    assert summary["total_realized_profit"] == pytest.approx(80.75 * 0.92)


def test_economic_learning():
    """Test attributing profits to features and evaluating profitability ratio."""
    loop = EconomicLearningLoop()
    
    features_a = {"elo_diff": 12.0, "rest_diff": 0.0}
    features_b = {"elo_diff": 12.0, "rest_diff": 2.0}
    
    loop.attribute_profit(features_a, pnl=95.0)
    loop.attribute_profit(features_b, pnl=-100.0)
    
    report = loop.evaluate_features_monetary_impact()
    
    assert report["elo_diff"]["total_monetary_contribution"] == -5.0
    assert report["elo_diff"]["status"] == "PRUNE_CANDIDATE"


def test_thompson_sampling_bandits():
    """Test Thompson Sampling bandit routing updates."""
    bandit = ThompsonSamplingBandit("champ", "challenger")
    
    assert bandit.alphas["champ"] == 1.0
    assert bandit.betas["champ"] == 1.0
    
    choices = [bandit.route_bandit() for _ in range(50)]
    assert len(choices) == 50
    
    bandit.update_feedback("challenger", won=True)
    assert bandit.alphas["challenger"] == 2.0
    
    bandit.update_feedback("champ", won=False)
    assert bandit.betas["champ"] == 2.0


def test_partial_fill_manager():
    """Test decision logic when handling partial order matches."""
    manager = PartialFillManager()
    
    # Combined odds: (100 * 1.95 + 100 * 1.92) / 200 = 1.935.
    # MAO is 1.90. Combined odds 1.935 >= 1.90 -> CHASE is approved!
    book_levels = [{"price": 1.92, "size": 150.0}]
    chase_res = manager.handle_partial_fill(
        event_id="E-10", 
        filled_stake=100.0, 
        filled_odds=1.95, 
        unfilled_stake=100.0, 
        min_acceptable_odds=1.90, 
        available_levels=book_levels
    )
    assert chase_res["decision"] == "CHASE"
    assert chase_res["chase_stake"] == 100.0
    assert chase_res["chase_odds"] == 1.92

    # If the combined odds drop below MAO (e.g. MAO is 1.98), we must cancel
    cancel_res = manager.handle_partial_fill(
        event_id="E-11", 
        filled_stake=100.0, 
        filled_odds=1.95, 
        unfilled_stake=100.0, 
        min_acceptable_odds=1.98, 
        available_levels=book_levels
    )
    assert cancel_res["decision"] == "CANCEL"
    assert cancel_res["reason"] == "SLIPPAGE_EXCEEDED_MAO"


def test_order_batcher():
    """Test sequential batch scheduling spacing."""
    batcher = OrderBatcher(delay_between_orders_ms=10.0) # short delay for tests
    
    orders = [{"event_id": "G1", "stake": 50}, {"event_id": "G2", "stake": 100}]
    
    def mock_execution(ord_dict):
        return {"status": "SUCCESS", "event_id": ord_dict["event_id"]}
        
    start_t = time.time()
    results = batcher.execute_batch(orders, mock_execution)
    duration = time.time() - start_t
    
    assert len(results) == 2
    assert results[0]["status"] == "SUCCESS"
    assert duration >= 0.01 # Spaced at least 10ms


def test_time_sync_corrector():
    """Test clock drift measurement and kickoff limit adjustments."""
    corrector = TimeSyncCorrector()
    
    # Mock api function returning server time
    # Let's simulate that server time is exactly 2.5 seconds ahead of client time
    def mock_ping():
        # returns server time. RTT is tiny, let's say client time is t, mid_point t, server is t + 2.5.
        return time.time() + 2.5
        
    offset = corrector.synchronize_clock(mock_ping)
    assert offset == pytest.approx(2.5, abs=0.1)
    
    # Scheduled kickoff = 10000. Safety margin = 30s. Offset = 2.5s.
    # Adjusted kickoff limit = 10000 - 2.5 - 30 = 9967.5
    limit = corrector.adjust_kickoff_limit(scheduled_kickoff_timestamp=10000.0, safety_margin_seconds=30.0)
    assert limit == pytest.approx(9967.5, abs=0.1)
