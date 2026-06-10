"""
Meta-Labeling system V2 — Reconstrução completa.

O meta-modelo filtra sinais do modelo primário usando features de MERCADO,
não features de jogo. Target: o sinal do modelo primário foi correto?

REQUIRED_FEATURES:
    - line_movement        # (opening_odd - current_odd) / opening_odd
    - sharp_ratio          # pinnacle_prob / avg_market_prob
    - steam_move           # flag: odd moveu > 5% em < 1 hora
    - reverse_line_move    # flag: dinheiro vai p/ A mas odd de A sobe
    - market_consensus     # desvio padrão das odds entre bookmakers
    - time_to_kickoff_hours # horas até o jogo
    - model_edge           # edge do modelo primário
    - model_confidence     # prob do modelo (calibrada)

Pipeline:
    1. Coletar dados de mercado (The Odds API ou histórico)
    2. Para cada aposta histórica, calcular REQUIRED_FEATURES
    3. Target: aposta ganhou? (0/1)
    4. Treinar Random Forest com TimeSeriesSplit (5 folds)
    5. Selecionar threshold de meta-prob que maximiza Precision
    6. Só gerar sinal quando meta_prob > 0.60

Validação:
    - Subset filtrada deve ter ROI > ROI total
    - Deve reduzir apostas em 40-60%
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import TimeSeriesSplit

logger = logging.getLogger("meta_labeling")


# ---------------------------------------------------------------------------
# The Odds API client (free tier: 500 req/mês)
# ---------------------------------------------------------------------------

class OddsAPIClient:
    """
    Cliente minimalista para The Odds API (free tier).
    Documentação: https://the-odds-api.com/
    """

    BASE_URL = "https://api.the-odds-api.com/v4"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ODDS_API_KEY")
        if not self.api_key:
            logger.warning("ODDS_API_KEY not set. OddsAPIClient will not work.")

    def get_historical_odds(
        self,
        sport: str = "soccer_epl",
        regions: str = "eu",
        markets: str = "h2h",
        date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical odds snapshot. Free tier limited to 500 requests/month.

        Returns list of bookmaker odds for each event.
        """
        if not self.api_key:
            raise RuntimeError("ODDS_API_KEY is required")

        import requests

        url = f"{self.BASE_URL}/sports/{sport}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "decimal",
        }
        if date:
            params["date"] = date

        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_event_odds(
        self,
        event_id: str,
        sport: str = "soccer_epl",
        regions: str = "eu",
        markets: str = "h2h",
    ) -> Dict[str, Any]:
        """Fetch odds for a specific event."""
        if not self.api_key:
            raise RuntimeError("ODDS_API_KEY is required")

        import requests

        url = f"{self.BASE_URL}/sports/{sport}/events/{event_id}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "decimal",
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Market feature builders
# ---------------------------------------------------------------------------

