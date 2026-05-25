"""
Bootstrap backtesting — confidence intervals for backtest metrics.

Generates thousands of resampled bankroll paths (with replacement) and
computes confidence intervals for ROI, Sharpe, max drawdown, etc.

This answers: "Is an ROI of 3% statistically different from zero?"

Two methods:
1. Simple bootstrap: Resample individual bets (i.i.d. assumption)
2. Block bootstrap: Resample blocks of consecutive bets (preserves autocorrelation)

Usage:
    from src.simulation.bootstrap_backtest import BootstrapBacktest

    bt = BootstrapBacktest(n_bootstrap=1000, block_size=5)
    result = bt.run(bets_df, pnl_col="pnl_units")
    print(result["ci_95"]["roi"])  # e.g., [0.005, 0.058]
    print(result["p_value"]["roi_positive"])  # e.g., 0.012
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("bootstrap_backtest")


class BootstrapBacktest:
    """
    Bootstrap resampling for backtest confidence intervals.

    Supports both simple (i.i.d.) and block bootstrap (preserving
    temporal autocorrelation in bet returns).
    """

    def __init__(
        self,
        n_bootstrap: int = 1000,
        block_size: int = 5,
        method: str = "block",
        confidence_level: float = 0.95,
        initial_bankroll: float = 1000.0,
        seed: Optional[int] = 42,
    ):
        """
        Args:
            n_bootstrap: Number of bootstrap resamples
            block_size: Block size for block bootstrap (preserves autocorrelation)
            method: "simple" (i.i.d.) or "block" (moving block bootstrap)
            confidence_level: Confidence level for intervals (0.95 = 95% CI)
            initial_bankroll: Starting bankroll for drawdown calculation
            seed: Random seed for reproducibility
        """
        self.n_bootstrap = n_bootstrap
        self.block_size = block_size
        self.method = method
        self.confidence_level = confidence_level
        self.initial_bankroll = initial_bankroll
        self.rng = np.random.RandomState(seed)

    def _resample_simple(self, returns: np.ndarray) -> np.ndarray:
        """Simple bootstrap: resample individual returns with replacement."""
        n = len(returns)
        indices = self.rng.randint(0, n, size=n)
        return returns[indices]

    def _resample_block(self, returns: np.ndarray) -> np.ndarray:
        """Moving Block Bootstrap: resample blocks of consecutive returns."""
        n = len(returns)
        block_size = min(self.block_size, n)
        n_blocks = int(np.ceil(n / block_size))

        resampled = []
        for _ in range(n_blocks):
            start = self.rng.randint(0, n - block_size + 1)
            block = returns[start:start + block_size]
            resampled.extend(block)

        return np.array(resampled[:n])

    def _compute_metrics_from_returns(self, returns: np.ndarray) -> Dict[str, float]:
        """Compute key metrics from a returns array."""
        if len(returns) == 0:
            return {"roi": 0.0, "sharpe": 0.0, "max_drawdown": 0.0, "win_rate": 0.0, "profit_factor": 0.0}

        # ROI
        total_pnl = np.sum(returns)
        total_stake = len(returns)  # Unit stakes
        roi = total_pnl / total_stake if total_stake > 0 else 0.0

        # Sharpe (annualized)
        mean_r = np.mean(returns)
        std_r = np.std(returns)
        sharpe = (mean_r / std_r * np.sqrt(365)) if std_r > 1e-10 else 0.0

        # Max drawdown
        equity = self.initial_bankroll + np.cumsum(returns * self.initial_bankroll)
        peak = np.maximum.accumulate(equity)
        dd = (peak - equity) / np.where(peak > 0, peak, 1.0)
        max_dd = float(np.max(dd)) if len(dd) > 0 else 0.0

        # Win rate
        win_rate = float(np.mean(returns > 0))

        # Profit factor
        gross_profit = np.sum(returns[returns > 0])
        gross_loss = abs(np.sum(returns[returns < 0]))
        profit_factor = float(gross_profit / gross_loss) if gross_loss > 1e-10 else 0.0

        return {
            "roi": round(roi, 6),
            "sharpe": round(sharpe, 4),
            "max_drawdown": round(max_dd, 6),
            "win_rate": round(win_rate, 4),
            "profit_factor": round(profit_factor, 4),
            "total_pnl": round(total_pnl, 4),
        }

    def run(
        self,
        bets_df: pd.DataFrame,
        pnl_col: str = "pnl_units",
        extra_cols: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run bootstrap backtest on a DataFrame of historical bets.

        Args:
            bets_df: DataFrame with at least a PnL column
            pnl_col: Column name for per-bet profit/loss
            extra_cols: Additional columns to include in bootstrap (e.g., "clv_pct")

        Returns:
            Dict with:
            - point_estimates: Original (non-resampled) metrics
            - ci_95: 95% confidence intervals for each metric
            - ci_90: 90% confidence intervals
            - p_value: P-values for key hypotheses
            - bootstrap_distribution: Full distribution of each metric
            - n_bootstrap: Number of resamples
        """
        if bets_df.empty:
            return {"error": "No bets to bootstrap"}

        returns = bets_df[pnl_col].astype(float).values
        n_bets = len(returns)

        if n_bets < 10:
            logger.warning("Very few bets (%d) for bootstrap — results may be unreliable", n_bets)

        # Point estimates from original data
        point_estimates = self._compute_metrics_from_returns(returns)

        # Bootstrap resampling
        logger.info(
            "Running %d bootstrap resamples (%s method, block_size=%d) on %d bets",
            self.n_bootstrap, self.method, self.block_size, n_bets,
        )

        bootstrap_metrics = {key: [] for key in point_estimates}

        for i in range(self.n_bootstrap):
            if self.method == "block":
                resampled = self._resample_block(returns)
            else:
                resampled = self._resample_simple(returns)

            metrics = self._compute_metrics_from_returns(resampled)
            for key in bootstrap_metrics:
                bootstrap_metrics[key].append(metrics.get(key, 0.0))

        # Convert to arrays
        for key in bootstrap_metrics:
            bootstrap_metrics[key] = np.array(bootstrap_metrics[key])

        # Confidence intervals
        alpha = 1.0 - self.confidence_level
        ci_95 = {}
        ci_90 = {}
        for key, values in bootstrap_metrics.items():
            ci_95[key] = {
                "lower": round(float(np.percentile(values, 2.5)), 6),
                "upper": round(float(np.percentile(values, 97.5)), 6),
            }
            ci_90[key] = {
                "lower": round(float(np.percentile(values, 5)), 6),
                "upper": round(float(np.percentile(values, 95)), 6),
            }

        # P-values
        roi_values = bootstrap_metrics["roi"]
        p_roi_positive = float(np.mean(roi_values <= 0))  # P(ROI <= 0)
        p_roi_negative = float(np.mean(roi_values >= 0))  # P(ROI >= 0)

        sharpe_values = bootstrap_metrics["sharpe"]
        p_sharpe_positive = float(np.mean(sharpe_values <= 0))

        dd_values = bootstrap_metrics["max_drawdown"]
        p_dd_gt_20 = float(np.mean(dd_values > 0.20))

        p_values = {
            "roi_positive": round(p_roi_positive, 4),
            "roi_negative": round(p_roi_negative, 4),
            "sharpe_positive": round(p_sharpe_positive, 4),
            "drawdown_gt_20pct": round(p_dd_gt_20, 4),
        }

        result = {
            "point_estimates": point_estimates,
            "ci_95": ci_95,
            "ci_90": ci_90,
            "p_value": p_values,
            "bootstrap_distribution": {
                key: {
                    "mean": round(float(np.mean(values)), 6),
                    "std": round(float(np.std(values)), 6),
                    "min": round(float(np.min(values)), 6),
                    "max": round(float(np.max(values)), 6),
                }
                for key, values in bootstrap_metrics.items()
            },
            "n_bootstrap": self.n_bootstrap,
            "n_bets": n_bets,
            "method": self.method,
            "block_size": self.block_size,
        }

        # Log summary
        logger.info(
            "Bootstrap results: ROI=%.4f [%.4f, %.4f] (p=%.4f), "
            "Sharpe=%.4f [%.4f, %.4f], MaxDD=%.4f [%.4f, %.4f]",
            point_estimates["roi"],
            ci_95["roi"]["lower"], ci_95["roi"]["upper"],
            p_roi_positive,
            point_estimates["sharpe"],
            ci_95["sharpe"]["lower"], ci_95["sharpe"]["upper"],
            point_estimates["max_drawdown"],
            ci_95["max_drawdown"]["lower"], ci_95["max_drawdown"]["upper"],
        )

        return result

    def run_from_simulator(
        self,
        simulator_result: Dict[str, Any],
        pnl_col: str = "pnl_units",
    ) -> Dict[str, Any]:
        """
        Convenience method: run bootstrap on output from HonestHistoricalSimulator.

        Args:
            simulator_result: Dict from simulator.run() with "bets" key
            pnl_col: PnL column name
        """
        bets = simulator_result.get("bets", [])
        if not bets:
            return {"error": "No bets in simulator result"}

        bets_df = pd.DataFrame(bets)
        return self.run(bets_df, pnl_col=pnl_col)
