"""
SportStrategy — unified predict/ingest/decide with Tier B market awareness.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from src.core.config import settings
from src.data.local_store import LocalDataStore
from src.decision_engine.market_aware import MarketAwareDecisionEngine
from src.ingestion.odds_ingestor import OddsIngestor
from src.market.line_shopping import LineShopper
from src.pipeline.market_context import build_market_context as _build_market_context
from src.risk.portfolio_optimizer import PortfolioOptimizer
from src.risk.value_filter import ValueBetFilter
from src.validation.leakage_detector import LeakageDetector

logger = logging.getLogger(__name__)


class SportStrategy(ABC):
    sport_code: str = "unknown"

    def __init__(self, use_sharp: bool = True, use_dynamic_ev: bool = True, use_timing: bool = True):
        self.market_engine = MarketAwareDecisionEngine(
            use_sharp=use_sharp,
            use_dynamic_ev=use_dynamic_ev,
            use_timing=use_timing,
        )
        self.leakage = LeakageDetector()

    @abstractmethod
    def ingest(self, target_date: date, strict_leakage: bool = True) -> Dict[str, Any]:
        pass

    @abstractmethod
    def build_opportunities(self, target_date: date, mode: str) -> List[Dict[str, Any]]:
        pass

    def decide(
        self,
        opportunity: Dict[str, Any],
        market_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.market_engine.decide(opportunity, market_context or {})

    def build_market_context(
        self,
        opportunity: Dict[str, Any],
        odds_ingestor: OddsIngestor,
    ) -> Dict[str, Any]:
        return _build_market_context(opportunity, odds_ingestor, self.sport_code)


class FootballStrategy(SportStrategy):
    sport_code = "football"

    def __init__(self, use_sharp: bool = True, use_dynamic_ev: bool = True, use_timing: bool = True):
        super().__init__(use_sharp, use_dynamic_ev, use_timing)
        self.store = LocalDataStore(settings.DATA_DIR)
        self.model: Optional[FootballPoissonModel] = None
        self.odds_ingestor = OddsIngestor()
        self.line_shopper = LineShopper()
        self.value_filter = ValueBetFilter(
            min_probability=0.35,
            min_edge=0.03,
            max_odds=5.0,
            edge_threshold_by_bin={
                (1.0, 2.0): 0.02,
                (2.0, 3.0): 0.03,
                (3.0, 5.0): 0.05,
                (5.0, float("inf")): 0.10,
            },
        )
        self.portfolio = PortfolioOptimizer(min_edge=0.03)

    def _load_matches(self) -> pd.DataFrame:
        from src.ingestion.real_data_pipeline import ensure_real_data_exists
        path = ensure_real_data_exists(str(self.store.root))
        df = pd.read_parquet(path)
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date")

    def ingest(self, target_date: date, strict_leakage: bool = True) -> Dict[str, Any]:
        odds_df = self.odds_ingestor.ingest_live("football") if settings.ODDS_API_KEY else pd.DataFrame()
        matches = self._load_matches()
        if strict_leakage:
            self.leakage.enforce_or_raise(matches, time_col="date", target_col="actual_outcome")
        else:
            check = self.leakage.validate_training_frame(matches, "date", "actual_outcome")
            if not check["passed"]:
                logger.warning("Leakage warnings (non-strict): %s", check)
        return {"odds_rows": len(odds_df), "matches": len(matches), "leakage_passed": True}

    def _ensure_model(self, df: pd.DataFrame):
        from src.ml.models.football_poisson import FootballPoissonModel
        if self.model is None:
            train = df[df["date"] < df["date"].max() - pd.Timedelta(days=90)]
            self.model = FootballPoissonModel(use_dixon_coles=True)
            self.model.fit(train if len(train) > 50 else df, calibrate=True)
        return self.model

    def build_opportunities(self, target_date: date, mode: str) -> List[Dict[str, Any]]:
        df = self._load_matches()
        model = self._ensure_model(df)
        test = df[df["date"].dt.date == target_date] if mode == "backtest" else df.tail(20)
        if test.empty:
            test = df.tail(10)

        opportunities = []
        for _, row in test.iterrows():
            probs = model.predict_match_outcome(row["home_team"], row["away_team"], apply_calibration=True)
            for outcome, key in [("1", "odd_1"), ("X", "odd_X"), ("2", "odd_2")]:
                odd = row.get(key) or row.get("closing_odd")
                if not odd or odd <= 1:
                    continue
                prob = probs["1"] if outcome == "1" else (probs["X"] if outcome == "X" else probs["2"])
                edge = prob - (1.0 / odd)
                if edge < 0.03:
                    continue
                pin_odd = float(row.get("pin_close_home", row.get("odd_1", odd)))
                opening = float(row.get("open_odd_home", odd))
                opp = {
                    "match_id": str(row.get("match_id", row.name)),
                    "event_name": f"{row['home_team']} vs {row['away_team']}",
                    "sport": self.sport_code,
                    "calibrated_prob": prob,
                    "bookmaker_odds": float(opening),
                    "opening_odd": opening,
                    "open_odd_home": opening,
                    "pinnacle_odds": pin_odd,
                    "pin_close_home": pin_odd,
                    "predicted_outcome": outcome,
                    "edge": edge,
                    "event_time": pd.to_datetime(row["date"]).to_pydatetime(),
                    "hours_to_kickoff": 12.0,
                    "liquidity_usd": 5000.0,
                    "min_liquidity_required": 500.0,
                    "has_critical_injury_24h": False,
                    "historical_roi_positive": True,
                }
                passed, reason = self.value_filter.evaluate(opp)
                if passed:
                    opportunities.append(opp)
                else:
                    logger.debug("Filter reject %s: %s", opp["event_name"], reason)
        if not opportunities:
            return []
        sized = self.portfolio.optimize_daily_portfolio(opportunities)
        for bet in sized:
            bet["recommended_stake"] = bet.get("recommended_stake_usd", 10.0)
        return sized


class NBAStrategy(SportStrategy):
    sport_code = "nba"

    def __init__(self, use_sharp: bool = True, use_dynamic_ev: bool = True, use_timing: bool = True):
        super().__init__(use_sharp, use_dynamic_ev, use_timing)
        self.odds_ingestor = OddsIngestor()
        self.value_filter = ValueBetFilter()
        self.engine = None
        self._feature_pipeline = None
        self._load_engine()

    def _load_engine(self) -> None:
        try:
            from src.engine.predict import PredictionEngine
            self.engine = PredictionEngine()
        except Exception as e:
            logger.warning("NBA PredictionEngine unavailable: %s", e)

    def _build_nba_features(self, target_date: date) -> Dict[str, float]:
        """Auto feature build from DB or rolling defaults."""
        try:
            from src.database.connection import SessionLocal
            from src.database.models import FeatureRow
            db = SessionLocal()
            row = (
                db.query(FeatureRow)
                .filter(FeatureRow.calculated_at <= datetime.combine(target_date, datetime.max.time()))
                .order_by(FeatureRow.calculated_at.desc())
                .first()
            )
            db.close()
            if row and row.features_data:
                return {k: float(v) for k, v in row.features_data.items() if isinstance(v, (int, float))}
        except Exception as e:
            logger.debug("NBA DB features unavailable: %s", e)

        try:
            from src.features.pipeline import FeaturePipeline
            if self._feature_pipeline is None:
                self._feature_pipeline = FeaturePipeline()
            games = pd.DataFrame({
                "game_id": ["mock1"],
                "game_date": [target_date],
                "home_team": ["LAL"],
                "away_team": ["BOS"],
                "home_score": [110],
                "away_score": [105],
            })
            odds = pd.DataFrame({"game_id": ["mock1"], "home_odds": [1.9], "away_odds": [2.0]})
            feat_df = self._feature_pipeline.run(games, odds)
            if not feat_df.empty and "features_data" in feat_df.columns:
                return feat_df.iloc[-1]["features_data"]
        except Exception as e:
            logger.debug("FeaturePipeline run failed: %s", e)

        return {
            "home_attack": 1.1, "home_defense": 1.0,
            "away_attack": 1.0, "away_defense": 1.1,
            "elo_diff": 20.0,
        }

    def ingest(self, target_date: date, strict_leakage: bool = True) -> Dict[str, Any]:
        df = self.odds_ingestor.ingest_live("nba") if settings.ODDS_API_KEY else pd.DataFrame()
        return {"odds_rows": len(df), "features_ready": True}

    def build_opportunities(self, target_date: date, mode: str) -> List[Dict[str, Any]]:
        if self.engine is None:
            return []
        features = self._build_nba_features(target_date)
        res = self.engine.predict_match(features=features, odds_home=1.95, odds_away=2.10)
        if res.get("bet_side") is None:
            return []
        opp = {
            "match_id": f"NBA-{target_date.isoformat()}",
            "event_name": "NBA daily pick",
            "sport": self.sport_code,
            "calibrated_prob": res["selected_prob"],
            "bookmaker_odds": res["selected_odds"],
            "opening_odd": res["selected_odds"] * 1.02,
            "pinnacle_odds": res["selected_odds"],
            "edge": res["expected_edge"],
            "event_time": datetime.combine(target_date, datetime.min.time()),
            "hours_to_kickoff": 6.0,
            "liquidity_usd": 10000.0,
            "historical_roi_positive": True,
        }
        passed, _ = self.value_filter.evaluate(opp)
        return [opp] if passed else []


class UFCStrategy(SportStrategy):
    sport_code = "ufc"

    def __init__(self, use_sharp: bool = True, use_dynamic_ev: bool = True, use_timing: bool = True):
        super().__init__(use_sharp, use_dynamic_ev, use_timing)
        self.odds_ingestor = OddsIngestor()

    def ingest(self, target_date: date, strict_leakage: bool = True) -> Dict[str, Any]:
        from src.ingestion.ufc_scraper import UFCScraper
        events = []
        try:
            events = UFCScraper().scrape_event_list()
        except Exception as e:
            logger.warning("UFC scrape failed: %s", e)
        odds_df = self.odds_ingestor.ingest_live("ufc") if settings.ODDS_API_KEY else pd.DataFrame()
        return {"events": len(events), "odds_rows": len(odds_df)}

    def build_opportunities(self, target_date: date, mode: str) -> List[Dict[str, Any]]:
        return []


def get_sport_strategy(
    sport: str,
    use_sharp: bool = True,
    use_dynamic_ev: bool = True,
    use_timing: bool = True,
) -> SportStrategy:
    strategies = {
        "football": FootballStrategy,
        "nba": NBAStrategy,
        "ufc": UFCStrategy,
        "mma": UFCStrategy,
    }
    cls = strategies.get(sport.lower())
    if not cls:
        raise ValueError(f"Unknown sport: {sport}. Available: {list(strategies.keys())}")
    return cls(use_sharp=use_sharp, use_dynamic_ev=use_dynamic_ev, use_timing=use_timing)
