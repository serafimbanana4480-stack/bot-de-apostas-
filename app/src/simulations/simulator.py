from typing import Any, Dict, Optional

import numpy as np


class BankrollSimulator:
    """
    Realistic bankroll simulator using empirical odds distributions.

    Instead of assuming static odds (e.g. 2.0), this samples from the
    historical distribution of odds and probabilities observed in backtests,
    yielding a far more accurate Risk-of-Ruin estimate.
    """

    def __init__(self, n_simulations: int = 5000):
        self.n_simulations = n_simulations

    def run_simulation(
        self,
        probs: np.ndarray,
        odds: np.ndarray,
        stakes_pct: np.ndarray,
        initial_bankroll: float = 1000.0,
        flat_staking: bool = False,
        flat_stake_amount: float = 10.0,
        commission_pct: float = 0.0,
        bootstrap_odds: bool = True,
        seed: int = 42,
    ) -> Dict[str, Any]:
        """
        Runs Monte Carlo pathways.

        Parameters
        ----------
        probs : np.ndarray
            Predicted probabilities for each bet.
        odds : np.ndarray
            Bookmaker odds for each bet (can be empirical distribution).
        stakes_pct : np.ndarray
            Stake as fraction of current bankroll per bet.
        initial_bankroll : float
        flat_staking : bool
        flat_stake_amount : float
        commission_pct : float
            Commission / overround deducted from winning bets (e.g. 5% = 0.05).
        bootstrap_odds : bool
            If True, odds are resampled with replacement from the provided
            odds array for each simulation, reflecting empirical variance.
        seed : int
            RNG seed for reproducibility.

        Returns
        -------
        Dict with risk metrics.
        """
        probs = np.asarray(probs, dtype=float)
        odds_arr = np.asarray(odds, dtype=float)
        stakes_pct_arr = np.asarray(stakes_pct, dtype=float)
        n_bets = len(probs)

        if n_bets == 0:
            return {
                "mean_final_bankroll": initial_bankroll,
                "median_final_bankroll": initial_bankroll,
                "percentile_5": initial_bankroll,
                "percentile_95": initial_bankroll,
                "profit_probability": 0.0,
                "ruin_probability": 0.0,
                "mean_max_drawdown_pct": 0.0,
                "max_drawdown_absolute_pct": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
            }

        rng = np.random.default_rng(seed=seed)

        # For each simulation, optionally bootstrap the odds sequence
        if bootstrap_odds and len(odds_arr) > 1:
            sim_odds = rng.choice(odds_arr, size=(self.n_simulations, n_bets), replace=True)
        else:
            sim_odds = np.broadcast_to(odds_arr, (self.n_simulations, n_bets)).copy()

        # Win/loss matrix
        random_trials = rng.random((self.n_simulations, n_bets))
        wins = random_trials < probs

        trajectories = np.zeros((self.n_simulations, n_bets + 1))
        trajectories[:, 0] = initial_bankroll
        pnl_per_bet = np.zeros((self.n_simulations, n_bets))

        for b in range(n_bets):
            current_bankroll = trajectories[:, b]

            if flat_staking:
                stake = np.full(self.n_simulations, flat_stake_amount)
            else:
                stake = current_bankroll * stakes_pct_arr[b]
                stake = np.minimum(stake, current_bankroll * 0.95)

            gross_win = stake * (sim_odds[:, b] - 1.0)
            # Apply commission on winnings only
            net_win = gross_win * (1.0 - commission_pct)
            net_loss = -stake

            outcome_change = np.where(wins[:, b], net_win, net_loss)
            pnl_per_bet[:, b] = outcome_change
            trajectories[:, b + 1] = np.maximum(0.0, current_bankroll + outcome_change)

        final_bankrolls = trajectories[:, -1]

        # Drawdowns
        peaks = np.maximum.accumulate(trajectories, axis=1)
        peaks = np.where(peaks == 0, 1.0, peaks)
        drawdowns = (peaks - trajectories) / peaks
        max_drawdowns = np.max(drawdowns, axis=1) * 100.0

        # Ruin: dropping below 50% of initial (configurable)
        ruin_threshold = initial_bankroll * 0.5
        dropped_below_half = np.any(trajectories < ruin_threshold, axis=1)
        ruin_prob = np.mean(dropped_below_half)

        # Path-level returns for Sharpe / Sortino
        total_returns = (final_bankrolls - initial_bankroll) / initial_bankroll
        mean_return = np.mean(total_returns)
        std_return = np.std(total_returns, ddof=1)
        downside_std = np.std(total_returns[total_returns < 0], ddof=1) if np.any(total_returns < 0) else 1e-9

        sharpe = mean_return / std_return if std_return > 0 else 0.0
        sortino = mean_return / downside_std if downside_std > 0 else 0.0

        return {
            "mean_final_bankroll": float(np.mean(final_bankrolls)),
            "median_final_bankroll": float(np.median(final_bankrolls)),
            "percentile_5": float(np.percentile(final_bankrolls, 5)),
            "percentile_95": float(np.percentile(final_bankrolls, 95)),
            "profit_probability": float(np.mean(final_bankrolls > initial_bankroll)),
            "ruin_probability": float(ruin_prob),
            "mean_max_drawdown_pct": float(np.mean(max_drawdowns)),
            "max_drawdown_absolute_pct": float(np.max(max_drawdowns)),
            "sharpe_ratio": float(sharpe),
            "sortino_ratio": float(sortino),
            "n_simulations": self.n_simulations,
            "n_bets": n_bets,
            "commission_pct": commission_pct,
        }
