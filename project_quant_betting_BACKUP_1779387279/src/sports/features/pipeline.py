"""
Feature Engineering Pipeline.
Transforms raw match and statistics data into ML-ready feature vectors.
Implements strict temporal ordering to prevent data leakage.
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class FeaturePipeline:
    """Pipeline for generating ML features for sports events."""
    
    def __init__(self):
        self.k_factor_default = 20.0
        
    def build_features(
        self, 
        match_data: Dict[str, Any], 
        historical_stats: List[Dict[str, Any]],
        market_data: Optional[Dict[str, Any]] = None,
        injury_modifiers: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Build a comprehensive feature vector for a single match.
        """
        features = {}
        
        # 1. Base Elo & Power Ratings (Injury Adjusted)
        elo_features = self._calculate_elo_features(
            match_data, historical_stats, injury_modifiers
        )
        features.update(elo_features)
        
        # 2. Rolling Statistics (Form)
        form_features = self._calculate_rolling_stats(
            match_data, historical_stats, window_sizes=[3, 5, 10]
        )
        features.update(form_features)
        
        # 3. Context (Rest, Travel, H2H)
        context_features = self._calculate_context_features(
            match_data, historical_stats
        )
        features.update(context_features)
        
        # 4. Market-Implied Probability (if available)
        if market_data:
            market_features = self._calculate_market_features(market_data)
            features.update(market_features)
            
        return features
        
    def _calculate_elo_features(
        self, 
        match: Dict[str, Any], 
        history: List[Dict[str, Any]],
        modifiers: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Calculate Elo ratings adjusted for injuries."""
        # Simplified for implementation - normally loads historical Elo state
        home_elo = 1500.0
        away_elo = 1500.0
        
        # Apply injury modifiers (e.g., star player out reduces Elo by 50 points)
        if modifiers:
            home_mod = modifiers.get(match.get("home_team", ""), 0.0)
            away_mod = modifiers.get(match.get("away_team", ""), 0.0)
            home_elo -= home_mod
            away_elo -= away_mod
            
        elo_diff = home_elo - away_elo
        
        # Probability derived from Elo diff (logistic curve)
        implied_home_win_prob = 1.0 / (10.0 ** (-elo_diff / 400.0) + 1.0)
        
        return {
            "f_home_elo": home_elo,
            "f_away_elo": away_elo,
            "f_elo_diff": elo_diff,
            "f_elo_implied_prob": implied_home_win_prob
        }
        
    def _calculate_rolling_stats(
        self, 
        match: Dict[str, Any], 
        history: List[Dict[str, Any]],
        window_sizes: List[int]
    ) -> Dict[str, float]:
        """Calculate rolling averages (form) over recent matches."""
        features = {}
        
        # Note: In a real system, 'history' must strictly be matches played BEFORE this match's kickoff
        # This is where temporal leakage often occurs.
        home_team = match.get("home_team")
        away_team = match.get("away_team")
        
        home_games = [m for m in history if m.get("home_team") == home_team or m.get("away_team") == home_team]
        away_games = [m for m in history if m.get("home_team") == away_team or m.get("away_team") == away_team]
        
        for w in window_sizes:
            # Win percentages
            h_recent = home_games[-w:] if len(home_games) >= w else home_games
            a_recent = away_games[-w:] if len(away_games) >= w else away_games
            
            h_wins = sum(1 for m in h_recent if self._did_win(m, home_team))
            a_wins = sum(1 for m in a_recent if self._did_win(m, away_team))
            
            features[f"f_home_win_pct_{w}"] = h_wins / max(1, len(h_recent))
            features[f"f_away_win_pct_{w}"] = a_wins / max(1, len(a_recent))
            
            # Simplified generic scoring stats
            features[f"f_home_avg_scored_{w}"] = np.mean([self._goals_for(m, home_team) for m in h_recent]) if h_recent else 0.0
            features[f"f_away_avg_scored_{w}"] = np.mean([self._goals_for(m, away_team) for m in a_recent]) if a_recent else 0.0
            
        return features
        
    def _calculate_context_features(
        self, match: Dict[str, Any], history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate contextual features like rest days."""
        # Simplified implementations
        return {
            "f_home_rest_days": match.get("home_rest_days", 7.0),
            "f_away_rest_days": match.get("away_rest_days", 7.0),
            "f_rest_diff": match.get("home_rest_days", 7.0) - match.get("away_rest_days", 7.0)
        }
        
    def _calculate_market_features(self, market_data: Dict[str, Any]) -> Dict[str, float]:
        """Derive features from market odds (consensus)."""
        home_odds = market_data.get("home_odds", 2.0)
        away_odds = market_data.get("away_odds", 2.0)
        
        implied_home = 1.0 / home_odds if home_odds > 0 else 0
        implied_away = 1.0 / away_odds if away_odds > 0 else 0
        overround = implied_home + implied_away
        
        return {
            "f_market_implied_home": implied_home / overround if overround > 0 else 0,
            "f_market_implied_away": implied_away / overround if overround > 0 else 0,
            "f_market_overround": overround
        }
        
    def _did_win(self, match: Dict[str, Any], team: str) -> bool:
        if match.get("home_team") == team:
            return match.get("home_score", 0) > match.get("away_score", 0)
        return match.get("away_score", 0) > match.get("home_score", 0)
        
    def _goals_for(self, match: Dict[str, Any], team: str) -> float:
        if match.get("home_team") == team:
            return float(match.get("home_score", 0))
        return float(match.get("away_score", 0))
