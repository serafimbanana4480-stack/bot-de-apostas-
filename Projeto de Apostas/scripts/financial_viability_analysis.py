#!/usr/bin/env python3
"""
Financial viability analysis — net profitability after all costs.

Simulates 1000 bets with Kelly 0.25, Betfair 5% commission,
FX costs (EUR/GBP 0.85), and API fees ($50/month).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.monitoring.operational_costs import OperationalCostMonitor


def simulate_bets(
    n_bets: int = 1000,
    mean_clv_pct: float = 1.363,
    win_rate: float = 0.4678,
    avg_odds: float = 2.20,
    kelly_fraction: float = 0.25,
    bankroll: float = 1000.0,
    commission_rate: float = 0.05,
    fx_spread_pct: float = 0.015,
    api_cost_per_month: float = 50.0,
    rng_seed: int = 42,
) -> dict:
    """
    Simulate betting with full cost accounting.

    Theory: expected gross ROI ≈ mean_clv_pct (CLV is the theoretical edge).
    We simulate actual outcomes with variance around the expected value.
    """
    rng = np.random.RandomState(rng_seed)
    monitor = OperationalCostMonitor(cost_threshold_pct=999.0)  # suppress per-bet alerts

    # Amortize API cost per bet
    api_cost_per_bet = api_cost_per_month / n_bets

    gross_pnl = 0.0
    turnover = 0.0
    wins = 0
    losses = 0
    total_commission = 0.0
    total_fx_cost = 0.0
    total_api_cost = 0.0

    for i in range(n_bets):
        # Kelly stake: f* = edge / (odds - 1), stake = bankroll * f* * kelly_fraction
        edge = mean_clv_pct / 100.0
        f_star = edge / (avg_odds - 1.0) if avg_odds > 1 else edge
        stake = bankroll * f_star * kelly_fraction
        stake = max(1.0, min(stake, bankroll * 0.05))  # cap at 5% bankroll

        # Simulate outcome: expected return = stake * edge
        # Actual return = expected + noise
        expected_return = stake * edge
        noise = rng.normal(0, stake * 0.5)  # high variance in betting
        actual_return = expected_return + noise

        # Determine win/loss for tracking
        won = actual_return > 0
        if won:
            gross_profit = actual_return
            commission = gross_profit * commission_rate  # on net profit
            wins += 1
        else:
            gross_profit = actual_return
            commission = 0.0
            losses += 1

        # FX cost on stake
        fx_cost = stake * fx_spread_pct

        # Net for this bet
        bet_net = gross_profit - commission - fx_cost - api_cost_per_bet

        # Record in monitor
        monitor.record_bet(stake=stake, commission_rate=commission_rate, gross_pnl=gross_profit)
        monitor.record_api_call(provider="oddsapi", cost=api_cost_per_bet)
        monitor.record_fx_cost(fx_cost)

        gross_pnl += gross_profit
        turnover += stake
        total_commission += commission
        total_fx_cost += fx_cost
        total_api_cost += api_cost_per_bet

    report = monitor.get_report()

    return {
        "n_bets": n_bets,
        "gross_pnl": gross_pnl,
        "net_pnl": gross_pnl - total_commission - total_fx_cost - total_api_cost,
        "turnover": turnover,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / n_bets,
        "gross_roi_pct": (gross_pnl / turnover) * 100 if turnover else 0,
        "net_roi_pct": ((gross_pnl - total_commission - total_fx_cost - total_api_cost) / turnover) * 100 if turnover else 0,
        "total_commission": total_commission,
        "total_fx_cost": total_fx_cost,
        "total_api_cost": total_api_cost,
        "total_costs": total_commission + total_fx_cost + total_api_cost,
        "cost_pct_of_gross": (abs(total_commission + total_fx_cost + total_api_cost) / abs(gross_pnl)) * 100 if gross_pnl != 0 else 0,
        "monitor_report": report,
    }


def find_break_even_clv(
    n_bets: int = 1000,
    avg_odds: float = 2.20,
    kelly_fraction: float = 0.25,
    bankroll: float = 1000.0,
    commission_rate: float = 0.05,
    fx_spread_pct: float = 0.015,
    api_cost_per_month: float = 50.0,
) -> float:
    """Find CLV where expected net ROI = 0."""
    # Theoretical: gross ROI = CLV%
    # Net ROI = CLV% * (1 - commission_rate) - fx_cost% - api_cost%
    # For break-even: CLV * (1 - 0.05) = fx_cost% + api_cost%
    # But fx_cost% and api_cost% depend on stake, which depends on CLV (Kelly)
    # Iterative solution:

    api_cost_per_bet = api_cost_per_month / n_bets

    for clv in np.arange(0.0, 20.0, 0.001):
        edge = clv / 100.0
        f_star = edge / (avg_odds - 1.0) if avg_odds > 1 else edge
        stake = max(1.0, min(bankroll * f_star * kelly_fraction, bankroll * 0.05))
        turnover = stake * n_bets

        gross_profit = turnover * edge  # expected
        commission = gross_profit * commission_rate
        fx_cost = turnover * fx_spread_pct
        api_cost = api_cost_per_bet * n_bets

        net = gross_profit - commission - fx_cost - api_cost
        net_roi = (net / turnover) * 100 if turnover else 0

        if net_roi >= 0:
            return clv
    return 20.0


def main() -> int:
    print("\n" + "=" * 70)
    print("  FINANCIAL VIABILITY ANALYSIS")
    print("=" * 70 + "\n")

    # 1. CLV from report
    clv_report_path = PROJECT_ROOT / "data" / "reports" / "clv_report.json"
    if clv_report_path.exists():
        with open(clv_report_path) as f:
            clv_data = json.load(f)
        mean_clv = clv_data.get("mean_clv_pct", 1.363)
    else:
        mean_clv = 1.363
    print(f"[1] Baseline CLV from report: {mean_clv:.3f}%")

    # 2. Simulate 1000 bets
    print("\n[2] Simulating 1000 bets with full cost accounting...")
    sim = simulate_bets(
        n_bets=1000,
        mean_clv_pct=mean_clv,
        win_rate=0.4678,
        avg_odds=2.20,
        kelly_fraction=0.25,
        bankroll=1000.0,
        commission_rate=0.05,
        fx_spread_pct=0.015,
        api_cost_per_month=50.0,
    )

    # 3. Results table
    print("\n" + "=" * 70)
    print("  RESULTS TABLE (1000 bets, Kelly 0.25)")
    print("=" * 70)
    print(f"  {'Metric':<45} {'Value':>15}")
    print("  " + "-" * 60)
    print(f"  {'Gross PnL (before costs)':<45} {sim['gross_pnl']:>+14.2f} EUR")
    print(f"  {'Net PnL (after all costs)':<45} {sim['net_pnl']:>+14.2f} EUR")
    print(f"  {'Total Turnover':<45} {sim['turnover']:>14.2f} EUR")
    print(f"  {'Gross ROI':<45} {sim['gross_roi_pct']:>14.2f}%")
    print(f"  {'Net ROI':<45} {sim['net_roi_pct']:>14.2f}%")
    print(f"  {'Win Rate':<45} {sim['win_rate']*100:>14.2f}%")
    print(f"  {'Wins / Losses':<45} {sim['wins']:>8} / {sim['losses']}")

    print("\n" + "=" * 70)
    print("  COST BREAKDOWN")
    print("=" * 70)
    print(f"  {'Commission (Betfair 5% on profit)':<45} {sim['total_commission']:>14.2f} EUR")
    print(f"  {'FX Costs (1.5% spread on turnover)':<45} {sim['total_fx_cost']:>14.2f} EUR")
    print(f"  {'API Fees ($50/mo amortized)':<45} {sim['total_api_cost']:>14.2f} EUR")
    print(f"  {'Total Costs':<45} {sim['total_costs']:>14.2f} EUR")
    print(f"  {'Cost % of Gross Profit':<45} {sim['cost_pct_of_gross']:>14.2f}%")

    # 4. Break-even CLV
    print("\n[3] Computing break-even CLV...")
    break_even_clv = find_break_even_clv(
        n_bets=1000,
        avg_odds=2.20,
        kelly_fraction=0.25,
        bankroll=1000.0,
        commission_rate=0.05,
        fx_spread_pct=0.015,
        api_cost_per_month=50.0,
    )
    print(f"    Break-even CLV: {break_even_clv:.3f}%")
    print(f"    Current CLV: {mean_clv:.3f}%")
    print(f"    Margin above break-even: {mean_clv - break_even_clv:+.3f}%")

    # 5. OperationalCostMonitor verification
    print("\n[4] OperationalCostMonitor report:")
    mr = sim["monitor_report"]
    print(f"    Gross profit (monitor): {mr['gross_profit']} EUR")
    print(f"    Total costs (monitor): {mr['total_costs']} EUR")
    print(f"    Net profit (monitor): {mr['net_profit']} EUR")
    print(f"    Cost %: {mr['cost_pct']}%")
    print(f"    Alert triggered: {mr['alert']}")

    # 6. Recommendations
    print("\n" + "=" * 70)
    print("  RECOMMENDATIONS")
    print("=" * 70)
    if sim['net_roi_pct'] <= 0:
        print("  [!] SYSTEM NOT PROFITABLE after costs.")
        print(f"      Net ROI: {sim['net_roi_pct']:.2f}%")
        if break_even_clv > mean_clv:
            print(f"      Break-even CLV ({break_even_clv:.2f}%) > Current CLV ({mean_clv:.2f}%)")
            print("      -> Improve model edge or reduce costs")
        print("      Options:")
        print("        1. Increase stakes (higher turnover dilutes fixed costs)")
        print("        2. Switch to lower-commission exchange (Pinnacle 0% vs Betfair 5%)")
        print("        3. Reduce FX exposure (EUR account or hedging)")
        print("        4. Negotiate lower API fees or batch calls")
    else:
        print(f"  [OK] System is profitable after costs.")
        print(f"      Net ROI: {sim['net_roi_pct']:.2f}%")
        if sim['cost_pct_of_gross'] > 20:
            print(f"      Warning: Costs consume {sim['cost_pct_of_gross']:.1f}% of gross profit")
            print("      -> Optimize: reduce commission (Pinnacle), batch API calls")

    # 7. Scenario table
    print("\n" + "=" * 70)
    print("  SCENARIO ANALYSIS: Net ROI at different CLV levels")
    print("=" * 70)
    print(f"  {'CLV %':<10} {'Gross ROI':<12} {'Net ROI':<12} {'Status':<20}")
    print("  " + "-" * 55)
    for clv in [0.5, 1.0, 1.363, 2.0, 3.0, 5.0]:
        s = simulate_bets(
            n_bets=1000, mean_clv_pct=clv, win_rate=0.4678, avg_odds=2.20,
            kelly_fraction=0.25, bankroll=1000.0, commission_rate=0.05,
            fx_spread_pct=0.015, api_cost_per_month=50.0,
            rng_seed=int(clv * 100),
        )
        status = "PROFITABLE" if s['net_roi_pct'] > 0 else "UNPROFITABLE"
        print(f"  {clv:<10.2f} {s['gross_roi_pct']:<12.2f}% {s['net_roi_pct']:<12.2f}% {status:<20}")

    # 8. Save report
    report = {
        "mean_clv_pct": mean_clv,
        "simulation": sim,
        "break_even_clv_pct": break_even_clv,
        "recommendation": "PROFITABLE" if sim['net_roi_pct'] > 0 else "UNPROFITABLE",
    }
    out = PROJECT_ROOT / "data" / "reports" / "financial_viability.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Report saved to: {out}")
    print("=" * 70 + "\n")

    return 0 if sim['net_roi_pct'] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
