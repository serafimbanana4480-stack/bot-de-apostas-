"""
Calibration Metrics & Backtest Diagnostics

Implements:
- Expected Calibration Error (ECE)
- Reliability Diagrams
- Brier Score decomposition (reliability + resolution + uncertainty)
- Monte Carlo Risk of Ruin
- Kelly Criterion with sanity checks
- Complete BacktestReport dataclass
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. ECE & Reliability Diagram
# ---------------------------------------------------------------------------

def compute_ece(probs: np.ndarray, outcomes: np.ndarray, n_bins: int = 10) -> float:
    """
    Compute Expected Calibration Error (ECE) using equal-width bins.

    Args:
        probs: Predicted probabilities (0-1)
        outcomes: Actual binary outcomes (0 or 1)
        n_bins: Number of bins

    Returns:
        ECE value (0 = perfectly calibrated)
    """
    probs = np.asarray(probs).flatten()
    outcomes = np.asarray(outcomes).flatten()

    if len(probs) != len(outcomes):
        raise ValueError("probs and outcomes must have the same length")
    if len(probs) == 0:
        return 0.0

    # Clamp to avoid edge issues
    probs = np.clip(probs, 1e-6, 1 - 1e-6)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        low, high = bin_edges[i], bin_edges[i + 1]
        if i == n_bins - 1:
            mask = (probs >= low) & (probs <= high)
        else:
            mask = (probs >= low) & (probs < high)

        if mask.sum() == 0:
            continue

        bin_conf = probs[mask].mean()
        bin_acc = outcomes[mask].mean()
        bin_weight = mask.sum() / len(probs)
        ece += bin_weight * abs(bin_conf - bin_acc)

    return float(ece)


def compute_ece_by_bin(
    probs: np.ndarray, outcomes: np.ndarray, n_bins: int = 10
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Returns bin_centers, bin_accuracies, bin_confidences, bin_counts for plotting.
    """
    probs = np.asarray(probs).flatten()
    outcomes = np.asarray(outcomes).flatten()
    probs = np.clip(probs, 1e-6, 1 - 1e-6)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    centers = []
    accuracies = []
    confidences = []
    counts = []

    for i in range(n_bins):
        low, high = bin_edges[i], bin_edges[i + 1]
        if i == n_bins - 1:
            mask = (probs >= low) & (probs <= high)
        else:
            mask = (probs >= low) & (probs < high)

        cnt = int(mask.sum())
        counts.append(cnt)
        if cnt == 0:
            centers.append((low + high) / 2)
            accuracies.append(np.nan)
            confidences.append(np.nan)
        else:
            centers.append(probs[mask].mean())
            accuracies.append(outcomes[mask].mean())
            confidences.append(probs[mask].mean())

    return (
        np.array(centers),
        np.array(accuracies),
        np.array(confidences),
        np.array(counts),
    )


def plot_reliability_diagram(
    probs: np.ndarray,
    outcomes: np.ndarray,
    title: str = "Reliability Diagram",
    n_bins: int = 10,
) -> Any:
    """
    Plot a reliability diagram using matplotlib.

    Returns the matplotlib Figure object.
    """
    import matplotlib.pyplot as plt

    centers, accuracies, confidences, counts = compute_ece_by_bin(
        probs, outcomes, n_bins=n_bins
    )
    ece = compute_ece(probs, outcomes, n_bins=n_bins)

    fig, ax = plt.subplots(figsize=(7, 7))

    # Bar plot with counts
    valid = ~np.isnan(accuracies)
    ax.bar(
        centers[valid],
        accuracies[valid],
        width=(1.0 / n_bins) * 0.8,
        edgecolor="black",
        alpha=0.7,
        label="Observed frequency",
    )

    # Perfect calibration line
    ax.plot([0, 1], [0, 1], "k--", label="Perfect calibration")

    # Annotate counts
    for c, a, cnt in zip(centers[valid], accuracies[valid], counts[valid]):
        ax.text(c, a + 0.02, str(cnt), ha="center", va="bottom", fontsize=8)

    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of positives")
    ax.set_title(f"{title}\nECE = {ece:.4f}  (n={len(probs)})")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    return fig


# ---------------------------------------------------------------------------
# 2. Brier Score Decomposition
# ---------------------------------------------------------------------------

