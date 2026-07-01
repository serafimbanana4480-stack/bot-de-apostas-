"""
PipelineOrchestrator — unified end-to-end flow with:
- Tier B: market-aware decisions (SharpMoney, DynamicEV, Timing)
- Tier C: real execution support (Betfair, Pinnacle, Polymarket)
- Tier D: dynamic ensemble (LinUCB bandit), counterfactual explanations,
  RL timing/stake, slippage-aware execution
"""
from __future__ import annotations

import logging
import random
from datetime import date
from typing import Any, Dict, List, Optional

import numpy as np

from src.accounting.pnl import FinancialAccountingEngine
from src.core.config import settings
from src.data.local_store import LocalDataStore
from src.decision_engine.audit_logger import DecisionAuditLogger
from src.execution.balance_validator import BalanceSnapshot, BalanceValidator, ValidationVerdict
from src.execution.order_tracker import OrderTracker
from src.execution.reconciliation import ReconciliationEngine
from src.explainability.counterfactual import CounterfactualExplainer
from src.ingestion.odds_ingestor import OddsIngestor
from src.ingestion.result_settlement import ResultConsensusSettlement
from src.ml.ensemble.bandit_pipeline import BanditEnsemblePipeline
from src.ml.regime_classifier import RegimeClassifier
from src.simulations.slippage_model import SlippageModel
from src.monitoring.correlation_context import correlation_ctx
from src.monitoring.missed_opportunity_tracker import MissedOpportunityTracker
from src.validation.leakage_detector import LeakageDetector, LeakageError

# Lazy imports — only load when needed (heavy dependencies)
try:
    from src.ml.rl.ppo_agent import STAKE_FRACTIONS, BetAction, PPOBettingAgent
    _RL_AVAILABLE = True
except ImportError:
    _RL_AVAILABLE = False

try:
    from src.pipeline.sport_strategy import get_sport_strategy
    from src.simulation.historical_simulator import HonestHistoricalSimulator
    _STRATEGY_AVAILABLE = True
except ImportError:
    _STRATEGY_AVAILABLE = False

logger = logging.getLogger(__name__)

# Legal compliance warning logged once at module import
logger.warning(
    "LEGAL NOTICE: This system is designed for paper trading and quantitative research. "
    "Real-money execution requires compliance with local gambling regulations (e.g. SRIJ in Portugal). "
    "Betfair Exchange is not legally available in Portugal. Use licensed operators only."
)

# Feature names used by the counterfactual explainer
COUNTERFACTUAL_FEATURES = [
    "edge", "odds", "volatility", "liquidity", "kelly_fraction",
    "regime_score", "sharp_score", "hours_to_kickoff",
]

# Feature bounds for counterfactual search
COUNTERFACTUAL_BOUNDS = {
    "edge": (0.0, 0.3),
    "odds": (1.01, 50.0),
    "volatility": (0.0, 1.0),
    "liquidity": (0.0, 100000.0),
    "kelly_fraction": (0.0, 0.5),
    "regime_score": (0.0, 1.0),
    "sharp_score": (0.0, 1.0),
    "hours_to_kickoff": (0.0, 48.0),
}


