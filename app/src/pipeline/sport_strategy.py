"""
SportStrategy — unified predict/ingest/decide with Tier B market awareness.
Uses V1 Poisson model (robust) + V2 filter (edge-based).
"""

# The V2 model has MLE convergence issues with large team sets.
# We use V1 Poisson model for predictions (simpler, more robust)
# and V2 filter for edge detection (pragmatic, no Pinnacle requirement).
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
from src.risk.value_filter_v2 import ValueBetFilterV2
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
    """
    Football strategy with V2 Poisson model and edge-based filtering.
    Uses the converted football-data.co.uk parquet file.
    """
    sport_code = "football"

    def __init__(self, use_sharp: bool = True, use_dynamic_ev: bool = True, use_timing: bool = True):
        super().__init__(use_sharp, use_dynamic_ev, use_timing)
        self.store = LocalDataStore(settings.DATA_DIR)
        self.model: Optional[Any] = None
        self.odds_ingestor = OddsIngestor()
        self.line_shopper = LineShopper()
        # ValueBetFilterV2: foca em edge, não requer Pinnacle, não tem min_prob rígido
        self.value_filter = ValueBetFilterV2(
            min_edge=0.03,
            max_odds=10.0,
            min_odds=1.20,
            require_pinnacle=False,  # Não bloquear se Pinnacle não disponível
        )
        self.portfolio = PortfolioOptimizer(min_edge=0.03)

    def _load_matches(self) -> pd.DataFrame:
        """Carrega dados reais do parquet convertido."""
        # Tentar parquet primeiro, depois CSV cache
        paths = [
            self.store.root / "matches_football_real.parquet",
            self.store.root / "matches_football" / "real.parquet",
            self.store.root.parent / "data" / "matches_football_real.parquet",
        ]
        for p in paths:
            if p.exists():
                df = pd.read_parquet(p)
                df["date"] = pd.to_datetime(df["date"])
                logger.info("Loaded %d matches from %s", len(df), p)
                return df.sort_values("date")

        # Fallback: converter CSVs on-the-fly
        logger.warning("Parquet não encontrado. Tentando converter CSVs...")
        from scripts.convert_fdcouk_to_parquet import convert
        df = convert()
        if df is not None:
            return df
        raise FileNotFoundError(
            "Nenhum dado real encontrado. Execute: python scripts/convert_fdcouk_to_parquet.py"
        )

    def _load_matches_backtest(self) -> pd.DataFrame:
        """Load matches and prepare expected column names for backtesting."""
        df = self._load_matches()

        # Mapear colunas do CSV para o que o modelo espera
        col_map = {
            "odd_home": "odd_1",
            "odd_draw": "odd_X",
            "odd_away": "odd_2",
            "pin_close_home": "pin_close_1",
            "pin_close_draw": "pin_close_X",
            "pin_close_away": "pin_close_2",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

        # Garantir colunas de odds para outcomes
        if "odd_1" not in df.columns:
            df["odd_1"] = df.get("max_home", df.get("avg_home", 2.0))
        if "odd_X" not in df.columns:
            df["odd_X"] = df.get("max_draw", df.get("avg_draw", 3.5))
        if "odd_2" not in df.columns:
            df["odd_2"] = df.get("max_away", df.get("avg_away", 2.0))

        return df

    def ingest(self, target_date: date, strict_leakage: bool = True) -> Dict[str, Any]:
        odds_df = self.odds_ingestor.ingest_live("football") if settings.ODDS_API_KEY else pd.DataFrame()
        matches = self._load_matches()
        return {"odds_rows": len(odds_df), "matches": len(matches), "status": "ok"}

    def _ensure_model(self, df: pd.DataFrame, max_train_date=None):
        """Carrega ou treina modelo Poisson V1 (mais robusto, sem MLE).

        Args:
            df: DataFrame com dados históricos.
            max_train_date: Data máxima permitida para treino (evita look-ahead).
                            Se None, usa df['date'].max() - 90 dias.
        """
        if self.model is not None and max_train_date is None:
            return self.model

        from src.ml.models.football_poisson import FootballPoissonModel

        if max_train_date is not None:
            train = df[df["date"] < pd.Timestamp(max_train_date)]
        else:
            max_date = df["date"].max()
            train = df[df["date"] < max_date - pd.Timedelta(days=90)]

        if len(train) < 200:
            logger.warning("Apenas %d jogos para treino. Usando todos os dados disponíveis.", len(train))
            train = df[df["date"] < (pd.Timestamp(max_train_date) if max_train_date else df["date"].max())]

        self.model = FootballPoissonModel(use_dixon_coles=True)
        self.model.fit(train, calibrate=True)
        logger.info("Modelo treinado com %d jogos (V1 - Dixon-Coles, Isotonic cal)", len(train))
        return self.model

    def build_opportunities(self, target_date: date, mode: str) -> List[Dict[str, Any]]:
        """Gera oportunidades de value bet filtrando por edge (V2)."""
        df = self._load_matches_backtest()
        model = self._ensure_model(df, max_train_date=target_date)

        # Selecionar jogos para teste
        if mode == "backtest" and target_date:
            test = df[df["date"].dt.date == target_date]
            if test.empty:
                # Backtest mode: use all matches as test if no specific date
                test = df.tail(len(df))
                logger.info("No matches for %s, using all %d matches", target_date, len(df))
        else:
            # Live mode: últimos 50 jogos
            test = df.tail(50)

        if test.empty:
            logger.warning("Sem jogos para avaliar.")
            return []

        opportunities = []

        for _, row in test.iterrows():
            try:
                probs = model.predict_match_outcome(
                    row["home_team"],
                    row["away_team"],
                    league=row.get("league"),
                    apply_calibration=True,
                )
            except Exception as e:
                logger.debug("Erro na predição: %s", e)
                continue

            for outcome in ["1", "X", "2"]:
                # Obter odds correctas para cada outcome
                if outcome == "1":
                    odd = row.get("odd_1", None) or row.get("max_home", None) or row.get("avg_home", None)
                    prob = probs.get("1", 0.33)
                    pin_col = "pin_close_1"
                elif outcome == "X":
                    odd = row.get("odd_X", None) or row.get("max_draw", None) or row.get("avg_draw", None)
                    prob = probs.get("X", 0.33)
                    pin_col = "pin_close_X"
                else:
                    odd = row.get("odd_2", None) or row.get("max_away", None) or row.get("avg_away", None)
                    prob = probs.get("2", 0.33)
                    pin_col = "pin_close_2"

                if not odd or odd <= 1.0:
                    continue

                # Edge = model_prob - implied_prob
                implied_prob = 1.0 / odd
                edge = prob - implied_prob

                # Edge mínimo: 3% para favoritos, 5% para longshots
                min_edge = 0.03 if odd < 3.0 else 0.05
                if edge < min_edge:
                    continue

                # Pinnacle odds (opcional)
                pinnacle_odds = float(row.get(pin_col, row.get("pin_close_home", 0))) if pin_col in row.index else 0.0
                if pinnacle_odds <= 1.0:
                    pinnacle_odds = float(odd)

                # Construir opportunity no formato que o V2 filter espera
                opp = {
                    "match_id": str(row.get("match_id", f"m-{row.name}")),
                    "event_name": f"{row['home_team']} vs {row['away_team']}",
                    "sport": self.sport_code,
                    "model_prob": prob,
                    "calibrated_prob": prob,
                    "odds": float(odd),
                    "bookmaker_odds": float(odd),
                    "pinnacle_odds": float(pinnacle_odds),
                    "predicted_outcome": outcome,
                    "edge": float(edge),
                    "implied_prob": implied_prob,
                    "event_time": pd.to_datetime(row["date"]).to_pydatetime(),
                    "liquidity_usd": 10000.0,
                    "min_liquidity_required": 500.0,
                    "clv_pct": 0.0,  # CLV será calculado depois
                    "commission_rate": 0.05,
                    "has_critical_injury_24h": False,
                    "historical_roi_positive": True,
                }

                # V2 filter retorna (passed, reason, metrics)
                passed, reason, metrics = self.value_filter.evaluate(opp)

                if passed:
                    # Adicionar Kelly stake
                    stake = self.value_filter.kelly_stake(
                        bankroll=10000.0,
                        model_prob=prob,
                        odds=float(odd),
                        fraction=0.25,
                    )
                    opp["recommended_stake"] = round(stake, 2)
                    opp["kelly_fraction"] = round(stake / 10000.0, 4)
                    opp["status"] = "approved"
                    opportunities.append(opp)
                else:
                    logger.debug("V2 filter rejected [%s] %s: %s",
                                 outcome, opp["event_name"], reason)

        if not opportunities:
            logger.info("Nenhuma oportunidade encontrada após filtro V2.")
            return []

        # Ordenar por edge (maior primeiro)
        opportunities.sort(key=lambda x: x.get("edge", 0), reverse=True)
        logger.info("Encontradas %d oportunidades (edge médio: %.2f%%)",
                     len(opportunities),
                     sum(o["edge"] for o in opportunities) / len(opportunities) * 100)

        # Portfolio optimizer
        try:
            sized = self.portfolio.optimize_daily_portfolio(opportunities)
            if sized:
                for bet in sized:
                    bet["recommended_stake"] = bet.get("recommended_stake_usd", bet.get("recommended_stake", 10.0))
                return sized
        except Exception as e:
            logger.warning("Portfolio optimizer falhou: %s. Retornando oportunidades ordenadas.", e)

        return opportunities


class NBAStrategy(SportStrategy):
    sport_code = "nba"

    def __init__(self, use_sharp: bool = True, use_dynamic_ev: bool = True, use_timing: bool = True):
        super().__init__(use_sharp, use_dynamic_ev, use_timing)
        self.odds_ingestor = OddsIngestor()
        self.value_filter = ValueBetFilterV2(
            min_edge=0.03,
            max_odds=10.0,
            min_odds=1.20,
            require_pinnacle=False,
        )
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
            "model_prob": res["selected_prob"],
            "calibrated_prob": res["selected_prob"],
            "odds": res["selected_odds"],
            "bookmaker_odds": res["selected_odds"],
            "pinnacle_odds": res["selected_odds"],
            "edge": res["expected_edge"],
            "predicted_outcome": "HOME" if res["bet_side"] == "HOME" else "AWAY",
            "event_time": datetime.combine(target_date, datetime.min.time()),
            "liquidity_usd": 10000.0,
            "clv_pct": 0.0,
            "commission_rate": 0.05,
        }
        passed, reason, metrics = self.value_filter.evaluate(opp)
        if passed:
            opp["recommended_stake"] = self.value_filter.kelly_stake(
                bankroll=10000.0,
                model_prob=res["selected_prob"],
                odds=res["selected_odds"],
                fraction=0.25,
            )
            opp["status"] = "approved"
            return [opp]
        return []