def brier_decomposition(probs: np.ndarray, outcomes: np.ndarray) -> Dict[str, float]:
    """
    Decompose Brier Score into:
        - uncertainty (irreducible)
        - reliability (calibration error)
        - resolution (discrimination ability)

    Formula (Murphy 1973):
        BS = reliability - resolution + uncertainty
    """
    probs = np.asarray(probs).flatten()
    outcomes = np.asarray(outcomes).flatten()

    if len(probs) != len(outcomes):
        raise ValueError("probs and outcomes must have same length")
    if len(probs) == 0:
        return {"brier_score": 0.0, "reliability": 0.0, "resolution": 0.0, "uncertainty": 0.0}

    n = len(probs)
    climo = outcomes.mean()  # base rate

    # Overall Brier Score
    bs = float(np.mean((probs - outcomes) ** 2))

    # Use 10 equal-width bins for decomposition
    bin_edges = np.linspace(0.0, 1.0, 11)
    reliability = 0.0
    resolution = 0.0

    for i in range(10):
        low, high = bin_edges[i], bin_edges[i + 1]
        if i == 9:
            mask = (probs >= low) & (probs <= high)
        else:
            mask = (probs >= low) & (probs < high)

        cnt = mask.sum()
        if cnt == 0:
            continue

        bin_prob = probs[mask].mean()
        bin_obs = outcomes[mask].mean()
        weight = cnt / n

        reliability += weight * (bin_prob - bin_obs) ** 2
        resolution += weight * (bin_obs - climo) ** 2

    uncertainty = climo * (1 - climo)

    return {
        "brier_score": bs,
        "reliability": float(reliability),
        "resolution": float(resolution),
        "uncertainty": float(uncertainty),
    }


# ---------------------------------------------------------------------------
# 3. BacktestReport dataclass
# ---------------------------------------------------------------------------

@dataclass
class BacktestReport:
    """Complete backtest report with mandatory calibration metrics."""

    roi: float
    profit_factor: float
    sharpe: float
    sortino: float
    brier_score: float
    ece: float
    clv: float
    yield_per_bet: float
    n_bets: int
    win_rate: float
    avg_odds: float
    avg_edge: float
    max_drawdown: float
    risk_of_ruin: float
    kelly_ratio: float
    statistical_significance: float
    min_bets_for_significance: int
    # Optional extra fields
    brier_reliability: float = 0.0
    brier_resolution: float = 0.0
    brier_uncertainty: float = 0.0
    model_probs: np.ndarray = field(default_factory=lambda: np.array([]))
    outcomes: np.ndarray = field(default_factory=lambda: np.array([]))
    league_breakdown: Dict[str, Dict[str, float]] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "roi": self.roi,
            "profit_factor": self.profit_factor,
            "sharpe": self.sharpe,
            "sortino": self.sortino,
            "brier_score": self.brier_score,
            "ece": self.ece,
            "clv": self.clv,
            "yield_per_bet": self.yield_per_bet,
            "n_bets": self.n_bets,
            "win_rate": self.win_rate,
            "avg_odds": self.avg_odds,
            "avg_edge": self.avg_edge,
            "max_drawdown": self.max_drawdown,
            "risk_of_ruin": self.risk_of_ruin,
            "kelly_ratio": self.kelly_ratio,
            "statistical_significance": self.statistical_significance,
            "min_bets_for_significance": self.min_bets_for_significance,
            "brier_reliability": self.brier_reliability,
            "brier_resolution": self.brier_resolution,
            "brier_uncertainty": self.brier_uncertainty,
            "league_breakdown": self.league_breakdown,
            "warnings": self.warnings,
        }
        return d

    def is_acceptable(self) -> Tuple[bool, List[str]]:
        """Check if backtest meets acceptance criteria."""
        issues = []
        if self.ece > 0.05:
            issues.append(f"ECE {self.ece:.4f} > 0.05 — model is poorly calibrated")
        if self.n_bets < 2000:
            issues.append(f"n_bets {self.n_bets} < 2000 — insufficient sample size")
        if self.statistical_significance >= 0.10:
            issues.append(f"p-value {self.statistical_significance:.4f} >= 0.10 — ROI not statistically significant")
        if self.risk_of_ruin > 0.10:
            issues.append(f"Risk of Ruin {self.risk_of_ruin:.2%} > 10%")
        if self.max_drawdown > 0.20:
            issues.append(f"Max Drawdown {self.max_drawdown:.2%} > 20%")
        if self.brier_score > 0.22:
            issues.append(f"Brier Score {self.brier_score:.4f} > 0.22")
        return len(issues) == 0, issues


