import json
import logging
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.stats import poisson

mlflow = None
try:
    import mlflow as _mlflow
    mlflow = _mlflow
except ImportError:
    pass

from sklearn.isotonic import IsotonicRegression
from src.ml.serialization import isotonic_from_dict, isotonic_to_dict
from src.validation.splits import temporal_oof_split


class FootballPoissonModel:
    """
    Bivariate Poisson Model for Football.
    Estimates the attack and defense strength of teams to predict goal distributions.
    This serves as a strong professional baseline before adding ML models.
    """
    def __init__(self, use_dixon_coles: bool = True, use_context: bool = True, reg_lambda: float = 0.1):
        self.logger = logging.getLogger(__name__)
        self.attack_strengths = {}
        self.defense_strengths = {}
        self.home_advantage = 1.2
        self.home_advantage_by_league = {}
        self.global_avg_goals = 1.3
        self.use_dixon_coles = use_dixon_coles
        self.use_context = use_context
        self.rho = -0.05  # Dixon-Coles correlation parameter (typically negative)
        self.reg_lambda = reg_lambda  # L2 regularization for attack/defense strengths

        # Calibration models
        self.calibrator_1 = IsotonicRegression(out_of_bounds='clip')
        self.calibrator_X = IsotonicRegression(out_of_bounds='clip')
        self.calibrator_2 = IsotonicRegression(out_of_bounds='clip')
        self.odds_bin_calibrators: Dict[str, Dict[str, IsotonicRegression]] = {
            "1": {},
            "X": {},
            "2": {},
        }
        self.is_calibrated = False

        # Incremental training state
        self._training_match_count = 0
        self._league_match_counts: Dict[str, int] = {}

        # Match history for form/H2H/rest calculations
        self._match_history: List[Dict[str, Any]] = []

    def fit(self, df_matches: pd.DataFrame, calibrate: bool = False):
        """
        Fits the Poisson model to historical match data to derive attack/defense parameters.
        Using a simplified average-based approach for the proof of concept.
        """
        self.logger.info("Fitting Poisson model to football data...")
        if df_matches.empty:
            return
            
        _mlflow_active = False
        _mlflow_ctx = nullcontext()
        if mlflow:
            try:
                _mlflow_ctx = mlflow.start_run(run_name="football_poisson_fit", nested=True)
                _mlflow_active = True
            except Exception:
                pass
        with _mlflow_ctx:
            home_goals_avg = max(df_matches['home_goals'].mean(), 0.01)
            away_goals_avg = max(df_matches['away_goals'].mean(), 0.01)
            self.global_avg_goals = (home_goals_avg + away_goals_avg) / 2
            self.home_advantage = home_goals_avg / away_goals_avg if away_goals_avg > 0 else 1.2
            
            # Dynamic Home Advantage by League
            league_col = 'league' if 'league' in df_matches.columns else ('competition' if 'competition' in df_matches.columns else None)
            if league_col:
                self.home_advantage_by_league = {}
                for league, group in df_matches.groupby(league_col):
                    home_goals_avg_l = group['home_goals'].mean()
                    away_goals_avg_l = group['away_goals'].mean()
                    self.home_advantage_by_league[league] = home_goals_avg_l / away_goals_avg_l if away_goals_avg_l > 0 else self.home_advantage
            
            teams = pd.concat([df_matches['home_team'], df_matches['away_team']]).unique()
            
            for team in teams:
                # Attack strength
                team_home_goals = df_matches[df_matches['home_team'] == team]['home_goals'].mean()
                team_away_goals = df_matches[df_matches['away_team'] == team]['away_goals'].mean()
                
                # Defense strength (goals conceded)
                team_home_conceded = df_matches[df_matches['home_team'] == team]['away_goals'].mean()
                team_away_conceded = df_matches[df_matches['away_team'] == team]['home_goals'].mean()
                
                # Safe defaults if not enough data
                if pd.isna(team_home_goals): team_home_goals = home_goals_avg
                if pd.isna(team_away_goals): team_away_goals = away_goals_avg
                if pd.isna(team_home_conceded): team_home_conceded = away_goals_avg
                if pd.isna(team_away_conceded): team_away_conceded = home_goals_avg
                
                raw_attack = ((team_home_goals / home_goals_avg) + (team_away_goals / away_goals_avg)) / 2
                raw_defense = ((team_home_conceded / away_goals_avg) + (team_away_conceded / home_goals_avg)) / 2
                # Shrink towards 1.0 (league average) to prevent extreme overfitting on small samples
                self.attack_strengths[team] = 1.0 + (raw_attack - 1.0) * (1.0 - self.reg_lambda)
                self.defense_strengths[team] = 1.0 + (raw_defense - 1.0) * (1.0 - self.reg_lambda)
                
            if _mlflow_active:
                try:
                    mlflow.log_metric("global_avg_goals", float(self.global_avg_goals))
                    mlflow.log_metric("home_advantage", float(self.home_advantage))
                    mlflow.log_param("num_teams", len(teams))
                    mlflow.log_param("num_matches", len(df_matches))
                    mlflow.log_param("use_dixon_coles", self.use_dixon_coles)
                except Exception:
                    pass

            # Track training counts for incremental updates
            self._training_match_count += len(df_matches)
            if 'league' in df_matches.columns:
                for league, group in df_matches.groupby('league'):
                    self._league_match_counts[league] = self._league_match_counts.get(league, 0) + len(group)

            # Store match history for form/H2H calculations
            for _, row in df_matches.iterrows():
                self._match_history.append({
                    "date": row.get("date"),
                    "home_team": row["home_team"],
                    "away_team": row["away_team"],
                    "home_goals": row["home_goals"],
                    "away_goals": row["away_goals"],
                    "result": row.get("result", "X"),
                })
            # Keep only last 1000 matches for memory efficiency
            if len(self._match_history) > 1000:
                self._match_history = self._match_history[-1000:]

            # Support both 'result' and 'actual_outcome' column names
            outcome_col = 'result' if 'result' in df_matches.columns else (
                'actual_outcome' if 'actual_outcome' in df_matches.columns else None
            )
            if calibrate and outcome_col:
                self._calibrate_model(df_matches, outcome_col=outcome_col)

    @staticmethod
    def _odds_bin_label(odd: Optional[float]) -> Optional[str]:
        if odd is None or pd.isna(odd):
            return None
        odd = float(odd)
        if odd < 1.5:
            return "1.00-1.50"
        if odd < 2.0:
            return "1.50-2.00"
        if odd < 3.0:
            return "2.00-3.00"
        if odd < 5.0:
            return "3.00-5.00"
        return "5.00+"

    @staticmethod
    def _odds_cols_for_side(side: str) -> List[str]:
        if side == "1":
            return ["open_odd_home", "odd_1"]
        if side == "X":
            return ["open_odd_draw", "odd_X"]
        return ["open_odd_away", "odd_2"]

    def _calibrate_model(self, df: pd.DataFrame, outcome_col: str = "result"):
        """
        Fits Isotonic Regression calibrators using 3-fold Out-of-Fold cross-calibration.
        This removes calibration leakage by ensuring calibrators are fitted on predictions
        from models that did not see the target records during strength fitting.
        """
        self.logger.info("Calibrating probabilities using temporal Out-of-Fold cross-calibration...")
        
        min_matches = 3 * 3  # n_splits * min_per_fold
        if len(df) < min_matches:
            self.logger.warning("Not enough matches (%d < %d) to perform temporal OOF cross-calibration. Skipping calibration.", len(df), min_matches)
            return

        # Reset and prepare OOF arrays
        oof_preds_1 = np.zeros(len(df))
        oof_preds_X = np.zeros(len(df))
        oof_preds_2 = np.zeros(len(df))
        
        y_1 = np.zeros(len(df))
        y_X = np.zeros(len(df))
        y_2 = np.zeros(len(df))
        bin_labels = {
            "1": [None] * len(df),
            "X": [None] * len(df),
            "2": [None] * len(df),
        }
        
        # Create targets
        for idx, (_, row) in enumerate(df.iterrows()):
            y_1[idx] = 1 if row[outcome_col] == '1' else 0
            y_X[idx] = 1 if row[outcome_col] == 'X' else 0
            y_2[idx] = 1 if row[outcome_col] == '2' else 0
            for side in ("1", "X", "2"):
                for col in self._odds_cols_for_side(side):
                    if col in df.columns:
                        bin_labels[side][idx] = self._odds_bin_label(row.get(col))
                        if bin_labels[side][idx]:
                            break
            
        oof_splits = temporal_oof_split(df, n_splits=3, embargo_days=2, time_col=None)
        
        for train_idx, val_idx in oof_splits:
            df_train = df.iloc[train_idx]
            
            # Fit temporary model on df_train
            temp_model = FootballPoissonModel(use_dixon_coles=self.use_dixon_coles)
            temp_model.fit(df_train, calibrate=False)
            
            # Predict validation set matches (without calibration)
            for val_i in val_idx:
                row = df.iloc[val_i]
                league_val = row.get('league', row.get('competition', None))
                prob = temp_model.predict_match_outcome(
                    row['home_team'], 
                    row['away_team'], 
                    league=league_val,
                    apply_calibration=False
                )
                oof_preds_1[val_i] = prob['1']
                oof_preds_X[val_i] = prob['X']
                oof_preds_2[val_i] = prob['2']
                
        # Fit global calibrators on the Out-of-Fold predictions
        self.calibrator_1.fit(oof_preds_1, y_1)
        self.calibrator_X.fit(oof_preds_X, y_X)
        self.calibrator_2.fit(oof_preds_2, y_2)

        # Fit per-odds-bin calibrators so longshots can be adjusted separately.
        self.odds_bin_calibrators = {"1": {}, "X": {}, "2": {}}
        for side, preds, targets in (
            ("1", oof_preds_1, y_1),
            ("X", oof_preds_X, y_X),
            ("2", oof_preds_2, y_2),
        ):
            side_bins = bin_labels[side]
            for bin_label in sorted({b for b in side_bins if b}):
                idxs = [i for i, b in enumerate(side_bins) if b == bin_label]
                if len(idxs) < 20:
                    continue
                calibrator = IsotonicRegression(out_of_bounds='clip')
                calibrator.fit(preds[idxs], targets[idxs])
                self.odds_bin_calibrators[side][bin_label] = calibrator
        self.is_calibrated = True

    def update(
        self,
        df_new: pd.DataFrame,
        alpha: Optional[float] = None,
        calibrate: bool = True,
        max_calibration_window: int = 1000,
    ) -> Dict[str, float]:
        """
        Incrementally update model with new match data using exponential moving average (EMA).

        Instead of retraining from scratch, this method:
        1. Computes team strengths from the NEW data only
        2. Blends them with existing strengths via EMA:  s_new = alpha*s_new + (1-alpha)*s_old
        3. Teams not seen in new data keep their old strength
        4. Recalibrates using a sliding window of recent matches

        Args:
            df_new: New match records (same schema as fit)
            alpha: EMA learning rate (0=keep old, 1=overwrite with new).
                   If None, auto-computed as n_new / (n_new + n_old)
            calibrate: Whether to recalibrate probabilities
            max_calibration_window: Max matches used for calibration window

        Returns:
            Dict with update statistics (alpha_used, teams_updated, new_teams, etc.)
        """
        if df_new.empty:
            return {"updated": False, "reason": "empty_data"}

        n_new = len(df_new)
        n_old = max(self._training_match_count, 1)
        alpha_used = alpha if alpha is not None else min(n_new / (n_new + n_old), 0.5)
        alpha_used = float(np.clip(alpha_used, 0.01, 0.8))

        # Compute new data statistics
        home_goals_avg_new = df_new['home_goals'].mean()
        away_goals_avg_new = df_new['away_goals'].mean()
        global_avg_new = (home_goals_avg_new + away_goals_avg_new) / 2
        home_adv_new = (
            home_goals_avg_new / away_goals_avg_new
            if away_goals_avg_new > 0 else self.home_advantage
        )

        # EMA update of global parameters
        self.global_avg_goals = alpha_used * global_avg_new + (1 - alpha_used) * self.global_avg_goals
        self.home_advantage = alpha_used * home_adv_new + (1 - alpha_used) * self.home_advantage

        # Update league-specific home advantage
        league_col = 'league' if 'league' in df_new.columns else ('competition' if 'competition' in df_new.columns else None)
        if league_col:
            for league, group in df_new.groupby(league_col):
                hgn = group['home_goals'].mean()
                agn = group['away_goals'].mean()
                ha_new = hgn / agn if agn > 0 else self.home_advantage
                old_ha = self.home_advantage_by_league.get(league, self.home_advantage)
                # Weight by match count
                league_n_old = self._league_match_counts.get(league, 0)
                league_n_new = len(group)
                league_alpha = min(league_n_new / (league_n_new + max(league_n_old, 1)), 0.5)
                self.home_advantage_by_league[league] = league_alpha * ha_new + (1 - league_alpha) * old_ha
                self._league_match_counts[league] = league_n_old + league_n_new

        # Compute team strengths from NEW data only
        teams_new = pd.concat([df_new['home_team'], df_new['away_team']]).unique()
        new_attack = {}
        new_defense = {}
        for team in teams_new:
            team_home_goals = df_new[df_new['home_team'] == team]['home_goals'].mean()
            team_away_goals = df_new[df_new['away_team'] == team]['away_goals'].mean()
            team_home_conceded = df_new[df_new['home_team'] == team]['away_goals'].mean()
            team_away_conceded = df_new[df_new['away_team'] == team]['home_goals'].mean()

            if pd.isna(team_home_goals): team_home_goals = home_goals_avg_new
            if pd.isna(team_away_goals): team_away_goals = away_goals_avg_new
            if pd.isna(team_home_conceded): team_home_conceded = away_goals_avg_new
            if pd.isna(team_away_conceded): team_away_conceded = home_goals_avg_new

            new_attack[team] = ((team_home_goals / home_goals_avg_new) + (team_away_goals / away_goals_avg_new)) / 2
            new_defense[team] = ((team_home_conceded / away_goals_avg_new) + (team_away_conceded / home_goals_avg_new)) / 2

        # EMA blend with existing strengths
        teams_updated = 0
        new_teams = 0
        for team in teams_new:
            is_new_team = team not in self.attack_strengths and team not in self.defense_strengths
            old_atk = self.attack_strengths.get(team, 1.0)
            old_def = self.defense_strengths.get(team, 1.0)
            self.attack_strengths[team] = alpha_used * new_attack[team] + (1 - alpha_used) * old_atk
            self.defense_strengths[team] = alpha_used * new_defense[team] + (1 - alpha_used) * old_def
            if is_new_team:
                new_teams += 1
            else:
                teams_updated += 1

        # Track training count
        self._training_match_count += n_new

        # Recalibrate with sliding window (recent matches only)
        if calibrate and 'result' in df_new.columns:
            # Rebuild a recent-history DataFrame for calibration
            # Since we only have new data here, we do OOF on new data only.
            # In production, you'd keep a replay buffer of recent matches.
            if len(df_new) >= 30:
                self._calibrate_model(df_new)
            else:
                self.logger.info("Skipping recalibration: only %d new matches (min 30)", len(df_new))

        return {
            "updated": True,
            "alpha_used": round(alpha_used, 4),
            "teams_updated": teams_updated,
            "new_teams": new_teams,
            "matches_added": n_new,
            "total_matches": self._training_match_count,
        }

    def _dixon_coles_correction(self, h: int, a: int, lambda_home: float, lambda_away: float) -> float:
        """Applies the Dixon-Coles adjustment for low-scoring match dependence."""
        if h == 0 and a == 0:
            return 1.0 - (lambda_home * lambda_away * self.rho)
        elif h == 0 and a == 1:
            return 1.0 + (lambda_home * self.rho)
        elif h == 1 and a == 0:
            return 1.0 + (lambda_away * self.rho)
        elif h == 1 and a == 1:
            return 1.0 - self.rho
        return 1.0

    # --- Contextual features (form, H2H, rest) ---
    def _get_team_form(self, team: str, last_n: int = 5) -> float:
        """Returns a form multiplier based on last N matches. 1.0 = neutral."""
        if not self._match_history:
            return 1.0
        team_matches = [
            m for m in self._match_history[-200:]  # look at last 200 matches max
            if m["home_team"] == team or m["away_team"] == team
        ][-last_n:]
        if not team_matches:
            return 1.0
        points = 0
        for m in team_matches:
            if m["home_team"] == team:
                if m["home_goals"] > m["away_goals"]: points += 3
                elif m["home_goals"] == m["away_goals"]: points += 1
            else:
                if m["away_goals"] > m["home_goals"]: points += 3
                elif m["away_goals"] == m["home_goals"]: points += 1
        avg_points = points / len(team_matches)
        # Scale: 0 pts -> 0.90, 1.5 pts -> 1.0, 3 pts -> 1.10
        return 1.0 + (avg_points - 1.5) * 0.067

    def _get_h2h_adjustment(self, home_team: str, away_team: str) -> float:
        """Returns H2H bias: >1.0 means home team historically dominates."""
        if not self._match_history:
            return 1.0
        h2h_matches = [
            m for m in self._match_history[-500:]
            if (m["home_team"] == home_team and m["away_team"] == away_team)
            or (m["home_team"] == away_team and m["away_team"] == home_team)
        ][-10:]  # last 10 H2H
        if not h2h_matches:
            return 1.0
        home_wins = sum(1 for m in h2h_matches if m["home_goals"] > m["away_goals"])
        n = len(h2h_matches)
        # Scale: 0% home wins -> 0.95, 50% -> 1.0, 100% -> 1.05
        return 1.0 + (home_wins / n - 0.5) * 0.10

    def _get_rest_factor(self, team: str) -> float:
        """Returns rest factor: well-rested = slight boost."""
        if not self._match_history:
            return 1.0
        team_matches = [
            m for m in self._match_history[-100:]
            if m["home_team"] == team or m["away_team"] == team
        ]
        if len(team_matches) < 2:
            return 1.02  # well rested (no recent games)
        # We don't have actual dates in mock data, assume ~3 days between matches
        return 1.0  # neutral for now; enhance when real dates available

    def to_dict(self) -> Dict[str, Any]:
        """Serialize model state to a JSON-safe dictionary."""
        return {
            "attack_strengths": self.attack_strengths,
            "defense_strengths": self.defense_strengths,
            "home_advantage": float(self.home_advantage),
            "home_advantage_by_league": self.home_advantage_by_league,
            "global_avg_goals": float(self.global_avg_goals),
            "use_dixon_coles": self.use_dixon_coles,
            "use_context": self.use_context,
            "rho": float(self.rho),
            "is_calibrated": self.is_calibrated,
            "calibrator_1": isotonic_to_dict(self.calibrator_1) if self.is_calibrated else None,
            "calibrator_X": isotonic_to_dict(self.calibrator_X) if self.is_calibrated else None,
            "calibrator_2": isotonic_to_dict(self.calibrator_2) if self.is_calibrated else None,
            "odds_bin_calibrators": {
                side: {k: isotonic_to_dict(v) for k, v in calibs.items()}
                for side, calibs in self.odds_bin_calibrators.items()
            } if self.is_calibrated else {},
            "_training_match_count": self._training_match_count,
            "_league_match_counts": self._league_match_counts,
            "_match_history": self._match_history[-1000:],  # cap for safety
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FootballPoissonModel":
        """Deserialize model state from a dictionary."""
        model = cls(
            use_dixon_coles=data.get("use_dixon_coles", True),
            use_context=data.get("use_context", True),
        )
        model.attack_strengths = data.get("attack_strengths", {})
        model.defense_strengths = data.get("defense_strengths", {})
        model.home_advantage = data.get("home_advantage", 1.2)
        model.home_advantage_by_league = data.get("home_advantage_by_league", {})
        model.global_avg_goals = data.get("global_avg_goals", 1.3)
        model.rho = data.get("rho", -0.05)
        model.is_calibrated = data.get("is_calibrated", False)
        model._training_match_count = data.get("_training_match_count", 0)
        model._league_match_counts = data.get("_league_match_counts", {})
        model._match_history = data.get("_match_history", [])

        if model.is_calibrated:
            for key in ("calibrator_1", "calibrator_X", "calibrator_2"):
                cal_data = data.get(key)
                if cal_data:
                    setattr(model, key, isotonic_from_dict(cal_data))

            model.odds_bin_calibrators = {"1": {}, "X": {}, "2": {}}
            for side in ("1", "X", "2"):
                for bin_label, cal_data in data.get("odds_bin_calibrators", {}).get(side, {}).items():
                    model.odds_bin_calibrators[side][bin_label] = isotonic_from_dict(cal_data)
        return model

    def save(self, path: str) -> None:
        """Serialize model to a JSON file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        self.logger.info("Poisson model saved to %s", path)

    @classmethod
    def load(cls, path: str) -> "FootballPoissonModel":
        """Load model from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        model = cls.from_dict(data)
        model.logger.info("Poisson model loaded from %s", path)
        return model

    def predict_match_outcome(
        self,
        home_team: str,
        away_team: str,
        league: str = None,
        apply_calibration: bool = True,
        market_odds: Optional[Dict[str, float]] = None,
    ):
        """
        Returns probabilities for Home Win (1), Draw (X), Away Win (2).
        """
        home_attack = self.attack_strengths.get(home_team, 1.0)
        home_defense = self.defense_strengths.get(home_team, 1.0)
        away_attack = self.attack_strengths.get(away_team, 1.0)
        away_defense = self.defense_strengths.get(away_team, 1.0)
        
        # Expected goals
        ha = self.home_advantage
        if league and league in self.home_advantage_by_league:
            ha = self.home_advantage_by_league[league]

        # Apply contextual adjustments (form, H2H, rest) when enabled
        if self.use_context:
            form_home = self._get_team_form(home_team)
            form_away = self._get_team_form(away_team)
            h2h_boost = self._get_h2h_adjustment(home_team, away_team)
            rest_home = self._get_rest_factor(home_team)
            rest_away = self._get_rest_factor(away_team)
            lambda_home = home_attack * away_defense * self.global_avg_goals * ha * form_home * h2h_boost * rest_home
            lambda_away = away_attack * home_defense * self.global_avg_goals * (1 / ha) * form_away * (1 / h2h_boost) * rest_away
        else:
            lambda_home = home_attack * away_defense * self.global_avg_goals * ha
            lambda_away = away_attack * home_defense * self.global_avg_goals * (1 / ha)
        
        # Calculate matrix of exact score probabilities (up to 5 goals)
        prob_matrix = np.zeros((6, 6))
        for h in range(6):
            for a in range(6):
                base_prob = poisson.pmf(h, lambda_home) * poisson.pmf(a, lambda_away)
                if self.use_dixon_coles:
                    correction = self._dixon_coles_correction(h, a, lambda_home, lambda_away)
                    # Prevent negative probabilities
                    base_prob = max(0.0, base_prob * correction)
                prob_matrix[h, a] = base_prob
                
        # Sum probabilities for 1, X, 2
        prob_1 = np.sum(np.tril(prob_matrix, -1))
        prob_X = np.sum(np.diag(prob_matrix))
        prob_2 = np.sum(np.triu(prob_matrix, 1))
        
        # Normalize in case of truncation or correction shifts
        total = prob_1 + prob_X + prob_2
        p1, pX, p2 = prob_1 / total, prob_X / total, prob_2 / total
        
        # Apply Isotonic Calibration if enabled and fitted
        if apply_calibration and self.is_calibrated:
            # Transform and ensure scalar return
            p1_cal = float(self.calibrator_1.transform([p1])[0])
            pX_cal = float(self.calibrator_X.transform([pX])[0])
            p2_cal = float(self.calibrator_2.transform([p2])[0])
            
            # Re-normalize after independent calibrations
            total_cal = p1_cal + pX_cal + p2_cal
            p1, pX, p2 = p1_cal / total_cal, pX_cal / total_cal, p2_cal / total_cal

            if market_odds:
                side_probs = {"1": p1, "X": pX, "2": p2}
                for side in ("1", "X", "2"):
                    bin_label = self._odds_bin_label(market_odds.get(side))
                    calibrator = self.odds_bin_calibrators.get(side, {}).get(bin_label)
                    if calibrator is not None:
                        side_probs[side] = float(calibrator.transform([side_probs[side]])[0])
                total_bin = side_probs["1"] + side_probs["X"] + side_probs["2"]
                if total_bin > 0:
                    p1, pX, p2 = (
                        side_probs["1"] / total_bin,
                        side_probs["X"] / total_bin,
                        side_probs["2"] / total_bin,
                    )
        
        return {
            "1": p1,
            "X": pX,
            "2": p2,
            "expected_goals_home": lambda_home,
            "expected_goals_away": lambda_away
        }