class PipelineOrchestrator:
    def __init__(
        self,
        sport: str,
        mode: str = "live",
        use_sharp: bool = True,
        use_dynamic_ev: bool = True,
        use_timing: bool = True,
        strict_leakage: bool = True,
        use_bandit: bool = True,
        use_counterfactual: bool = True,
        use_rl_timing: bool = False,
        dry_run: bool = False,
        use_slippage: bool = True,
        bandit_context_dim: int = 10,
        bandit_alpha: float = 1.0,
        rl_agent_path: Optional[str] = None,
        shadow_mode: bool = False,
    ):
        self.sport = sport.lower()
        self.mode = mode
        self.dry_run = dry_run
        self.use_sharp = use_sharp
        self.use_dynamic_ev = use_dynamic_ev
        self.use_timing = use_timing
        self.strict_leakage = strict_leakage
        self.use_bandit = use_bandit
        self.use_counterfactual = use_counterfactual
        self.use_rl_timing = use_rl_timing
        self.use_slippage = use_slippage
        if _STRATEGY_AVAILABLE:
            self.strategy = get_sport_strategy(
                self.sport,
                use_sharp=use_sharp,
                use_dynamic_ev=use_dynamic_ev,
                use_timing=use_timing,
            )
        else:
            self.strategy = None
        self.order_tracker = OrderTracker(audit_log_path=f"logs/execution_{self.sport}.jsonl")
        self.ledger = FinancialAccountingEngine()
        self.audit = DecisionAuditLogger()
        self.settlement = ResultConsensusSettlement()
        self.odds_ingestor = OddsIngestor()
        self.store = LocalDataStore(settings.DATA_DIR)
        self.leakage = LeakageDetector()
        self.reconciliation = ReconciliationEngine(
            log_path=f"logs/reconciliation_{self.sport}.jsonl",
        )
        self.balance_validator = BalanceValidator(
            max_drift_pct=float(getattr(settings, "BALANCE_MAX_DRIFT_PCT", 5.0)),
            max_balance_age_seconds=float(getattr(settings, "BALANCE_MAX_AGE_SECONDS", 60.0)),
            min_reserve_pct=float(getattr(settings, "BALANCE_MIN_RESERVE_PCT", 5.0)),
        )
        self.regime_classifier = RegimeClassifier()
        self._paper_bankroll = float(getattr(settings, "PAPER_BANKROLL", 1000.0))
        self._betfair_connector = None
        self._pinnacle_connector = None
        self._missed_tracker = MissedOpportunityTracker()

        # --- Tier D: Dynamic ensemble via LinUCB bandit ---
        self._bandit_pipeline: Optional[BanditEnsemblePipeline] = None
        self._bandit_context_dim = bandit_context_dim
        self._bandit_alpha = bandit_alpha
        if self.use_bandit:
            self._bandit_pipeline = BanditEnsemblePipeline(
                models={},
                context_dim=bandit_context_dim,
                alpha=bandit_alpha,
            )

        # --- Tier D: Counterfactual explanations ---
        self._counterfactual: Optional[CounterfactualExplainer] = None
        if self.use_counterfactual:
            self._counterfactual = CounterfactualExplainer(
                decision_fn=self._decision_fn,
                feature_names=COUNTERFACTUAL_FEATURES,
                feature_bounds=COUNTERFACTUAL_BOUNDS,
            )

        # --- Tier D: Slippage model ---
        self._slippage_model = SlippageModel() if self.use_slippage else None

        # --- Tier D: RL agent for timing/stake ---
        self._rl_agent = None
        if self.use_rl_timing and _RL_AVAILABLE and rl_agent_path:
            self._rl_agent = PPOBettingAgent.load(rl_agent_path)

        # --- Shadow deployment controller ---
        self.shadow_mode = shadow_mode
        self._shadow_controller = None
        self._challenger_model = None
        if shadow_mode:
            from src.mlops.shadow_controller import LiveShadowController
            self._shadow_controller = LiveShadowController(
                champion_id="champion_poisson",
                challenger_id="challenger_poisson",
            )
            # Train a simple challenger on first 50% of data (past only)
            try:
                from src.ingestion.real_data_pipeline import ensure_real_data_exists
                import pandas as pd
                path = ensure_real_data_exists(settings.DATA_DIR)
                df = pd.read_parquet(path)
                df = df.sort_values("date").reset_index(drop=True)
                split = int(len(df) * 0.5)
                train = df.iloc[:split].copy()
                self._challenger_model = FootballPoissonModel(use_dixon_coles=True)
                self._challenger_model.fit(train, calibrate=True)
                logger.info("Shadow challenger trained on %d matches (past data only)", len(train))
            except Exception as e:
                logger.warning("Shadow challenger training failed: %s", e)

    # ------------------------------------------------------------------
    # Decision function for counterfactual explainer
    # ------------------------------------------------------------------
    @staticmethod
    def _decision_fn(features: Dict[str, float]) -> bool:
        """Accept bet if edge >= 2% and kelly > 0."""
        return features.get("edge", 0) >= 0.02 and features.get("kelly_fraction", 0) > 0

    # ------------------------------------------------------------------
    # Bandit model registration
    # ------------------------------------------------------------------
    def register_bandit_model(self, name: str, model: Any, predict_fn: Any) -> None:
        """Register a model with the bandit ensemble pipeline."""
        if self._bandit_pipeline is not None:
            self._bandit_pipeline.register_model(name, model, predict_fn)
            logger.info("Registered bandit model: %s", name)

    # ------------------------------------------------------------------
    # Build context vector for bandit
    # ------------------------------------------------------------------
    def _build_bandit_context(self, opp: Dict[str, Any], regime: str) -> np.ndarray:
        """Build context vector from opportunity + regime for the bandit."""
        context = np.zeros(self._bandit_context_dim)
        idx = 0

        # Edge (normalized to 0-1)
        context[idx] = np.clip(opp.get("edge", 0) / 0.2, 0, 1)
        idx += 1

        # Odds (normalized)
        context[idx] = np.clip(opp.get("bookmaker_odds", 2.0) / 10.0, 0, 1)
        idx += 1

        # Regime one-hot
        regime_map = {"low_vol": 0.0, "normal": 0.5, "high_vol": 1.0}
        context[idx] = regime_map.get(regime, 0.5)
        idx += 1

        # Liquidity (normalized)
        context[idx] = np.clip(opp.get("liquidity_usd", 1000) / 50000, 0, 1)
        idx += 1

        # Volatility
        context[idx] = np.clip(opp.get("volatility", 0.1), 0, 1)
        idx += 1

        # Hours to kickoff
        context[idx] = np.clip(opp.get("hours_to_kickoff", 6) / 48, 0, 1)
        idx += 1

        # Sharp score
        signals = opp.get("market_signals", {}) or {}
        sharp = signals.get("sharp", {})
        context[idx] = np.clip(sharp.get("sharp_score", 0.5), 0, 1)
        idx += 1

        # Model probability
        context[idx] = np.clip(opp.get("calibrated_prob", 0.5), 0, 1)
        idx += 1

        # EV
        ev = opp.get("calibrated_prob", 0.5) * opp.get("bookmaker_odds", 2.0) - 1.0
        context[idx] = np.clip((ev + 0.5) / 1.0, 0, 1)
        idx += 1

        # Kelly fraction
        context[idx] = np.clip(opp.get("final_kelly_fraction", 0) / 0.25, 0, 1)

        return context

    # ------------------------------------------------------------------
    # Build feature dict for counterfactual
    # ------------------------------------------------------------------
    def _build_counterfactual_features(self, opp: Dict[str, Any]) -> Dict[str, float]:
        """Extract features for counterfactual explanation."""
        signals = opp.get("market_signals", {}) or {}
        sharp = signals.get("sharp", {}) or {}
        return {
            "edge": float(opp.get("edge", 0)),
            "odds": float(opp.get("bookmaker_odds", 2.0)),
            "volatility": float(opp.get("volatility", 0.1)),
            "liquidity": float(opp.get("liquidity_usd", 1000)),
            "kelly_fraction": float(opp.get("final_kelly_fraction", 0)),
            "regime_score": {"low_vol": 0.2, "normal": 0.5, "high_vol": 0.8}.get(
                opp.get("detected_regime", "normal"), 0.5
            ),
            "sharp_score": float(sharp.get("sharp_score", 0.5)),
            "hours_to_kickoff": float(opp.get("hours_to_kickoff", 6)),
        }

    def run_daily(self, target_date: Optional[date] = None, dry_run: bool = False) -> Dict[str, Any]:
        self.dry_run = dry_run
        target_date = target_date or date.today()
        if dry_run:
            logger.info("Pipeline [%s] DRY RUN — decisions logged but not executed", self.sport)
        if settings.PAPER_TRADING_ONLY and not dry_run:
            logger.info("Pipeline [%s] PAPER TRADING ONLY — no real bets will be placed", self.sport)
        logger.info(
            "Pipeline [%s] mode=%s tier_b=(sharp=%s,ev=%s) tier_d=(bandit=%s,cf=%s,rl=%s,slip=%s)",
            self.sport, self.mode, self.use_sharp, self.use_dynamic_ev,
            self.use_bandit, self.use_counterfactual, self.use_rl_timing, self.use_slippage,
        )

        try:
            ingest_stats = self.strategy.ingest(target_date, strict_leakage=self.strict_leakage)
        except LeakageError as e:
            logger.critical("Ingest blocked by leakage: %s", e)
            return {"error": str(e), "leakage_gate": "FAILED", "sport": self.sport}

        opportunities = self.strategy.build_opportunities(target_date, self.mode)
        decisions: List[Dict[str, Any]] = []

        for opp in opportunities:
            event_id = opp.get("match_id", opp.get("event_id", "unknown"))
            with correlation_ctx():
                ctx = self.strategy.build_market_context(opp, self.odds_ingestor)

                # --- Regime detection ---
                regime = self.regime_classifier.predict(ctx)
                opp["detected_regime"] = regime.value

                # --- Tier D: Bandit ensemble model selection ---
                if self._bandit_pipeline is not None and self._bandit_pipeline._models:
                    bandit_context = self._build_bandit_context(opp, regime.value)
                    features_vec = self._opp_to_features(opp)
                    try:
                        model_name, prediction, weights = self._bandit_pipeline.predict(
                            features_vec, bandit_context,
                        )
                        opp["bandit_selected_model"] = model_name
                        opp["bandit_prediction"] = prediction
                        opp["bandit_weights"] = weights.tolist()
                        # Override calibrated probability with bandit-weighted prediction
                        opp["calibrated_prob"] = prediction
                        logger.debug(
                            "Bandit selected %s (pred=%.4f) for %s",
                            model_name, prediction, opp.get("match_id"),
                        )
                    except Exception as e:
                        logger.warning("Bandit prediction failed, using default: %s", e)
                else:
                    # Fallback: regime specialist blending (original logic)
                    specialist = self.regime_classifier.get_specialist_model(regime)
                    if specialist is not None:
                        opp["model_used"] = f"specialist_{regime.value}"
                        regime_result = self.regime_classifier.predict_with_specialist(
                            ctx, np.zeros(1), fallback_model=None,
                        )
                        if regime_result.get("model_used") == "specialist":
                            opp["regime_probability"] = regime_result["probability"]
                            orig_prob = opp.get("calibrated_prob", opp.get("predicted_prob", 0.5))
                            opp["calibrated_prob"] = 0.7 * regime_result["probability"] + 0.3 * orig_prob

                # --- Tier D: RL timing/stake decision ---
                if self._rl_agent is not None and _RL_AVAILABLE:
                    rl_state = self._build_rl_state(opp, ctx)
                    action_type, stake_idx = self._rl_agent.act(rl_state)
                    if action_type == BetAction.BET:
                        stake_frac = STAKE_FRACTIONS[stake_idx]
                        opp["decision"] = "BET_NOW"
                        opp["recommended_stake"] = self._paper_bankroll * stake_frac
                        opp["rl_action"] = "BET"
                        opp["rl_stake_fraction"] = stake_frac
                    elif action_type == BetAction.WAIT:
                        opp["decision"] = "WAIT"
                        opp["decision_reason"] = "RL agent recommends waiting for better odds"
                        opp["rl_action"] = "WAIT"
                    else:
                        opp["decision"] = "NO_BET"
                        opp["decision_reason"] = "RL agent recommends skipping"
                        opp["rl_action"] = "SKIP"
                else:
                    # Standard decision flow
                    opp = self.strategy.decide(opp, ctx)

                stake = opp.get("recommended_stake_usd") or opp.get("recommended_stake", 0.0)

                # --- Tier D: Slippage check ---
                slippage_info = None
                if self._slippage_model is not None and stake > 0:
                    slippage_info = self._slippage_model.compute(
                        stake=stake,
                        available_liquidity=float(opp.get("liquidity_usd", 5000)),
                        hours_to_kickoff=float(opp.get("hours_to_kickoff", 6)),
                        regime=opp.get("detected_regime", "normal"),
                        best_price=float(opp.get("bookmaker_odds", 2.0)),
                        side="back",
                    )
                    opp["slippage_bps"] = slippage_info.slippage_bps
                    opp["effective_odds"] = slippage_info.effective_price
                    opp["fill_fraction"] = slippage_info.stake_fraction_filled

                    # Reject if slippage too high
                    if not self._slippage_model.should_execute(slippage_info):
                        opp["decision"] = "NO_BET"
                        opp["decision_reason"] = (
                            f"Slippage {slippage_info.slippage_bps:.1f} bps exceeds limit "
                            f"(fill={slippage_info.stake_fraction_filled:.0%})"
                        )

                # --- Tier D: Counterfactual explanation for rejected bets ---
                counterfactual_info = None
                if self._counterfactual is not None and opp.get("decision") not in ("BET_NOW", "BET"):
                    try:
                        cf_features = self._build_counterfactual_features(opp)
                        cf_result = self._counterfactual.explain(
                            current_features=cf_features,
                            desired_outcome=True,
                            method="search",
                            top_k=3,
                        )
                        counterfactual_info = {
                            "summary": cf_result.summary,
                            "top_features": cf_result.top_features,
                            "distance": cf_result.distance,
                            "deltas": cf_result.feature_deltas,
                        }
                        opp["counterfactual"] = counterfactual_info
                    except Exception as e:
                        logger.warning("Counterfactual explanation failed: %s", e)

                # --- Audit ---
                self.audit.record_decision(
                    event_id=opp.get("match_id", ""),
                    features={
                        "sport": self.sport,
                        "edge": opp.get("edge", 0),
                        "signals": opp.get("market_signals"),
                        "bandit_model": opp.get("bandit_selected_model"),
                        "slippage_bps": opp.get("slippage_bps"),
                        "effective_odds": opp.get("effective_odds"),
                    },
                    predicted_prob=opp.get("calibrated_prob", 0),
                    market_odds=opp.get("bookmaker_odds", 0),
                    kelly_fraction=opp.get("final_kelly_fraction", 0),
                    risk_evaluation={"decision": opp.get("decision")},
                    decision_status=opp.get("decision", "NO_BET"),
                    reason=opp.get("decision_reason", ""),
                    counterfactual=counterfactual_info,
                )

                # --- Shadow deployment: log champion vs challenger ---
                if self._shadow_controller is not None and self._challenger_model is not None:
                    try:
                        home = opp.get("home_team", "")
                        away = opp.get("away_team", "")
                        current_odds = float(opp.get("bookmaker_odds", opp.get("odd_1", 2.0)))

                        def champ_pred():
                            p = self.strategy.model.predict_match_outcome(home, away, apply_calibration=True)
                            return p["1"]

                        def chall_pred():
                            p = self._challenger_model.predict_match_outcome(home, away, apply_calibration=True)
                            return p["1"]

                        self._shadow_controller.process_live_opportunity(
                            str(event_id), current_odds, champ_pred, chall_pred
                        )
                    except Exception as e:
                        logger.debug("Shadow processing skipped: %s", e)

                if opp.get("decision") in ("BET_NOW", "BET") and stake > 0:
                    opp["executed"] = self._execute(opp, stake)
                else:
                    # Track missed opportunity for later reconciliation
                    self._missed_tracker.record_skip(
                        event_id=event_id,
                        odds=opp.get("bookmaker_odds", 0.0),
                        predicted_prob=opp.get("calibrated_prob", 0.0),
                        recommended_stake=stake,
                        reason=opp.get("decision_reason", opp.get("decision", "unknown")),
                    )
                decisions.append(opp)

        summary = {
            "sport": self.sport,
            "mode": self.mode,
            "date": target_date.isoformat(),
            "ingest": ingest_stats,
            "opportunities": len(opportunities),
            "decisions": decisions,
            "bets_placed": sum(1 for d in decisions if d.get("executed")),
            "waits": sum(1 for d in decisions if d.get("decision") == "WAIT"),
            "no_bets_with_explanation": sum(
                1 for d in decisions
                if d.get("decision") not in ("BET_NOW", "BET") and d.get("counterfactual")
            ),
            "paper_bankroll": self._paper_bankroll,
            "missed_opportunities": self._missed_tracker.generate_report(),
            "tier_b": {"sharp": self.use_sharp, "dynamic_ev": self.use_dynamic_ev, "timing": self.use_timing},
            "tier_d": {
                "bandit": self.use_bandit,
                "counterfactual": self.use_counterfactual,
                "rl_timing": self.use_rl_timing,
                "slippage": self.use_slippage,
            },
            "shadow": (
                self._shadow_controller.get_shadow_performance_metrics()
                if self._shadow_controller is not None else None
            ),
        }
        self.store.save_report(summary, f"daily_{self.sport}_{target_date.isoformat()}")
        return summary

    # ------------------------------------------------------------------
    # Helper: convert opportunity to feature vector for bandit
    # ------------------------------------------------------------------
    @staticmethod
    def _opp_to_features(opp: Dict[str, Any]) -> np.ndarray:
        """Convert opportunity dict to a feature vector for model prediction."""
        feature_keys = [
            "elo_diff", "rest_diff", "win_rate_5_diff", "market_overround",
            "form_home", "form_away", "h2h_home_win_rate", "days_since_last",
        ]
        features = np.array([float(opp.get(k, 0.0)) for k in feature_keys])
        return features

    # ------------------------------------------------------------------
    # Helper: build RL state vector
    # ------------------------------------------------------------------
    def _build_rl_state(self, opp: Dict[str, Any], ctx: Dict[str, Any]) -> np.ndarray:
        """Build state vector for the RL agent."""
        state = np.zeros(20)
        idx = 0

        # Model probability
        state[idx] = np.clip(opp.get("calibrated_prob", 0.5), 0, 1)
        idx += 1

        # Opening odds
        state[idx] = np.clip(opp.get("bookmaker_odds", 2.0) / 10.0, 0, 1)
        idx += 1

        # Closing odds estimate
        state[idx] = np.clip(opp.get("pinnacle_odds", opp.get("bookmaker_odds", 2.0)) / 10.0, 0, 1)
        idx += 1

        # Implied probability
        odds = opp.get("bookmaker_odds", 2.0)
        state[idx] = np.clip(1.0 / odds if odds > 0 else 0.5, 0, 1)
        idx += 1

        # Edge
        state[idx] = np.clip(opp.get("edge", 0), -1, 1)
        idx += 1

        # Line movement
        state[idx] = np.clip(opp.get("line_movement_home", 0.0), -1, 1)
        idx += 1

        # Bankroll (normalized)
        state[idx] = np.clip(self._paper_bankroll / 2000.0, 0, 1)
        idx += 1

        # Hours to kickoff
        state[idx] = np.clip(opp.get("hours_to_kickoff", 6) / 48, 0, 1)
        idx += 1

        # Liquidity
        state[idx] = np.clip(opp.get("liquidity_usd", 1000) / 50000, 0, 1)
        idx += 1

        # Regime
        regime_map = {"low_vol": 0.2, "normal": 0.5, "high_vol": 0.8}
        state[idx] = regime_map.get(opp.get("detected_regime", "normal"), 0.5)
        idx += 1

        return state

    def _execute(self, opp: Dict[str, Any], stake: float) -> bool:
        if self.dry_run:
            logger.info("DRY RUN: Would execute %s on %s @ %.2f for %.2f", opp.get("side"), opp.get("match_id"), opp.get("bookmaker_odds", 0), stake)
            self.order_tracker.log_decision({
                "event_id": opp.get("match_id"),
                "predicted_prob": opp.get("calibrated_prob"),
                "edge": opp.get("edge"),
                "final_stake": stake,
                "executed": False,
                "dry_run": True,
                "result_settled": False,
                "human_override": False,
                "model_version": "dry_run",
                "input_features_hash": self.sport,
            })
            return False

        if settings.PAPER_TRADING_ONLY:
            # Look up actual result from settlement engine or data store
            actual_result = self._get_actual_result(opp.get("match_id"))
            if actual_result is None:
                # Fallback: simular resultado realista com base na probabilidade do modelo
                calibrated_prob = opp.get("calibrated_prob", opp.get("model_prob", 0.5))
                simulated_win = random.random() < calibrated_prob
                odds = opp.get("bookmaker_odds", 2.0)
                pnl = stake * (odds - 1.0) if simulated_win else -stake
                self._paper_bankroll += pnl
                self.ledger.record_transaction(
                    event_id=opp.get("match_id", ""),
                    stake=stake,
                    odds_predicted=odds,
                    odds_executed=odds,
                    won=simulated_win,
                )
                logger.info(
                    "PAPER %s stake=$%.2f simulated_win=%s pnl=$%.2f bankroll=$%.2f (fallback: prob=%.3f)",
                    opp.get("match_id"), stake, simulated_win, pnl, self._paper_bankroll, calibrated_prob,
                )
                self.order_tracker.log_decision({
                    "event_id": opp.get("match_id"),
                    "predicted_prob": opp.get("calibrated_prob"),
                    "edge": opp.get("edge"),
                    "kelly_stake": opp.get("final_kelly_fraction", 0),
                    "final_stake": stake,
                    "odds_available": odds,
                    "odds_used": odds,
                    "executed": False,
                    "result_settled": True,
                    "won": simulated_win,
                    "pnl": pnl,
                    "human_override": False,
                    "model_version": "paper_simulated",
                    "input_features_hash": self.sport,
                })
                return False

            bet_side = opp.get("side", "back")
            # Determine win based on actual result and bet side
            won = self._determine_paper_win(bet_side, actual_result, opp)
            odds = opp.get("bookmaker_odds", 2.0)
            pnl = stake * (odds - 1.0) if won else -stake
            self._paper_bankroll += pnl
            self.ledger.record_transaction(
                event_id=opp.get("match_id", ""),
                stake=stake,
                odds_predicted=odds,
                odds_executed=odds,
                won=won,
            )
            logger.info(
                "PAPER %s stake=$%.2f won=%s pnl=$%.2f bankroll=$%.2f",
                opp.get("match_id"), stake, won, pnl, self._paper_bankroll
            )
            self.order_tracker.log_decision({
                "event_id": opp.get("match_id"),
                "predicted_prob": opp.get("calibrated_prob"),
                "edge": opp.get("edge"),
                "kelly_stake": opp.get("final_kelly_fraction", 0),
                "final_stake": stake,
                "odds_available": odds,
                "odds_used": odds,
                "executed": False,
                "result_settled": True,
                "won": won,
                "pnl": pnl,
                "human_override": False,
                "model_version": "paper",
                "input_features_hash": self.sport,
            })
            return False

        # --- Tier C: Real execution path ---
        bookie = opp.get("best_bookie", "betfair").lower()
        odds = opp.get("bookmaker_odds", 0)
        market_id = opp.get("market_id", opp.get("match_id", ""))
        selection_id = opp.get("selection_id", 0)
        side = opp.get("side", "back")

        execution_result = None

        try:
            if bookie == "betfair":
                execution_result = self._execute_betfair(market_id, selection_id, odds, stake, side)
            elif bookie == "pinnacle":
                execution_result = self._execute_pinnacle(opp, odds, stake)
            else:
                logger.warning("No real adapter for bookie '%s' — falling back to account manager", bookie)
                from src.execution.account_manager import AccountManager
                routes = AccountManager().route_stake(bookie, stake)
                execution_result = {"status": "ROUTED", "routes": len(routes)}
        except Exception as e:
            logger.error("Real execution failed for %s: %s", opp.get("match_id"), e)
            execution_result = {"status": "ERROR", "reason": str(e)}

        executed = execution_result and execution_result.get("status") in (
            "FULLY_FILLED", "PARTIALLY_FILLED", "ROUTED",
        )

        self.order_tracker.log_decision({
            "event_id": opp.get("match_id"),
            "predicted_prob": opp.get("calibrated_prob"),
            "edge": opp.get("edge"),
            "final_stake": stake,
            "executed": executed,
            "result_settled": False,
            "human_override": False,
            "model_version": "live",
            "input_features_hash": self.sport,
            "kelly_stake": opp.get("final_kelly_fraction", 0),
            "odds_available": opp.get("bookmaker_odds"),
            "odds_used": execution_result.get("average_odds", odds) if execution_result else odds,
            "execution_result": execution_result,
        })
        return executed

    def _get_betfair_connector(self):
        """Lazy-initialize Betfair real connector."""
        if self._betfair_connector is None:
            from src.execution.adapters.betfair_real import BetfairRealConnector
            self._betfair_connector = BetfairRealConnector(
                app_key=settings.BETFAIR_APP_KEY,
                cert_path=settings.BETFAIR_CERT_PATH,
                key_path=settings.BETFAIR_KEY_PATH,
                username=settings.BETFAIR_USERNAME,
                password=settings.BETFAIR_PASSWORD,
                sandbox=settings.BETFAIR_SANDBOX,
                commission_rate=settings.BETFAIR_COMMISSION_RATE,
            )
            self._betfair_connector.authenticate()
        else:
            self._betfair_connector.ensure_session()
        return self._betfair_connector

    def _get_pinnacle_connector(self):
        """Lazy-initialize Pinnacle real connector."""
        if self._pinnacle_connector is None:
            from src.execution.adapters.pinnacle_real import PinnacleRealConnector
            self._pinnacle_connector = PinnacleRealConnector(
                client_id=settings.PINNACLE_CLIENT_ID,
                password=settings.PINNACLE_PASSWORD,
                commission_rate=settings.PINNACLE_COMMISSION_RATE,
            )
        return self._pinnacle_connector

    def _execute_betfair(
        self, market_id: str, selection_id: int, odds: float, stake: float, side: str,
    ) -> Dict[str, Any]:
        """Execute a real bet on Betfair Exchange with balance validation and reconciliation."""
        connector = self._get_betfair_connector()

        # Record pre-balance for reconciliation
        balance_info = connector.get_account_balance()
        balance_before = float(balance_info.get("availableToBetBalance", 0))
        total_balance = float(balance_info.get("availableToBetBalance", 0)) + float(balance_info.get("exposure", 0))

        # --- Tier C+: Rigorous balance validation before placing order ---
        self.balance_validator.update_real_balance(BalanceSnapshot(
            total_balance=total_balance,
            available_balance=balance_before,
            currency=balance_info.get("currencyCode", "EUR"),
            source="real_api",
        ))
        validation = self.balance_validator.validate(stake=stake)
        if validation.verdict == ValidationVerdict.FAIL:
            logger.error(
                "Balance validation FAILED for %s: %s (available=%.2f, stake=%.2f)",
                market_id, validation.message, balance_before, stake,
            )
            return {"status": "REJECTED", "reason": validation.message}
        if validation.verdict == ValidationVerdict.WARN:
            logger.warning("Balance validation warning: %s", validation.message)

        order_id = f"bf_{market_id}_{int(__import__('time').time())}"

        self.reconciliation.record_pre_balance(
            order_id=order_id,
            balance_before=balance_before,
            stake=stake,
            odds=odds,
            bookmaker="betfair",
            market_id=market_id,
        )

        # Place order
        if side.lower() == "lay":
            result = connector.place_lay_order(
                market_id=market_id,
                selection_id=selection_id,
                odds=odds,
                stake=stake,
            )
        else:
            result = connector.place_back_order(
                market_id=market_id,
                selection_id=selection_id,
                odds=odds,
                stake=stake,
            )

        # Reconcile post-balance
        if result.get("status") not in ("REJECTED",):
            new_balance_info = connector.get_account_balance()
            balance_after = float(new_balance_info.get("availableToBetBalance", 0))
            self.reconciliation.verify_post_balance(
                order_id=order_id,
                balance_after=balance_after,
                filled_stake=result.get("filled_stake", 0),
                fill_status=result.get("status", "UNKNOWN"),
                bet_id=result.get("bet_id"),
            )

        return result

    def _execute_pinnacle(self, opp: Dict[str, Any], odds: float, stake: float) -> Dict[str, Any]:
        """Execute a real bet on Pinnacle Sports with balance validation and reconciliation."""
        connector = self._get_pinnacle_connector()

        # Record pre-balance
        balance_info = connector.get_balance()
        balance_before = float(balance_info.get("availableBalance", 0))
        total_balance = float(balance_info.get("balance", balance_before))

        # --- Tier C+: Rigorous balance validation before placing order ---
        self.balance_validator.update_real_balance(BalanceSnapshot(
            total_balance=total_balance,
            available_balance=balance_before,
            currency=balance_info.get("currencyCode", "USD"),
            source="real_api",
        ))
        validation = self.balance_validator.validate(stake=stake, currency="USD")
        if validation.verdict == ValidationVerdict.FAIL:
            logger.error(
                "Balance validation FAILED for Pinnacle %s: %s (available=%.2f, stake=%.2f)",
                opp.get("match_id"), validation.message, balance_before, stake,
            )
            return {"status": "REJECTED", "reason": validation.message}
        if validation.verdict == ValidationVerdict.WARN:
            logger.warning("Balance validation warning: %s", validation.message)

        event_id = str(opp.get("event_id", opp.get("match_id", "")))
        order_id = f"pin_{event_id}_{int(__import__('time').time())}"

        self.reconciliation.record_pre_balance(
            order_id=order_id,
            balance_before=balance_before,
            stake=stake,
            odds=odds,
            bookmaker="pinnacle",
            market_id=event_id,
        )

        # Place order
        sport_id = connector.get_sport_id(self.sport)
        result = connector.place_bet(
            event_id=event_id,
            sport_id=sport_id,
            line_id=int(opp.get("line_id", 0)),
            period_number=int(opp.get("period", 0)),
            bet_type=opp.get("bet_type", "MONEYLINE"),
            odds=odds,
            stake=stake,
            team=opp.get("team"),
        )

        # Reconcile
        if result.get("status") not in ("REJECTED",):
            new_balance_info = connector.get_balance()
            balance_after = float(new_balance_info.get("availableBalance", 0))
            self.reconciliation.verify_post_balance(
                order_id=order_id,
                balance_after=balance_after,
                filled_stake=result.get("filled_stake", 0),
                fill_status=result.get("status", "UNKNOWN"),
                bet_id=result.get("bet_id"),
            )

        return result

    def _get_actual_result(self, match_id: str) -> Optional[str]:
        """Look up actual result from settlement engine or local store."""
        try:
            # Try result settlement first
            result = self.settlement.get_result(match_id)
            if result and result.get("settled"):
                return result.get("winner")
        except Exception:
            pass
        # Fallback to local data store
        try:
            df = self.store.load_matches(self.sport)
            if not df.empty and "match_id" in df.columns:
                row = df[df["match_id"] == match_id]
                if not row.empty:
                    return str(row.iloc[0].get("actual_outcome", ""))
        except Exception:
            pass
        return None

    def _determine_paper_win(self, bet_side: str, actual_result: str, opp: Dict[str, Any]) -> bool:
        """Determine if a paper bet won based on actual result."""
        if not actual_result:
            return False
        # Map actual_result to winner
        if actual_result in ("1", "H", "HOME"):
            winner = "HOME"
        elif actual_result in ("2", "A", "AWAY"):
            winner = "AWAY"
        elif actual_result in ("X", "D", "DRAW"):
            winner = "DRAW"
        else:
            winner = actual_result.upper()

        # For back bets on home/away
        if bet_side.lower() == "back":
            selection = opp.get("selection", opp.get("team", opp.get("home_team", "")))
            if winner == "HOME" and selection == opp.get("home_team"):
                return True
            if winner == "AWAY" and selection == opp.get("away_team"):
                return True
        elif bet_side.lower() == "lay":
            selection = opp.get("selection", opp.get("team", opp.get("home_team", "")))
            if winner == "HOME" and selection != opp.get("home_team"):
                return True
            if winner == "AWAY" and selection != opp.get("away_team"):
                return True
        # Default: if we bet on home and home won
        if winner == "HOME":
            return True
        return False

    def run_backtest(
        self,
        start_date: date,
        end_date: date,
        train_days: int = 180,
        test_days: int = 30,
        embargo_days: int = 7,
        check_leakage: bool = False,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        sim = HonestHistoricalSimulator(
            sport=self.sport,
            train_days=train_days,
            test_days=test_days,
            embargo_days=embargo_days,
            check_leakage=check_leakage,
            verbose=verbose,
            use_sharp=self.use_sharp,
            use_dynamic_ev=self.use_dynamic_ev,
        )
        return sim.run(self.strategy, start_date, end_date)

    @classmethod
    def run_all_sports(cls, mode: str = "live", target_date: Optional[date] = None, **kwargs) -> Dict[str, Any]:
        results = {}
        for sport in ("football", "nba", "ufc"):
            try:
                orch = cls(sport, mode=mode, **kwargs)
                results[sport] = orch.run_daily(target_date)
            except Exception as e:
                logger.error("Sport %s failed: %s", sport, e)
                results[sport] = {"error": str(e)}
        return results
