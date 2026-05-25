from typing import List

import numpy as np


class ConditionalRiskEngine:
    """
    Computes advanced tail-risk metrics like Conditional Drawdown
    and Block Bootstrap Ruin under temporal correlations.
    """
    def __init__(self, n_bootstrap_paths: int = 2000):
        self.n_bootstrap_paths = n_bootstrap_paths

    def calculate_conditional_drawdown(
        self, 
        pnl_history: np.ndarray, 
        regime_labels: List[str], 
        target_regime: str
    ) -> float:
        """
        Computes the maximum drawdown experienced strictly during a target regime
        (e.g., when the model is in playoff regime or high volatility regime).
        """
        pnl = np.array(pnl_history)
        regimes = np.array(regime_labels)
        
        if len(pnl) == 0 or len(regimes) != len(pnl):
            return 0.0
            
        # Filter PnL to only target regime events
        regime_pnl = pnl[regimes == target_regime]
        if len(regime_pnl) == 0:
            return 0.0
            
        # Reconstruct bankroll path for this regime
        bankroll_path = 1000.0 + np.cumsum(regime_pnl)
        peaks = np.maximum.accumulate(bankroll_path)
        peaks = np.where(peaks == 0, 1.0, peaks)
        
        drawdowns = (peaks - bankroll_path) / peaks
        return float(np.max(drawdowns) * 100.0) # return percentage

    def bootstrap_ruin_probability(
        self, 
        returns: np.ndarray, 
        block_size: int = 5, 
        initial_bankroll: float = 1000.0, 
        num_bets: int = 100
    ) -> float:
        """
        Performs Moving Block Bootstrap (MBB) resampling to maintain temporal correlation structure,
        and computes the empirical probability of ruin (bankroll falling below 50%).
        """
        ret = np.array(returns)
        n = len(ret)
        
        if n < block_size or n == 0:
            return 0.0
            
        ruin_count = 0
        
        for _ in range(self.n_bootstrap_paths):
            # Construct a bootstrap sample of length num_bets
            path_returns = []
            while len(path_returns) < num_bets:
                # Randomly select a start index for a block
                start_idx = np.random.randint(0, n - block_size + 1)
                block = ret[start_idx : start_idx + block_size]
                path_returns.extend(block)
                
            path_returns = np.array(path_returns[:num_bets])
            
            # Simulate bankroll path
            bankroll_path = initial_bankroll + np.cumsum(path_returns)
            
            if np.any(bankroll_path < (initial_bankroll * 0.5)):
                ruin_count += 1
                
        return float(ruin_count / self.n_bootstrap_paths)
