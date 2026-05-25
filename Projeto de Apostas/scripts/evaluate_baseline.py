import logging
import os
import sys
from typing import Any, Dict

import numpy as np
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

# Append parent path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("evaluate_baseline")

def compute_metrics(y_true: np.ndarray, odds_home: np.ndarray, odds_away: np.ndarray) -> Dict[str, Any]:
    """
    Computes Brier Score, ROC-AUC, and Log-loss for the bookmaker baseline vs a naive model.
    """
    # 1. Implied probabilities
    raw_p_home = 1.0 / odds_home
    raw_p_away = 1.0 / odds_away
    
    # 2. Overround removal (normalization)
    p_home = raw_p_home / (raw_p_home + raw_p_away)
    p_away = raw_p_away / (raw_p_home + raw_p_away)
    
    # 3. Naive model (equal probability)
    naive_p = np.full_like(y_true, 0.5, dtype=float)
    
    # 4. Compute metrics
    # Note: Brier score loss expects target and predicted probability for the positive class (Home wins)
    brier_naive = brier_score_loss(y_true, naive_p)
    brier_bookie = brier_score_loss(y_true, p_home)
    
    auc_bookie = roc_auc_score(y_true, p_home)
    
    # Log loss metrics
    logloss_naive = log_loss(y_true, naive_p, labels=[0, 1])
    logloss_bookie = log_loss(y_true, p_home, labels=[0, 1])
    
    # Calculate overround percentage
    overrounds = (raw_p_home + raw_p_away) - 1.0
    mean_overround = np.mean(overrounds)
    
    report = {
        "mean_overround": mean_overround,
        "naive": {
            "brier": brier_naive,
            "logloss": logloss_naive
        },
        "bookmaker": {
            "brier": brier_bookie,
            "auc": auc_bookie,
            "logloss": logloss_bookie
        }
    }
    
    print("\n=== BOOKMAKER BASELINE EVALUATION REPORT ===")
    print(f"Number of Matches: {len(y_true)}")
    print(f"Average Market Overround: {mean_overround * 100:.2f}%")
    print("-" * 50)
    print(f"{'Metric':<18} | {'Naive (50/50)':<15} | {'Bookmaker Implied':<18}")
    print("-" * 50)
    print(f"{'Brier Score':<18} | {brier_naive:<15.4f} | {brier_bookie:<18.4f}")
    print(f"{'Log-Loss':<18} | {logloss_naive:<15.4f} | {logloss_bookie:<18.4f}")
    print(f"{'ROC-AUC':<18} | {'0.5000':<15} | {auc_bookie:<18.4f}")
    print("-" * 50)
    
    return report

if __name__ == "__main__":
    # Simulate historical matches for dry-run
    np.random.seed(42)
    n_matches = 500
    
    # Home team wins 58% of the time (historical NBA home-court advantage average)
    y_true = np.random.choice([0, 1], p=[0.42, 0.58], size=n_matches)
    
    # Set up some realistic bookie odds around home bias
    # If home wins, odds are usually shorter
    odds_home = []
    odds_away = []
    
    for y in y_true:
        # Generate odds with around 4% overround
        overround = 0.04
        if y == 1:
            # Home favorite
            p_h = np.random.uniform(0.55, 0.85)
        else:
            # Away favorite / closer match
            p_h = np.random.uniform(0.25, 0.55)
            
        p_a = 1.0 - p_h + overround
        
        odds_home.append(1.0 / p_h)
        odds_away.append(1.0 / p_a)
        
    compute_metrics(y_true, np.array(odds_home), np.array(odds_away))
