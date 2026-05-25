import logging
import time
from typing import Any, Dict

logger = logging.getLogger("latency")

class LatencyBudgetTracker:
    """
    Measures processing and transmission latency across the pipeline steps.
    """
    def __init__(self, budget_ms: float = 200.0):
        self.budget_ms = budget_ms

    def measure_latency(self, start_time: float) -> Dict[str, Any]:
        """
        Calculates execution latency and warns if budget was violated.
        """
        elapsed_ms = (time.time() - start_time) * 1000.0
        exceeded = elapsed_ms > self.budget_ms
        
        if exceeded:
            logger.warning(f"LATENCY VIOLATION: Execution took {elapsed_ms:.2f}ms (Budget: {self.budget_ms}ms)")
            
        return {
            "elapsed_ms": elapsed_ms,
            "budget_ms": self.budget_ms,
            "budget_exceeded": exceeded
        }


class OddMovementAnalyzer:
    """
    Correlates latency delays with loss of Expected Value (EV) due to price movements.
    """
    def __init__(self):
        pass

    def estimate_ev_decay(
        self, 
        predicted_prob: float, 
        initial_odds: float, 
        final_odds: float,
        latency_ms: float
    ) -> Dict[str, float]:
        """
        Compares expected value before and after latency delay.
        """
        initial_ev = (predicted_prob * initial_odds) - 1.0
        final_ev = (predicted_prob * final_odds) - 1.0
        
        ev_loss = initial_ev - final_ev
        
        # Calculate decay rate per 100ms
        decay_rate_100ms = (ev_loss / (latency_ms / 100.0)) if latency_ms > 0 else 0.0
        
        return {
            "initial_ev": float(initial_ev),
            "final_ev": float(final_ev),
            "ev_lost": float(ev_loss),
            "decay_rate_per_100ms": float(decay_rate_100ms)
        }
