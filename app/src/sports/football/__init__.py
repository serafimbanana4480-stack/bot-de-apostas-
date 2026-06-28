"""
Football Sport Implementation — uses Poisson V2 model, historical data from
football-data.co.uk, and edge-based value filtering.
"""
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from src.core.interfaces import BaseSport, BaseFeatureEngineer, BaseModelTrainer
from src.ml.models.football_poisson_v2 import FootballPoissonModelV2
from src.risk.value_filter_v2 import ValueBetFilterV2

logger = logging.getLogger(__name__)


class FootballSport(BaseSport):
    """
    Full football sport implementation using Poisson V2 models
    and edge-based value detection.
    """

    @property
    def name(self) -> str:
        return "Football"

    def __init__(self):
        self.model: Optional[FootballPoissonModelV2] = None
        self.filter = ValueBetFilterV2(min_edge=0.03, require_pinnacle=False)

    def get_ingestion_pipeline(self):
        """Returns a configured ingestion pipeline for football."""
        from src.ingestion.football_data_api import get_football_data
        return get_football_data

    def get_feature_engineer(self):
        """Returns a feature engineer for football (xG, form, H2H)."""
        class FootballFeatureEngineer(BaseFeatureEngineer):
            def build_features(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
                """Build features from raw football data."""
                return raw_data  # Passthrough for now; features built by model
        return FootballFeatureEngineer()

    def get_model_trainer(self):
        """Returns a model trainer configured for football."""
        class FootballModelTrainer(BaseModelTrainer):
            def __init__(self):
                self.model = FootballPoissonModelV2(
                    use_dixon_coles=True,
                    reg_lambda=0.15,
                    time_decay_halflife_days=90.0,
                )

            def train(self, X: Any, y: Any) -> None:
                df = X if isinstance(X, pd.DataFrame) else pd.DataFrame()
                if "home_goals" in df.columns and "away_goals" in df.columns:
                    self.model.fit(df, calibrate=True)
                    logger.info("FootballModelTrainer: fitted on %d matches", len(df))

            def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
                home = features.get("home_team", "")
                away = features.get("away_team", "")
                league = features.get("league")
                probs = self.model.predict_match_outcome(home, away, league=league)
                return probs
        return FootballModelTrainer()

    def build_value_bets(self, df_matches: pd.DataFrame, bankroll: float = 10000.0) -> List[Dict[str, Any]]:
        """
        Build value bet opportunities from match data using Poisson V2 + V2 filter.
        """
        if self.model is None:
            self.model = FootballPoissonModelV2(
                use_dixon_coles=True,
                reg_lambda=0.15,
                time_decay_halflife_days=90.0,
            )
            self.model.fit(df_matches, calibrate=True)

        opportunities = []
        for _, row in df_matches.iterrows():
            try:
                probs = self.model.predict_match_outcome(
                    row["home_team"], row["away_team"],
                    league=row.get("league"), apply_calibration=True,
                )
            except Exception:
                continue

            for outcome, odd_col in [("1", "odd_1"), ("X", "odd_X"), ("2", "odd_2")]:
                odd = row.get(odd_col, None) or row.get(f"odd_{outcome.lower()}", None)
                if not odd or odd <= 1.0:
                    continue
                prob = probs.get(outcome, 0.33)
                edge = prob - (1.0 / odd)
                if edge < 0.03:
                    continue

                opp = {
                    "match_id": str(row.get("match_id", "")),
                    "event_name": f"{row['home_team']} vs {row['away_team']}",
                    "sport": "football",
                    "model_prob": prob,
                    "calibrated_prob": prob,
                    "odds": float(odd),
                    "bookmaker_odds": float(odd),
                    "pinnacle_odds": float(row.get(f"pin_close_{outcome}", 0) or 0),
                    "edge": float(edge),
                    "predicted_outcome": outcome,
                    "event_time": row.get("date", datetime.now()),
                    "liquidity_usd": 10000.0,
                    "clv_pct": 0.0,
                    "commission_rate": 0.05,
                }
                passed, reason, metrics = self.filter.evaluate(opp)
                if passed:
                    stake = self.filter.kelly_stake(
                        bankroll=bankroll, model_prob=prob,
                        odds=float(odd), fraction=0.25,
                    )
                    opp["recommended_stake"] = round(stake, 2)
                    opp["status"] = "approved"
                    opportunities.append(opp)

        opportunities.sort(key=lambda x: x.get("edge", 0), reverse=True)
        return opportunities