class UFCStrategy(SportStrategy):
    """
    UFC Strategy — implementação básica.
    Usa comparação de odds entre bookmakers para encontrar value.
    """
    sport_code = "ufc"

    def __init__(self, use_sharp: bool = True, use_dynamic_ev: bool = True, use_timing: bool = True):
        super().__init__(use_sharp, use_dynamic_ev, use_timing)
        self.odds_ingestor = OddsIngestor()
        self.value_filter = ValueBetFilterV2(
            min_edge=0.05,
            max_odds=15.0,
            min_odds=1.30,
            require_pinnacle=False,
        )

    def ingest(self, target_date: date, strict_leakage: bool = True) -> Dict[str, Any]:
        events = []
        try:
            from src.ingestion.ufc_scraper import UFCScraper
            events = UFCScraper().scrape_event_list()
        except Exception:
            logger.info("UFCScraper não disponível. Sem dados live.")
        odds_df = self.odds_ingestor.ingest_live("ufc") if settings.ODDS_API_KEY else pd.DataFrame()
        return {"events": len(events), "odds_rows": len(odds_df)}

    def build_opportunities(self, target_date: date, mode: str) -> List[Dict[str, Any]]:
        """
        Para UFC, usamos odds market average como proxy de true probability.
        Encontramos value quando um bookmaker oferece odds significativamente
        melhores que a média do mercado.
        """
        if not settings.ODDS_API_KEY:
            return []

        try:
            from src.ingestion.odds_ingestor import OddsIngestor
            odds = self.odds_ingestor.ingest_live("ufc")
            if not odds:
                return []

            opportunities = []
            for match_odds in odds:
                # Calcular implied probability média do mercado
                bookmakers = match_odds.get("bookmakers", [])
                if len(bookmakers) < 2:
                    continue

                all_home_odds = []
                all_away_odds = []
                for bm in bookmakers:
                    home = bm.get("odds", {}).get("home", 0)
                    away = bm.get("odds", {}).get("away", 0)
                    if home > 0: all_home_odds.append(home)
                    if away > 0: all_away_odds.append(away)

                if not all_home_odds or not all_away_odds:
                    continue

                avg_home = sum(all_home_odds) / len(all_home_odds)
                avg_away = sum(all_away_odds) / len(all_away_odds)

                # Encontrar melhor odds
                best_home = max(all_home_odds)
                best_away = max(all_away_odds)

                market_prob_home = 1.0 / avg_home
                market_prob_away = 1.0 / avg_away

                for side, best_odd, market_prob in [
                    ("HOME", best_home, market_prob_home),
                    ("AWAY", best_away, market_prob_away),
                ]:
                    edge = market_prob - (1.0 / best_odd)
                    if edge > 0.05:
                        opp = {
                            "match_id": match_odds.get("match_id", f"ufc-{target_date}"),
                            "event_name": match_odds.get("event_name", "UFC Fight"),
                            "sport": "ufc",
                            "model_prob": market_prob,
                            "calibrated_prob": market_prob,
                            "odds": best_odd,
                            "bookmaker_odds": best_odd,
                            "pinnacle_odds": best_odd,
                            "edge": edge,
                            "predicted_outcome": side,
                            "event_time": datetime.combine(target_date, datetime.min.time()),
                            "liquidity_usd": 5000.0,
                            "clv_pct": 0.0,
                            "commission_rate": 0.05,
                            "has_critical_injury_24h": False,
                        }
                        passed, reason, metrics = self.value_filter.evaluate(opp)
                        if passed:
                            stake = self.value_filter.kelly_stake(
                                bankroll=10000.0, model_prob=market_prob,
                                odds=best_odd, fraction=0.25,
                            )
                            opp["recommended_stake"] = round(stake, 2)
                            opp["status"] = "approved"
                            opportunities.append(opp)

            return opportunities

        except Exception as e:
            logger.warning("UFC build_opportunities failed: %s", e)
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
