import logging
from typing import Dict

logger = logging.getLogger("governance")

class ModelGovernance:
    """
    Implements validation gates and promotion workflows for quantitative models.
    """
    def __init__(self, ece_threshold: float = 0.05, max_drawdown_limit: float = 20.0):
        self.ece_threshold = ece_threshold
        self.max_drawdown_limit = max_drawdown_limit

    def validation_gate(self, challenger_metrics: Dict[str, float], champion_metrics: Dict[str, float]) -> bool:
        """
        Evaluates if a challenger model is qualified to replace the current champion.
        
        Mandatory metrics check:
        - Brier Score must be lower (better) than or equal to the champion.
        - Expected Calibration Error (ECE) must be below threshold.
        - Sharpe Ratio must be greater than or equal to the champion.
        - Max Drawdown must be below maximum drawdown limit.
        """
        logger.info("Evaluating Challenger model through Validation Gates...")
        
        # 1. Calibraton Gate
        challenger_ece = challenger_metrics.get("ece", 1.0)
        if challenger_ece > self.ece_threshold:
            logger.warning(f"Challenger rejected: ECE {challenger_ece:.4f} exceeds threshold {self.ece_threshold:.4f}")
            return False

        # 2. Risk Gate (Max Drawdown)
        challenger_dd = challenger_metrics.get("max_drawdown", 100.0)
        if challenger_dd > self.max_drawdown_limit:
            logger.warning(f"Challenger rejected: Drawdown {challenger_dd:.2f}% exceeds safety limit {self.max_drawdown_limit}%")
            return False

        # 3. Accuracy Gate (Brier Score comparison)
        challenger_brier = challenger_metrics.get("brier", 1.0)
        champion_brier = champion_metrics.get("brier", 1.0)
        if challenger_brier > champion_brier:
            logger.warning(f"Challenger rejected: Brier Score {challenger_brier:.4f} is worse than Champion Brier {champion_brier:.4f}")
            return False

        # 4. Return/Sharpe Gate
        challenger_sharpe = challenger_metrics.get("sharpe", -1.0)
        champion_sharpe = champion_metrics.get("sharpe", -1.0)
        if challenger_sharpe < champion_sharpe:
            logger.warning(f"Challenger rejected: Sharpe Ratio {challenger_sharpe:.2f} is lower than Champion Sharpe {champion_sharpe:.2f}")
            return False

        logger.info("Challenger PASSED all validation gates! Promotion approved.")
        return True
