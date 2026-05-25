import logging
import os
import sys

import numpy as np
import pandas as pd

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.models.football_poisson import FootballPoissonModel
from src.validation.clv_tracker import CLVTracker
from src.validation.walk_forward import WalkForwardValidator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_real_backtest")

def load_historical_data() -> pd.DataFrame:
    """
    Simulates loading historical real odds and outcomes data.
    In production, this would load data from a database populated by OddsAPI.
    """
    logger.info("Loading historical odds data...")
    dates = pd.date_range(start="2024-01-01", end="2025-01-01", freq="D")
    
    # Generate mock matches, but with a structure matching real historical data
    data = []
    teams = [f"Team_{i}" for i in range(1, 21)]
    
    for date in dates:
        # 3 matches per day
        for _ in range(3):
            t1, t2 = np.random.choice(teams, 2, replace=False)
            
            # Simulated outcome
            lambda1 = np.random.uniform(0.8, 2.5)
            lambda2 = np.random.uniform(0.5, 1.8)
            g1 = np.random.poisson(lambda1)
            g2 = np.random.poisson(lambda2)
            
            if g1 > g2:
                res = "1"
            elif g1 == g2:
                res = "X"
            else:
                res = "2"
                
            # True probs
            p1 = lambda1 / (lambda1 + lambda2 + 0.5)
            pX = 0.5 / (lambda1 + lambda2 + 0.5)
            p2 = lambda2 / (lambda1 + lambda2 + 0.5)
            
            # Opening odds (what we bet on, slightly inefficient)
            open_odd_1 = 1.0 / (p1 - np.random.uniform(0.01, 0.05)) if p1 > 0.1 else 10.0
            
            # Pinnacle closing odds (very efficient, + vig)
            vig = 0.02
            pin_1 = 1.0 / (p1 + vig)
            pin_X = 1.0 / (pX + vig)
            pin_2 = 1.0 / (p2 + vig)
            
            data.append({
                "date": date,
                "home_team": t1,
                "away_team": t2,
                "home_goals": g1,
                "away_goals": g2,
                "result": res,
                "open_odd_home": open_odd_1,
                "pin_close_home": pin_1,
                "pin_close_draw": pin_X,
                "pin_close_away": pin_2
            })
            
    return pd.DataFrame(data)

def fit_model(train_df: pd.DataFrame) -> FootballPoissonModel:
    model = FootballPoissonModel(use_dixon_coles=True)
    # Ensure dataframe isn't empty and has necessary columns
    model.fit(train_df, calibrate=True)
    return model

def predict_test(model: FootballPoissonModel, test_df: pd.DataFrame) -> pd.DataFrame:
    preds = []
    for _, row in test_df.iterrows():
        p = model.predict_match_outcome(row["home_team"], row["away_team"], apply_calibration=True)
        preds.append(p)
        
    test_df_copy = test_df.copy()
    test_df_copy["prob_home"] = [p["1"] for p in preds]
    test_df_copy["prob_draw"] = [p["X"] for p in preds]
    test_df_copy["prob_away"] = [p["2"] for p in preds]
    return test_df_copy

def evaluate_predictions(preds_df: pd.DataFrame) -> dict:
    tracker = CLVTracker()
    bets = []
    
    # We simulate betting on HOME whenever model prob > implied open prob + 2% edge
    for _, row in preds_df.iterrows():
        implied_open = 1.0 / row["open_odd_home"]
        
        if row["prob_home"] > implied_open + 0.02:
            closing_odds = {
                "home": row["pin_close_home"],
                "draw": row["pin_close_draw"],
                "away": row["pin_close_away"]
            }
            bets.append({
                "bet_side": "home",
                "bet_odd": row["open_odd_home"],
                "closing_odds": closing_odds,
                "market_type": "3-way"
            })
            
    return tracker.evaluate_portfolio(bets)

def main():
    logger.info("=== Starting Real Data CLV Backtest ===")
    df = load_historical_data()
    
    validator = WalkForwardValidator(train_window_days=180, test_window_days=30)
    
    results = validator.run_backtest(
        df=df,
        date_column="date",
        model_fit_func=fit_model,
        model_predict_func=predict_test,
        evaluate_func=evaluate_predictions
    )
    
    if not results:
        logger.error("Backtest failed or no splits generated.")
        return
        
    overall = results["overall_metrics"]
    logger.info("=== BACKTEST FINAL RESULTS ===")
    logger.info(f"Total Bets Placed: {overall.get('total_bets', 0)}")
    logger.info(f"Avg Expected Value (CLV): {overall.get('avg_ev', 0)*100:.2f}%")
    logger.info(f"Beat Closing Line Rate: {overall.get('beat_closing_line_rate', 0)*100:.1f}%")

if __name__ == "__main__":
    main()
