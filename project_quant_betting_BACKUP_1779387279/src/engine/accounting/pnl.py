"""
P&L Analysis Module.
Calculates deep performance metrics like Sharpe Ratio, Sortino Ratio, and Max Drawdown.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List

class PnLAnalyzer:
    """Advanced P&L and Risk Metrics analyzer."""
    
    def __init__(self, risk_free_rate: float = 0.0):
        self.rf = risk_free_rate
        
    def analyze_returns(self, daily_returns: pd.Series) -> Dict[str, float]:
        """Calculate standard risk-adjusted performance metrics."""
        if len(daily_returns) < 2:
            return {"sharpe_ratio": 0.0, "sortino_ratio": 0.0, "max_drawdown": 0.0}
            
        # Annualization factor (assuming 365 betting days a year)
        ann_factor = np.sqrt(365)
        
        # 1. Sharpe Ratio
        mean_ret = daily_returns.mean()
        std_ret = daily_returns.std()
        
        if std_ret > 0:
            sharpe = (mean_ret - self.rf) / std_ret * ann_factor
        else:
            sharpe = 0.0
            
        # 2. Sortino Ratio
        downside_returns = daily_returns[daily_returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
        
        if downside_std > 0:
            sortino = (mean_ret - self.rf) / downside_std * ann_factor
        else:
            sortino = float('inf') if mean_ret > 0 else 0.0
            
        # 3. Maximum Drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        
        return {
            "sharpe_ratio": float(sharpe),
            "sortino_ratio": float(sortino),
            "max_drawdown_pct": float(max_drawdown * 100)
        }