# ---------------------------------------------------------------------------
# 4. Monte Carlo Risk of Ruin
# ---------------------------------------------------------------------------

def monte_carlo_risk_of_ruin(
    win_rate: float,
    avg_odds: float,
    kelly_fraction: float,
    n_sims: int = 10000,
    initial_bankroll: float = 1000.0,
    ruin_threshold: float = 0.01,
    max_bets: int = 3000,
) -> float:
    """
    Estimate Risk of Ruin via Monte Carlo simulation.

    Args:
        win_rate: Observed win rate (0-1)
        avg_odds: Average decimal odds taken
        kelly_fraction: Fraction of Kelly used (e.g. 0.25)
        n_sims: Number of Monte Carlo runs
        initial_bankroll: Starting bankroll
        ruin_threshold: Fraction of bankroll considered ruin (default 1%)
        max_bets: Maximum bets per simulation

    Returns:
        Probability of ruin (0-1)
    """
    if win_rate <= 0 or avg_odds <= 1.0 or kelly_fraction <= 0:
        return 1.0

    # Full Kelly fraction
    b = avg_odds - 1.0
    p = win_rate
    q = 1 - p
    kelly_full = (b * p - q) / b
    if kelly_full <= 0:
        return 1.0

    stake_pct = kelly_full * kelly_fraction
    # Cap stake at 5% per bet
    stake_pct = min(stake_pct, 0.05)

    ruin_level = initial_bankroll * ruin_threshold
    n_ruins = 0

    for _ in range(n_sims):
        bankroll = initial_bankroll
        for _ in range(max_bets):
            if bankroll <= ruin_level:
                n_ruins += 1
                break
            stake = bankroll * stake_pct
            won = np.random.random() < win_rate
            if won:
                bankroll += stake * (avg_odds - 1.0)
            else:
                bankroll -= stake

    return n_ruins / n_sims


# ---------------------------------------------------------------------------
# 5. Kelly with Sanity Checks
# ---------------------------------------------------------------------------

