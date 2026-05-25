#!/usr/bin/env python3
"""
Compliance Audit — verifies legal and governance requirements.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    print("\n" + "=" * 70)
    print("  COMPLIANCE AUDIT REPORT")
    print("=" * 70 + "\n")

    checks = []

    # 1. Bet logging
    print("[1] Checking bet audit logging...")
    from src.execution.order_tracker import OrderTracker
    tracker = OrderTracker(audit_log_path="logs/test_audit.jsonl")
    tracker.log_decision({
        "event_id": "TEST-001",
        "model_version": "v1.2.3",
        "input_features_hash": "abc123",
        "predicted_prob": 0.55,
        "edge": 0.05,
        "kelly_stake": 10.0,
        "final_stake": 8.0,
        "odds_available": 2.10,
        "odds_used": 2.08,
        "executed": True,
        "result_settled": False,
        "human_override": False,
    })
    lines = Path("logs/test_audit.jsonl").read_text().strip().split("\n")
    entry = json.loads(lines[-1])
    Path("logs/test_audit.jsonl").unlink()

    required = {
        "event_id", "timestamp", "model_version", "input_features_hash",
        "predicted_prob", "edge", "kelly_stake", "final_stake",
        "odds_available", "odds_used", "executed", "result_settled", "human_override"
    }
    missing = [k for k in required if entry.get(k) is None and k != "timestamp"]
    missing += [k for k in required if k == "timestamp" and not entry.get(k)]
    ok1 = len(missing) == 0
    checks.append(("Bet audit logging (timestamp, stake, odds, result, reason)", ok1))
    print(f"    {'PASS' if ok1 else 'FAIL'} — Missing fields: {missing if missing else 'none'}")

    # 2. Human override
    print("\n[2] Checking human override mechanism...")
    from src.execution.override import HumanOverrideLog
    override = HumanOverrideLog()
    record = override.record_override("EVT-123", 50.0, 0.0, "SKIP", "Suspicious line movement")
    settled = override.settle_override("EVT-123", won=True, odds=2.0)
    perf = override.evaluate_override_performance()
    ok2 = record is not None and settled is not None and perf["total_overrides"] == 1
    checks.append(("Human override core logic", ok2))
    print(f"    Core logic: {'PASS' if ok2 else 'FAIL'}")
    cli_integration = False
    checks.append(("Human override CLI integration (vbq --override)", cli_integration))
    print(f"    CLI integration: {'PASS' if cli_integration else 'FAIL — NOT IMPLEMENTED'}")

    # 3. Stake limits
    print("\n[3] Checking stake and daily loss limits...")
    from src.core.config import settings
    max_stake = getattr(settings, "MAX_STAKE_EUR", None)
    max_daily_loss = getattr(settings, "MAX_DAILY_LOSS_PCT", None)
    ok3 = max_stake is not None and max_daily_loss is not None
    checks.append(("Stake limits configured", ok3))
    print(f"    MAX_STAKE_EUR: {max_stake}")
    print(f"    MAX_DAILY_LOSS_PCT: {max_daily_loss}%")

    # Check if enforced — test with bankroll large enough to exceed MAX_STAKE_EUR
    from src.risk.portfolio_optimizer import PortfolioOptimizer
    from src.risk.bankroll import BankrollManager
    bm_large = BankrollManager(initial_bankroll=10000.0)
    sized = bm_large.calculate_stake(probability=0.55, odds=2.0)
    # The pipeline uses max_stake_per_bet_pct=2% bankroll, so 2% of 10000 = 200 EUR
    # This would exceed MAX_STAKE_EUR=50 if not capped
    exceeds = max_stake is not None and sized > max_stake
    enforced = not exceeds  # Pass only if the system actually caps it
    checks.append(("MAX_STAKE_EUR enforced in pipeline", enforced))
    print(f"    Simulated Kelly stake (bankroll=10k): {sized:.2f} EUR")
    print(f"    Enforced in pipeline: {'PASS' if enforced else 'FAIL — NOT ENFORCED'}")
    if exceeds:
        print(f"    [!] Stake {sized:.2f} EUR exceeds MAX_STAKE_EUR={max_stake} but is NOT blocked")

    # 4. Circuit breaker
    print("\n[4] Checking circuit breaker / kill switch...")
    from src.risk.circuit_breaker import CircuitBreaker
    from src.risk.circuit_breakers import DailyLossCircuitBreaker

    cb = CircuitBreaker(initial_bankroll=1000.0, max_drawdown_limit=0.10)
    for _ in range(20):
        cb.record_pnl_result(-20.0)
    wager = cb.validate_wager(bet_stake=10.0)
    auto_halt = cb.is_paused and wager["action"] == "ABORT"

    dl = DailyLossCircuitBreaker(max_daily_loss_pct=5.0)
    dl.bankroll_start = 1000.0
    dl.daily_pnl = -60.0
    daily_triggered = not dl.check()

    has_manual_stop = hasattr(cb, "emergency_stop") and callable(getattr(cb, "emergency_stop", None))

    checks.append(("Auto circuit breaker on drawdown", auto_halt))
    checks.append(("Daily loss circuit breaker", daily_triggered))
    checks.append(("Manual emergency_stop() method", has_manual_stop))
    print(f"    Auto-halt on drawdown: {'PASS' if auto_halt else 'FAIL'}")
    print(f"    Daily loss triggered: {'PASS' if daily_triggered else 'FAIL'}")
    print(f"    Manual emergency_stop(): {'PASS' if has_manual_stop else 'FAIL — NOT IMPLEMENTED'}")

    # 5. P&L reporting
    print("\n[5] Checking P&L reporting and export...")
    from src.accounting.pnl import FinancialAccountingEngine
    engine = FinancialAccountingEngine()
    engine.record_transaction(
        event_id="EVT-001", stake=10.0, odds_predicted=2.10, odds_executed=2.08,
        won=True, provider="Betfair", currency="EUR"
    )
    summary = engine.get_portfolio_summary()
    ok5 = summary.get("total_net_pnl", 0) != 0
    has_export = hasattr(engine, "export_csv") or hasattr(engine, "to_excel")
    checks.append(("P&L summary generation", ok5))
    checks.append(("CSV/Excel export for accounting", has_export))
    print(f"    P&L summary: {'PASS' if ok5 else 'FAIL'}")
    print(f"    Export method: {'PASS' if has_export else 'FAIL — NOT IMPLEMENTED'}")

    # Summary
    total = len(checks)
    passed = sum(1 for _, ok in checks if ok)

    print("\n" + "=" * 70)
    print(f"  RESULT: {passed}/{total} checks passed")
    print("=" * 70)

    print("\n  GAPS IDENTIFIED:")
    gaps = []
    if not cli_integration:
        gaps.append("Human override has no CLI integration (vbq.py missing --override)")
    if not enforced:
        gaps.append("MAX_STAKE_EUR is configured but NEVER enforced in the pipeline")
    if not has_manual_stop:
        gaps.append("No manual emergency_stop() method (only auto drawdown halt)")
    if not has_export:
        gaps.append("No CSV/Excel export for accounting ledger")

    for gap in gaps:
        print(f"    - {gap}")

    if not gaps:
        print("    None — all compliance requirements met.")

    # Save report
    report = {
        "checks": {name: ok for name, ok in checks},
        "gaps": gaps,
    }
    out = PROJECT_ROOT / "data" / "reports" / "compliance_audit.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Report saved to: {out}")
    print("=" * 70 + "\n")

    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main())