def build_market_features(
    df_signals: pd.DataFrame,
    df_odds: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the 8 REQUIRED_FEATURES for meta-labeling from signals + odds data.

    Expected df_signals columns:
        - predicted_outcome ('1', 'X', '2')
        - prob_home, prob_draw, prob_away (model probabilities)
        - actual_outcome (optional, for training)

    Expected df_odds columns:
        - odd_1, odd_X, odd_2 (current odds)
        - open_odd_home, open_odd_draw, open_odd_away (opening odds)
        - pin_close_home, pin_close_draw, pin_close_away (Pinnacle closing)
        - b365_home, b365_draw, b365_away (Bet365 odds, optional)
        - avg_home, avg_draw, avg_away (average market odds, optional)
        - date, commence_time (for time_to_kickoff)
    """
    df_s = df_signals.reset_index(drop=True)
    df_o = df_odds.reset_index(drop=True)

    if len(df_s) != len(df_o):
        raise ValueError(f"Signals ({len(df_s)}) and odds ({len(df_o)}) must align")

    feats = pd.DataFrame(index=df_s.index)

    # Map predicted outcome to relevant columns
    pred = df_s["predicted_outcome"].astype(str)
    odd_current = pd.Series(np.nan, index=df_s.index)
    odd_open = pd.Series(np.nan, index=df_s.index)
    odd_pinnacle = pd.Series(np.nan, index=df_s.index)
    prob_model = pd.Series(np.nan, index=df_s.index)

    for outcome, odd_col, open_col, pin_col, prob_col in [
        ("1", "odd_1", "open_odd_home", "pin_close_home", "prob_home"),
        ("X", "odd_X", "open_odd_draw", "pin_close_draw", "prob_draw"),
        ("2", "odd_2", "open_odd_away", "pin_close_away", "prob_away"),
    ]:
        mask = pred == outcome
        if odd_col in df_o.columns:
            odd_current.loc[mask] = df_o.loc[mask, odd_col]
        if open_col in df_o.columns:
            odd_open.loc[mask] = df_o.loc[mask, open_col]
        if pin_col in df_o.columns:
            odd_pinnacle.loc[mask] = df_o.loc[mask, pin_col]
        if prob_col in df_s.columns:
            prob_model.loc[mask] = df_s.loc[mask, prob_col]

    # 1. line_movement: (opening - current) / opening
    # Positive = line moved toward underdog (steam on underdog)
    feats["line_movement"] = np.where(
        odd_open > 0,
        (odd_open - odd_current) / odd_open,
        0.0,
    )

    # 2. sharp_ratio: pinnacle_prob / avg_market_prob
    avg_prob = pd.Series(np.nan, index=df_s.index)
    for outcome, odd_col in [("1", "odd_1"), ("X", "odd_X"), ("2", "odd_2")]:
        mask = pred == outcome
        if odd_col in df_o.columns:
            avg_prob.loc[mask] = 1.0 / df_o.loc[mask, odd_col]

    pin_prob = pd.Series(np.nan, index=df_s.index)
    for outcome, pin_col in [
        ("1", "pin_close_home"), ("X", "pin_close_draw"), ("2", "pin_close_away")
    ]:
        mask = pred == outcome
        if pin_col in df_o.columns:
            pin_prob.loc[mask] = 1.0 / df_o.loc[mask, pin_col]

    feats["sharp_ratio"] = np.where(
        (avg_prob > 0) & (avg_prob.notna()),
        pin_prob / avg_prob,
        1.0,
    )

    # 3. steam_move: flag if odd moved > 5% in short window
    # Proxy: |line_movement| > 0.05
    feats["steam_move"] = (feats["line_movement"].abs() > 0.05).astype(int)

    # 4. reverse_line_move: money goes to A but odd of A rises
    # Proxy: line_movement < 0 (current > opening = line moved against predicted)
    feats["reverse_line_move"] = (feats["line_movement"] < -0.02).astype(int)

    # 5. market_consensus: std dev of implied probs across bookmakers
    consensus_std = pd.Series(0.0, index=df_s.index)
    for outcome, cols in [
        ("1", ["odd_1", "b365_home", "avg_home"]),
        ("X", ["odd_X", "b365_draw", "avg_draw"]),
        ("2", ["odd_2", "b365_away", "avg_away"]),
    ]:
        mask = pred == outcome
        available = [c for c in cols if c in df_o.columns]
        if available:
            implied = 1.0 / df_o.loc[mask, available]
            consensus_std.loc[mask] = implied.std(axis=1).values
    feats["market_consensus"] = consensus_std.fillna(0.0)

    # 6. time_to_kickoff_hours (proxy using date)
    if "commence_time" in df_o.columns:
        kickoff = pd.to_datetime(df_o["commence_time"])
        now = pd.Timestamp.now()
        feats["time_to_kickoff_hours"] = (kickoff - now).dt.total_seconds() / 3600.0
    elif "date" in df_o.columns:
        # Fallback: assume 0 if game already started / no real-time data
        feats["time_to_kickoff_hours"] = 0.0
    else:
        feats["time_to_kickoff_hours"] = 0.0

    # 7. model_edge
    implied_prob = np.where(odd_current > 0, 1.0 / odd_current, 0.0)
    feats["model_edge"] = (prob_model - implied_prob).fillna(0.0)

    # 8. model_confidence
    feats["model_confidence"] = prob_model.fillna(0.33)

    # Clean
    feats = feats.replace([np.inf, -np.inf], np.nan)
    feats = feats.fillna(feats.median())
    feats = feats.fillna(0.0)

    return feats


# ---------------------------------------------------------------------------
# MetaLabelingModel
# ---------------------------------------------------------------------------

@dataclass
class MetaLabelingModel:
    """
    Modelo secundário que filtra sinais do modelo primário.
    Treina em features de MERCADO (não de jogo).
    Target: O sinal do modelo primário foi correto? (binário 0/1)
    """

    REQUIRED_FEATURES: List[str] = field(default_factory=lambda: [
        "line_movement",
        "sharp_ratio",
        "steam_move",
        "reverse_line_move",
        "market_consensus",
        "time_to_kickoff_hours",
        "model_edge",
        "model_confidence",
    ])

    meta_learner: Optional[Any] = None
    isotonic_calibrator: Optional[Any] = None
    is_fitted: bool = False
    feature_cols: List[str] = field(default_factory=list)
    threshold: float = 0.60
    calibrate: bool = True
    min_train_samples: int = 100
    _model_params: Dict[str, Any] = field(default_factory=dict)

    def fit(
        self,
        df_signals: pd.DataFrame,
        df_odds: pd.DataFrame,
        n_splits: int = 5,
    ) -> Dict[str, Any]:
        """
        Train the meta-learner on historical data.

        Args:
            df_signals: DataFrame with predicted_outcome, actual_outcome, model probs
            df_odds: DataFrame with raw odds aligned to df_signals
            n_splits: Number of temporal folds for cross-validation

        Returns:
            Training summary dict
        """
        if len(df_signals) != len(df_odds):
            raise ValueError("df_signals and df_odds must have same length")

        if len(df_signals) < 100:
            raise ValueError(f"Need at least 100 samples, got {len(df_signals)}")

        # Build market features
        X = build_market_features(df_signals, df_odds)
        self.feature_cols = [c for c in self.REQUIRED_FEATURES if c in X.columns]
        missing = [c for c in self.REQUIRED_FEATURES if c not in X.columns]
        if missing:
            logger.warning("Missing features: %s. Filling with zeros.", missing)
            for c in missing:
                X[c] = 0.0
        X = X[self.REQUIRED_FEATURES]

        # Target: was the primary signal correct?
        y = (df_signals["predicted_outcome"] == df_signals["actual_outcome"]).astype(int)

        # Temporal sort
        if "date" in df_odds.columns:
            sort_idx = pd.to_datetime(df_odds["date"]).argsort().values
            X = X.iloc[sort_idx].reset_index(drop=True)
            y = y.iloc[sort_idx].reset_index(drop=True)
        else:
            X = X.reset_index(drop=True)
            y = y.reset_index(drop=True)

        # Instantiate Random Forest
        if self.meta_learner is None:
            self.meta_learner = RandomForestClassifier(
                n_estimators=300,
                max_depth=8,
                min_samples_leaf=20,
                random_state=42,
                n_jobs=-1,
                class_weight="balanced",
            )
        self._model_params = self.meta_learner.get_params()

        # Fit on full sorted data
        self.meta_learner.fit(X, y)

        # OOF calibration with TimeSeriesSplit
        if len(X) >= n_splits * 50:
            oof_preds = np.zeros(len(X))
            tscv = TimeSeriesSplit(n_splits=n_splits)
            for train_idx, val_idx in tscv.split(X):
                X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_tr = y.iloc[train_idx]
                cloned = RandomForestClassifier(
                    n_estimators=200,
                    max_depth=8,
                    min_samples_leaf=20,
                    random_state=42,
                    n_jobs=-1,
                    class_weight="balanced",
                )
                cloned.fit(X_tr, y_tr)
                probs = cloned.predict_proba(X_val)[:, 1]
                oof_preds[val_idx] = probs

            valid_mask = oof_preds > 0
            if valid_mask.sum() > 50:
                self.isotonic_calibrator = IsotonicRegression(out_of_bounds="clip")
                self.isotonic_calibrator.fit(oof_preds[valid_mask], y[valid_mask])

        self.is_fitted = True

        # Feature importance
        importance = {}
        if hasattr(self.meta_learner, "feature_importances_"):
            importance = dict(
                zip(self.REQUIRED_FEATURES, map(float, self.meta_learner.feature_importances_))
            )

        # Find threshold that maximizes precision on OOF
        if len(X) >= n_splits * 50:
            best_thr, best_prec = self._find_best_threshold(oof_preds, y.values)
            self.threshold = best_thr
        else:
            self.threshold = 0.60

        base_acc = float(y.mean())
        return {
            "n_samples": int(len(y)),
            "base_accuracy": round(base_acc, 4),
            "n_features": len(self.REQUIRED_FEATURES),
            "feature_importance": importance,
            "selected_threshold": round(self.threshold, 3),
            "model_class": "RandomForestClassifier",
        }

    def _find_best_threshold(
        self, probs: np.ndarray, y_true: np.ndarray
    ) -> Tuple[float, float]:
        """Find threshold that maximizes precision while keeping at least 30% of bets."""
        best_thr = 0.60
        best_prec = 0.0
        for thr in np.arange(0.50, 0.85, 0.02):
            mask = probs >= thr
            if mask.sum() < len(y_true) * 0.30:
                continue
            if mask.sum() == 0:
                continue
            tp = ((probs >= thr) & (y_true == 1)).sum()
            fp = ((probs >= thr) & (y_true == 0)).sum()
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            if prec > best_prec:
                best_prec = prec
                best_thr = thr
        return float(best_thr), float(best_prec)

    def predict(self, df_signals: pd.DataFrame, df_odds: pd.DataFrame) -> np.ndarray:
        """
        Return probability that the primary signal is correct.

        Args:
            df_signals: DataFrame with primary model signals
            df_odds: DataFrame with market odds

        Returns:
            1-D array of calibrated probabilities
        """
        if not self.is_fitted:
            raise RuntimeError("MetaLabelingModel has not been fitted yet.")

        X = build_market_features(df_signals, df_odds)
        for c in self.REQUIRED_FEATURES:
            if c not in X.columns:
                X[c] = 0.0
        X = X[self.REQUIRED_FEATURES]

        probs = self.meta_learner.predict_proba(X)[:, 1]

        if self.isotonic_calibrator is not None:
            probs = self.isotonic_calibrator.transform(probs)

        return np.asarray(probs)

    def filter_signals(
        self,
        df_signals: pd.DataFrame,
        df_odds: pd.DataFrame,
        threshold: Optional[float] = None,
    ) -> pd.Series:
        """
        Return boolean mask of signals to keep.

        Args:
            df_signals: Primary model signals
            df_odds: Market odds
            threshold: Optional override for probability threshold

        Returns:
            Boolean Series (True = keep signal)
        """
        thr = threshold if threshold is not None else self.threshold
        probs = self.predict(df_signals, df_odds)
        return pd.Series(probs >= thr, index=df_signals.index)

    def evaluate(
        self,
        df_signals: pd.DataFrame,
        df_odds: pd.DataFrame,
        stake: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Evaluate meta-labeling performance.

        Returns metrics WITH and WITHOUT filtering.
        """
        df_s = df_signals.reset_index(drop=True)
        df_o = df_odds.reset_index(drop=True)

        correct = (df_s["predicted_outcome"] == df_s["actual_outcome"])

        # Odds taken for predicted outcome
        odd_map = {"1": "odd_1", "X": "odd_X", "2": "odd_2"}
        odds_taken = pd.Series(np.nan, index=df_s.index)
        for outcome, col in odd_map.items():
            mask = df_s["predicted_outcome"] == outcome
            if col in df_o.columns:
                odds_taken.loc[mask] = df_o.loc[mask, col]
        odds_taken = odds_taken.fillna(2.0)

        def _metrics(mask: pd.Series) -> Dict[str, float]:
            n = int(mask.sum())
            if n == 0:
                return {"n_bets": 0, "accuracy": 0.0, "roi": 0.0, "profit": 0.0}
            acc = float(correct[mask].mean())
            profit = float(
                (correct[mask] * (odds_taken[mask] - 1.0) - (~correct[mask]) * 1.0).sum() * stake
            )
            roi = profit / (n * stake)
            return {
                "n_bets": n,
                "accuracy": round(acc, 4),
                "roi": round(roi, 4),
                "profit": round(profit, 2),
            }

        without = _metrics(pd.Series(True, index=df_s.index))
        probs = self.predict(df_s, df_o)
        with_mask = pd.Series(probs >= self.threshold, index=df_s.index)
        with_metrics = _metrics(with_mask)

        reduction = (without["n_bets"] - with_metrics["n_bets"]) / max(without["n_bets"], 1)

        return {
            "threshold": self.threshold,
            "without_meta_labeling": without,
            "with_meta_labeling": with_metrics,
            "bets_filtered": without["n_bets"] - with_metrics["n_bets"],
            "reduction_pct": round(reduction, 4),
            "accuracy_lift": round(with_metrics["accuracy"] - without["accuracy"], 4),
            "roi_lift": round(with_metrics["roi"] - without["roi"], 4),
            "is_effective": with_metrics["roi"] > without["roi"] and reduction >= 0.30,
        }

    # ------------------------------------------------------------------ #
    # Serialization
    # ------------------------------------------------------------------ #
    def save(self, path: str) -> None:
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        model_path = path_obj.with_suffix(".joblib")
        joblib.dump(self.meta_learner, model_path)

        meta = {
            "is_fitted": self.is_fitted,
            "feature_cols": self.REQUIRED_FEATURES,
            "threshold": self.threshold,
            "model_class": "RandomForestClassifier",
            "model_params": self._get_serializable_params(),
            "isotonic_calibrator": self._isotonic_to_dict(self.isotonic_calibrator)
            if self.isotonic_calibrator is not None
            else None,
            "model_path": str(model_path.name),
        }
        meta_path = path_obj.with_suffix(".json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, default=str)

        logger.info("MetaLabelingModel saved to %s + %s", model_path, meta_path)

    @classmethod
    def load(cls, path: str) -> "MetaLabelingModel":
        path_obj = Path(path)
        meta_path = path_obj.with_suffix(".json")
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        model_path = path_obj.with_suffix(".joblib")
        meta_learner = joblib.load(model_path)

        instance = cls()
        instance.meta_learner = meta_learner
        instance.is_fitted = meta["is_fitted"]
        instance.threshold = meta.get("threshold", 0.60)
        instance._model_params = meta.get("model_params", {})

        if meta.get("isotonic_calibrator"):
            instance.isotonic_calibrator = cls._isotonic_from_dict(
                meta["isotonic_calibrator"]
            )

        return instance

    def _get_serializable_params(self) -> Dict[str, Any]:
        params = self.meta_learner.get_params() if self.meta_learner else {}
        clean = {}
        for k, v in params.items():
            if isinstance(v, (str, int, float, bool, type(None))):
                clean[k] = v
        return clean

    @staticmethod
    def _isotonic_to_dict(model: Optional[Any]) -> Optional[Dict[str, Any]]:
        if model is None:
            return None
        return {
            "X_min_": float(model.X_min_),
            "X_max_": float(model.X_max_),
            "increasing_": bool(model.increasing_),
            "X_thresholds_": np.asarray(model.X_thresholds_).tolist(),
            "y_thresholds_": np.asarray(model.y_thresholds_).tolist(),
            "out_of_bounds": model.out_of_bounds,
        }

    @staticmethod
    def _isotonic_from_dict(data: Dict[str, Any]) -> IsotonicRegression:
        model = IsotonicRegression(out_of_bounds=data.get("out_of_bounds", "clip"))
        model.X_min_ = np.float64(data["X_min_"])
        model.X_max_ = np.float64(data["X_max_"])
        model.increasing_ = data["increasing_"]
        model.X_thresholds_ = np.array(data["X_thresholds_"], dtype=float)
        model.y_thresholds_ = np.array(data["y_thresholds_"], dtype=float)
        model._build_f(model.X_thresholds_, model.y_thresholds_)
        return model


# ---------------------------------------------------------------------------
# Backward compatibility wrappers
# ---------------------------------------------------------------------------

class MetaLabeler(MetaLabelingModel):
    """Backward-compatible alias for MetaLabelingModel."""

    @staticmethod
    def extract_features(df: pd.DataFrame) -> pd.DataFrame:
        """Extract market features from a single odds DataFrame (test compat)."""
        out = pd.DataFrame(index=df.index)
        out["line_movement_home"] = (df.get("open_odd_home", 0) - df.get("pin_close_home", 0)) / df.get("open_odd_home", 1)
        out["odds_spread"] = df.get("max_home", 0) - df.get("avg_home", 0)
        out["open_vs_close_ratio"] = df.get("open_odd_home", 0) / df.get("pin_close_home", 1)
        out["b365_vs_pin"] = df.get("b365_home", 0) - df.get("pin_close_home", 0)
        out["market_efficiency_score"] = out["line_movement_home"].abs()
        out["closing_edge"] = 1 / df.get("pin_close_home", 1) - 1 / df.get("avg_home", 1)
        out = out.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        return out


def evaluate_meta_labeling(
    df_signals: pd.DataFrame,
    df_market: pd.DataFrame,
    meta_labeler: MetaLabelingModel,
    threshold: float = 0.55,
    stake: float = 1.0,
) -> Dict[str, Any]:
    """Backward-compatible wrapper."""
    # Temporarily override threshold for evaluation
    old_thr = meta_labeler.threshold
    meta_labeler.threshold = threshold
    result = meta_labeler.evaluate(df_signals, df_market, stake=stake)
    meta_labeler.threshold = old_thr
    return result
