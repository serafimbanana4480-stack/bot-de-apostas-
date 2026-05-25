"""Tests for backtest vs paper trading comparison script."""
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.backtest_paper_comparison import apply_paper_friction, compute_metrics, text_scatter_plot


@pytest.fixture
def sample_bets():
    rng = np.random.RandomState(123)
    bets = []
    for i in range(20):
        won = rng.random() > 0.5
        odd = round(rng.uniform(1.5, 3.0), 2)
        bets.append({
            "match_id": f"m{i}",
            "date": f"2024-01-{i+1:02d}",
            "open_odd": odd,
            "won": won,
            "pnl_units": (odd - 1.0) if won else -1.0,
            "clv_pct": rng.uniform(-1, 3),
        })
    return bets


def test_apply_paper_friction_slippage_negative(sample_bets):
    """Paper odds should be <= backtest odds (slippage against us)."""
    paper = apply_paper_friction(sample_bets, rng_seed=42)
    for pb, bb in zip(paper, sample_bets):
        assert pb["exec_odd"] <= bb["open_odd"] + 1e-9
        assert pb["exec_odd"] >= 1.01
        assert pb["slippage_pct"] <= 0.0


def test_apply_paper_friction_pnl_lower(sample_bets):
    """With negative slippage, winning PnL should be lower than backtest."""
    paper = apply_paper_friction(sample_bets, rng_seed=42)
    for pb, bb in zip(paper, sample_bets):
        if bb["won"]:
            assert pb["pnl_units"] < bb["pnl_units"]
        else:
            assert pb["pnl_units"] == bb["pnl_units"] == -1.0


def test_apply_paper_friction_same_count(sample_bets):
    """Without rejection, paper bet count equals backtest bet count."""
    paper = apply_paper_friction(sample_bets, rng_seed=42)
    assert len(paper) == len(sample_bets)


def test_compute_metrics_basic(sample_bets):
    """Metrics should be reasonable for known bet set."""
    m = compute_metrics(sample_bets)
    assert m["total_bets"] == len(sample_bets)
    assert -1.0 <= m["roi_per_bet"] <= 2.0
    assert 0.0 <= m["win_rate"] <= 1.0
    assert m["profit_factor"] >= 0


def test_compute_metrics_empty():
    """Empty bet list should return zero metrics."""
    m = compute_metrics([])
    assert m["total_bets"] == 0
    assert m["roi_per_bet"] == 0.0
    assert m["sharpe_proxy"] == 0.0
    assert m["max_drawdown_units"] == 0.0


def test_text_scatter_plot():
    """Scatter plot should return non-empty ASCII string."""
    import pandas as pd
    daily_bt = pd.DataFrame({"pnl_units": [1.0, -0.5, 2.0, -1.0]}, index=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"])
    daily_paper = pd.DataFrame({"pnl_units": [0.9, -0.4, 1.8, -1.1]}, index=["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"])
    plot = text_scatter_plot(daily_bt, daily_paper)
    assert "Backtest" in plot
    assert "*" in plot
