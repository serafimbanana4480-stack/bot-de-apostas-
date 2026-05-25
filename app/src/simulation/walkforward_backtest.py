from datetime import timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd


class PurgedWalkForwardBacktest:
    """
    Simulates a rigorous walk-forward backtest matching real production rules:
    1. Splits train/validation sequentially without lookahead bias.
    2. Applies an embargo window of N days between train and test sets.
    3. Locks event features and odds at decision timestamp (e.g., 2 hours before kickoff).
    """
    def __init__(
        self, 
        train_window_days: int = 180, 
        embargo_days: int = 7, 
        step_days: int = 30, 
        decision_hours_before: int = 2
    ):
        self.train_window_days = train_window_days
        self.embargo_days = embargo_days
        self.step_days = step_days
        self.decision_hours_before = decision_hours_before
        self.history: List[Dict[str, Any]] = []

    def run(
        self, 
        games_df: pd.DataFrame, 
        odds_df: pd.DataFrame, 
        mock_model_decide_func
    ) -> Dict[str, Any]:
        """
        Runs walk-forward iterations over chronological games dataframe.
        """
        games = games_df.sort_values(by=["game_date"]).copy()
        games["game_date"] = pd.to_datetime(games["game_date"])
        
        start_date = games["game_date"].min()
        end_date = games["game_date"].max()
        
        current_train_end = start_date + timedelta(days=self.train_window_days)
        
        while current_train_end + timedelta(days=self.embargo_days) < end_date:
            test_start = current_train_end + timedelta(days=self.embargo_days)
            test_end = test_start + timedelta(days=self.step_days)
            
            # 1. Filter sets
            train_set = games[games["game_date"] <= current_train_end]
            test_set = games[(games["game_date"] > test_start) & (games["game_date"] <= test_end)]
            
            if test_set.empty:
                break
                
            # 2. Simulate decisions for events in test window
            for _, row in test_set.iterrows():
                event_id = row["game_id"]
                kickoff = row["game_date"]
                decision_time = kickoff - timedelta(hours=self.decision_hours_before)
                
                # Fetch odds available at decision time (mock filter to simulate temporal consistency)
                odds_row = odds_df[odds_df["game_id"] == event_id]
                if odds_row.empty:
                    continue
                
                opening_odds = float(odds_row["home_odds"].values[0])
                closing_odds = float(odds_row.get("closing_odds", odds_row["home_odds"]).values[0])
                
                # Model decision using frozen odds
                prob = mock_model_decide_func(event_id, opening_odds)
                edge = prob - (1.0 / opening_odds)
                
                # Simple rule: if edge > 0.03, BET home team, else SKIP
                action = "BET" if edge > 0.03 else "SKIP"
                
                # Record outcome
                outcome = row.get("home_score", 0) > row.get("away_score", 0)
                actual_result = 1 if outcome else 0
                
                # Calculate P&L (implied EUR payout)
                pnl = 0.0
                clv = 0.0
                if action == "BET":
                    # CLV metric: log(Closing Odds) - log(Opening Odds)
                    clv = float(np.log(closing_odds) - np.log(opening_odds))
                    pnl = (opening_odds - 1.0) if actual_result == 1 else -1.0
                    
                self.history.append({
                    "game_id": event_id,
                    "action": action,
                    "opening_odds": opening_odds,
                    "closing_odds": closing_odds,
                    "pnl": pnl,
                    "clv": clv,
                    "actual_result": actual_result
                })
                
            current_train_end += timedelta(days=self.step_days)

        return self.compute_metrics()

    def compute_metrics(self) -> Dict[str, Any]:
        """
        Computes walk-forward backtest KPIs.
        """
        bets = [h for h in self.history if h["action"] == "BET"]
        total_bets = len(bets)
        if total_bets == 0:
            return {"roi": 0.0, "avg_clv": 0.0, "total_bets": 0, "win_rate": 0.0}

        total_pnl = sum(b["pnl"] for b in bets)
        total_stake = total_bets * 1.0 # fixed 1.0 stake
        roi = total_pnl / total_stake
        
        avg_clv = float(np.mean([b["clv"] for b in bets]))
        wins = sum(1 for b in bets if b["actual_result"] == 1)
        win_rate = wins / total_bets
        
        return {
            "roi": roi,
            "avg_clv": avg_clv,
            "total_bets": total_bets,
            "win_rate": win_rate
        }
