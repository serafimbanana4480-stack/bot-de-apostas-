from typing import Any, Dict

import numpy as np


class CVaR_KellyRiskManager:
    """
    Hedge-fund grade capital allocation controller:
    1. Adjusts Kelly fraction dynamically based on current rolling drawdown.
    2. Computes CVaR (Conditional Value at Risk / Expected Shortfall) to cap extreme tails.
    """
    def __init__(
        self, 
        initial_bankroll: float = 1000.0, 
        max_drawdown_limit: float = 0.15,
        cvar_confidence_level: float = 0.95,
        max_cvar_limit: float = 0.08
    ):
        self.initial_bankroll = initial_bankroll
        self.max_drawdown_limit = max_drawdown_limit
        self.cvar_confidence_level = cvar_confidence_level
        self.max_cvar_limit = max_cvar_limit
        
        self.current_bankroll = initial_bankroll
        self.peak_bankroll = initial_bankroll

    def update_bankroll(self, current_val: float):
        """Updates current bankroll and records high-water peak."""
        self.current_bankroll = current_val
        if current_val > self.peak_bankroll:
            self.peak_bankroll = current_val

    def get_current_drawdown(self) -> float:
        """Calculates current peak-to-trough drawdown."""
        if self.peak_bankroll <= 0:
            return 0.0
        return (self.peak_bankroll - self.current_bankroll) / self.peak_bankroll

    def calculate_drawdown_conditioned_kelly(self, raw_kelly_fraction: float) -> float:
        """
        Scales down Kelly fraction linearly as drawdown approaches max limit.
        """
        drawdown = self.get_current_drawdown()
        if drawdown >= self.max_drawdown_limit:
            return 0.0
            
        scale_factor = 1.0 - (drawdown / self.max_drawdown_limit)
        return float(max(0.0, raw_kelly_fraction * scale_factor))

    def estimate_cvar(self, simulated_pnl_returns: np.ndarray) -> float:
        """
        Estimates Conditional Value at Risk (Expected Shortfall) at confidence level.
        CVaR represents the average loss in the worst (1 - confidence_level) cases.
        """
        if len(simulated_pnl_returns) == 0:
            return 0.0
            
        # Find threshold VaR index
        alpha = 1.0 - self.cvar_confidence_level
        var_threshold = np.quantile(simulated_pnl_returns, alpha)
        
        # CVaR is the mean of returns below the VaR threshold
        worst_losses = simulated_pnl_returns[simulated_pnl_returns <= var_threshold]
        if len(worst_losses) == 0:
            return float(-var_threshold)
            
        return float(-np.mean(worst_losses))

    def evaluate_wager_risk(self, raw_kelly: float, simulated_pnl_returns: np.ndarray) -> Dict[str, Any]:
        """
        Enforces both CVaR capping and drawdown scaling on target Kelly.
        """
        # 1. Drawdown conditional adjustment
        adj_kelly = self.calculate_drawdown_conditioned_kelly(raw_kelly)
        
        # 2. CVaR estimation
        cvar_val = self.estimate_cvar(simulated_pnl_returns)
        cvar_flag = cvar_val > self.max_cvar_limit
        
        # 3. Apply capping if CVaR limit breached
        final_kelly = adj_kelly
        if cvar_flag:
            final_kelly = min(adj_kelly, adj_kelly * (self.max_cvar_limit / cvar_val))
            
        return {
            "raw_kelly": raw_kelly,
            "drawdown_adjusted_kelly": adj_kelly,
            "final_kelly": float(final_kelly),
            "estimated_cvar": cvar_val,
            "cvar_limit_breached": cvar_flag
        }