def kelly_with_sanity(
    model_prob: float,
    odds: float,
    ece: float = 0.0,
    fraction: float = 0.10,
    max_kelly_full: float = 0.15,
    n_bets_so_far: int = 0,
    roi_so_far: float = 0.0,
    current_drawdown: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculate fractional Kelly with multiple sanity checks.

    Returns dict with:
        - stake_fraction: recommended fraction of bankroll
        - kelly_full: full Kelly fraction (for info)
        - adjusted_prob: probability adjusted for calibration error
        - passed: bool, whether the signal passes sanity checks
        - reason: str, explanation if rejected
    """
    if odds <= 1.0 or model_prob <= 0 or model_prob >= 1:
        return {
            "stake_fraction": 0.0,
            "kelly_full": 0.0,
            "adjusted_prob": model_prob,
            "passed": False,
            "reason": "Invalid odds or probability",
        }

    # Adjust probability for calibration error
    adjusted_prob = model_prob * (1.0 - ece)
    adjusted_prob = max(0.001, min(0.999, adjusted_prob))

    # Full Kelly
    b = odds - 1.0
    p = adjusted_prob
    q = 1 - p
    kelly_full = (b * p - q) / b

    if kelly_full <= 0:
        return {
            "stake_fraction": 0.0,
            "kelly_full": 0.0,
            "adjusted_prob": adjusted_prob,
            "passed": False,
            "reason": "Negative edge after calibration adjustment",
        }

    # Sanity check 1: Kelly full > 15% → overconfidence signal
    if kelly_full > max_kelly_full:
        return {
            "stake_fraction": 0.0,
            "kelly_full": float(kelly_full),
            "adjusted_prob": adjusted_prob,
            "passed": False,
            "reason": f"Kelly full {kelly_full:.2%} > {max_kelly_full:.2%} — overconfidence",
        }

    # Dynamic fractional Kelly
    dynamic_fraction = fraction
    if n_bets_so_far < 100:
        dynamic_fraction = 0.10
    elif n_bets_so_far < 500:
        dynamic_fraction = 0.15
    else:
        if roi_so_far > 0:
            dynamic_fraction = min(0.25, 0.15 + (roi_so_far * 2))
        else:
            dynamic_fraction = 0.10

    # Reduce fraction after drawdown > 20%
    if current_drawdown > 0.20:
        dynamic_fraction *= 0.5

    stake_fraction = kelly_full * dynamic_fraction
    # Hard cap at 5% of bankroll per bet
    stake_fraction = min(stake_fraction, 0.05)

    return {
        "stake_fraction": float(stake_fraction),
        "kelly_full": float(kelly_full),
        "adjusted_prob": adjusted_prob,
        "passed": True,
        "reason": None,
        "dynamic_fraction": dynamic_fraction,
    }


# ---------------------------------------------------------------------------
# 6. Statistical helpers
# ---------------------------------------------------------------------------

def statistical_significance_roi(
    returns: np.ndarray,
) -> Tuple[float, float]:
    """
    One-sample t-test H0: mean return = 0.

    Returns:
        (t_statistic, p_value)
    """
    returns = np.asarray(returns)
    if len(returns) < 2 or returns.std() == 0:
        return 0.0, 1.0

    t_stat, p_value = stats.ttest_1samp(returns, 0.0)
    # One-sided test (we care about positive ROI)
    p_value_one_sided = p_value / 2.0 if t_stat > 0 else 1.0 - (p_value / 2.0)
    return float(t_stat), float(p_value_one_sided)


def compute_sortino(returns: np.ndarray, risk_free: float = 0.0) -> float:
    """Sortino ratio using downside deviation."""
    returns = np.asarray(returns)
    excess = returns - risk_free
    downside = excess[excess < 0]
    if len(downside) == 0 or downside.std() == 0:
        return 0.0
    return float(excess.mean() / downside.std())


def compute_clv(
    model_probs: np.ndarray,
    closing_probs: np.ndarray,
) -> float:
    """
    Closing Line Value: average difference between model prob and closing implied prob.
    Positive CLV means model beats the closing line.
    """
    if len(model_probs) == 0:
        return 0.0
    return float(np.mean(model_probs - closing_probs))


# ---------------------------------------------------------------------------
# 7. Build BacktestReport from bets DataFrame
# ---------------------------------------------------------------------------

def build_backtest_report(
    df_bets: pd.DataFrame,
    model_probs: Optional[np.ndarray] = None,
    outcomes: Optional[np.ndarray] = None,
    closing_probs: Optional[np.ndarray] = None,
    league_labels: Optional[np.ndarray] = None,
    n_mc_sims: int = 10000,
) -> BacktestReport:
    """
    Build a complete BacktestReport from a DataFrame of bets.

    Expected df_bets columns:
        - stake, profit, odds, edge, won
    Optional:
        - model_prob, actual_outcome (for calibration)
    """
    if df_bets.empty:
        return BacktestReport(
            roi=0.0,
            profit_factor=0.0,
            sharpe=0.0,
            sortino=0.0,
            brier_score=0.0,
            ece=0.0,
            clv=0.0,
            yield_per_bet=0.0,
            n_bets=0,
            win_rate=0.0,
            avg_odds=0.0,
            avg_edge=0.0,
            max_drawdown=0.0,
            risk_of_ruin=1.0,
            kelly_ratio=0.0,
            statistical_significance=1.0,
            min_bets_for_significance=2000,
            warnings=["No bets placed"],
        )

    df = df_bets.copy()
    total_stake = df["stake"].sum()
    total_profit = df["profit"].sum()
    roi = total_profit / total_stake if total_stake > 0 else 0.0

    returns = df["profit"] / df["stake"]
    win_rate = float(df["won"].mean()) if "won" in df.columns else 0.0
    avg_odds = float(df["odds"].mean()) if "odds" in df.columns else 0.0
    avg_edge = float(df["edge"].mean()) if "edge" in df.columns else 0.0

    # Profit factor
    gains = df.loc[df["profit"] > 0, "profit"].sum()
    losses = abs(df.loc[df["profit"] < 0, "profit"].sum())
    profit_factor = gains / losses if losses > 0 else float("inf")

    # Sharpe
    sharpe = float(returns.mean() / returns.std()) if returns.std() > 0 else 0.0

    # Sortino
    sortino = compute_sortino(returns.values)

    # Drawdown from bankroll history
    bankroll = 1000.0  # assume starting bankroll
    peak = bankroll
    max_dd = 0.0
    for _, row in df.iterrows():
        bankroll += row["profit"]
        if bankroll > peak:
            peak = bankroll
        dd = (peak - bankroll) / peak
        max_dd = max(max_dd, dd)

    # Risk of ruin (Monte Carlo)
    ror = monte_carlo_risk_of_ruin(
        win_rate=win_rate,
        avg_odds=avg_odds,
        kelly_fraction=0.25,
        n_sims=n_mc_sims,
    )

    # Statistical significance
    _, p_value = statistical_significance_roi(returns.values)

    # Kelly ratio (average recommended vs ideal)
    kelly_ratio = 0.0
    if "kelly_fraction" in df.columns:
        # ideal = what kelly would be with true win rate
        if avg_odds > 1.0 and win_rate > 0:
            b = avg_odds - 1.0
            ideal_kelly = (b * win_rate - (1 - win_rate)) / b
            ideal_kelly = max(0.0, ideal_kelly)
            avg_rec_kelly = df["kelly_fraction"].mean()
            kelly_ratio = avg_rec_kelly / ideal_kelly if ideal_kelly > 0 else 0.0

    # Calibration metrics
    brier = {"brier_score": 0.0, "reliability": 0.0, "resolution": 0.0, "uncertainty": 0.0}
    ece_val = 0.0
    clv_val = 0.0

    if model_probs is not None and outcomes is not None and len(model_probs) == len(outcomes):
        brier = brier_decomposition(model_probs, outcomes)
        ece_val = compute_ece(model_probs, outcomes)

    if closing_probs is not None and model_probs is not None and len(closing_probs) == len(model_probs):
        clv_val = compute_clv(model_probs, closing_probs)

    # League breakdown
    league_breakdown: Dict[str, Dict[str, float]] = {}
    if league_labels is not None and "league" in df.columns:
        for league, grp in df.groupby("league"):
            st = grp["stake"].sum()
            pr = grp["profit"].sum()
            league_breakdown[league] = {
                "n_bets": len(grp),
                "roi": pr / st if st > 0 else 0.0,
                "win_rate": float(grp["won"].mean()),
            }

    # Warnings
    warnings: List[str] = []
    if len(df) < 2000:
        warnings.append(f"Sample size {len(df)} < 2000 — insufficient for statistical conclusions")
    if ece_val > 0.05:
        warnings.append(f"ECE {ece_val:.4f} > 0.05 — model poorly calibrated")
    if p_value >= 0.10:
        warnings.append(f"p-value {p_value:.4f} >= 0.10 — ROI not statistically significant")
    if max_dd > 0.20:
        warnings.append(f"Max drawdown {max_dd:.2%} > 20%")

    # Minimum bets for significance at current yield
    yield_per_bet = total_profit / len(df) if len(df) > 0 else 0.0
    min_bets_sig = 2000
    if yield_per_bet > 0 and returns.std() > 0:
        # Solve for n where t-stat > 1.645 (one-sided 95%)
        # t = mean / (std / sqrt(n)) > 1.645
        # n > (1.645 * std / mean)^2
        required_n = int(np.ceil((1.645 * returns.std() / returns.mean()) ** 2))
        min_bets_sig = max(2000, required_n)

    return BacktestReport(
        roi=roi,
        profit_factor=profit_factor,
        sharpe=sharpe,
        sortino=sortino,
        brier_score=brier["brier_score"],
        ece=ece_val,
        clv=clv_val,
        yield_per_bet=yield_per_bet,
        n_bets=len(df),
        win_rate=win_rate,
        avg_odds=avg_odds,
        avg_edge=avg_edge,
        max_drawdown=max_dd,
        risk_of_ruin=ror,
        kelly_ratio=kelly_ratio,
        statistical_significance=p_value,
        min_bets_for_significance=min_bets_sig,
        brier_reliability=brier["reliability"],
        brier_resolution=brier["resolution"],
        brier_uncertainty=brier["uncertainty"],
        model_probs=model_probs if model_probs is not None else np.array([]),
        outcomes=outcomes if outcomes is not None else np.array([]),
        league_breakdown=league_breakdown,
        warnings=warnings,
    )
