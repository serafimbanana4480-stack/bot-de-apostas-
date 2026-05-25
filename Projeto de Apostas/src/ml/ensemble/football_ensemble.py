"""
Football ensemble model combining Poisson, XGBoost, Logistic Regression,
and a meta-learner for robust 1X2 probability estimation.

The ensemble is designed to reduce overfitting of the Poisson-only approach
by diversifying across a structural model (Poisson), a non-linear tree model
(XGBoost), and a simple linear model (Logistic Regression).  A meta-learner
blends the base predictions using out-of-fold estimates to avoid leakage.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from src.ml.models.football_poisson import FootballPoissonModel
from src.validation.splits import temporal_oof_split

logger = logging.getLogger(__name__)


class FootballEnsemble:
    """
    Multi-model ensemble for football match outcome prediction (1, X, 2).

    Base models
    -----------
    - FootballPoissonModel : captures long-term team strength via attack /
      defence parameters and Dixon-Coles correction.
    - XGBoostClassifier    : non-linear residual learner (binary home-win).
    - LogisticRegression   : simple linear 3-class regularised model.

    Meta-learner
    ------------
    - ``logistic``  : multinomial LogisticRegression trained on stacked
      out-of-fold base predictions (default).
    - ``average``   : near-unregularised multinomial LogisticRegression;
      approximates a weighted average blend in logit space.

    Serialization uses JSON for structured state and joblib for sklearn
    models — no raw pickle.
    """

    # --------------------------------------------------------------------- #
    # Construction
    # --------------------------------------------------------------------- #
    def __init__(
        self,
        meta_learner: str = "logistic",
        xgb_params: dict[str, Any] | None = None,
        use_feature_selection: bool = False,
        random_state: int = 42,
    ):
        if meta_learner not in {"logistic", "average"}:
            raise ValueError("meta_learner must be 'logistic' or 'average'")

        self.meta_learner_type = meta_learner
        self.random_state = random_state
        self.use_feature_selection = use_feature_selection

        self.poisson = FootballPoissonModel(use_dixon_coles=True)
        self.xgb_params = xgb_params or {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "max_depth": 4,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "n_estimators": 100,
            "reg_lambda": 1.0,
            "reg_alpha": 0.5,
            "min_child_weight": 10,
            "tree_method": "hist",
            "random_state": random_state,
        }
        self.xgb_model: xgb.Booster | None = None
        self.logistic_model: LogisticRegression | None = None
        self.meta_model: LogisticRegression | None = None
        self.scaler = StandardScaler()

        self._feature_names: list[str] | None = None
        self._selected_features: list[str] | None = None
        self._training_count = 0
        self.is_fitted = False

    # --------------------------------------------------------------------- #
    # Feature engineering
    # --------------------------------------------------------------------- #
    @staticmethod
    def _make_feature_row(
        poisson_probs: dict[str, float],
        row: pd.Series | None,
        odd_1: float = 2.0,
        odd_X: float = 3.0,
        odd_2: float = 3.0,
        open_odd_home: float | None = None,
        open_odd_away: float | None = None,
        open_odd_draw: float | None = None,
        date: pd.Timestamp | None = None,
        league: str | None = None,
        home_advantage_by_league: dict[str, float] | None = None,
        global_avg_goals: float = 1.3,
        rho: float = -0.05,
        default_home_advantage: float = 1.2,
    ) -> dict[str, float]:
        """Build a single feature dictionary from Poisson probs + context."""
        o1 = float(row.get("odd_1", odd_1)) if row is not None else float(odd_1)
        oX = float(row.get("odd_X", odd_X)) if row is not None else float(odd_X)
        o2 = float(row.get("odd_2", odd_2)) if row is not None else float(odd_2)

        ip1 = 1.0 / max(o1, 1.01)
        ipX = 1.0 / max(oX, 1.01)
        ip2 = 1.0 / max(o2, 1.01)
        overround = ip1 + ipX + ip2 - 1.0

        if row is not None and "date" in row:
            dt = pd.to_datetime(row["date"])
        else:
            dt = date or pd.Timestamp("2023-01-01")
        month = dt.month
        dow = dt.dayofweek
        is_weekend = int(dow >= 5)
        quarter = (month - 1) // 3 + 1

        _ooh = row.get("open_odd_home", open_odd_home) if row is not None else open_odd_home
        ooh = float(_ooh) if _ooh is not None else o1
        _ooa = row.get("open_odd_away", open_odd_away) if row is not None else open_odd_away
        ooa = float(_ooa) if _ooa is not None else o2
        _ood = row.get("open_odd_draw", open_odd_draw) if row is not None else open_odd_draw
        ood = float(_ood) if _ood is not None else oX

        ha = default_home_advantage
        if home_advantage_by_league and league in home_advantage_by_league:
            ha = home_advantage_by_league[league]

        p1 = poisson_probs["1"]
        pX = poisson_probs["X"]
        p2 = poisson_probs["2"]
        egh = poisson_probs["expected_goals_home"]
        ega = poisson_probs["expected_goals_away"]

        return {
            # Poisson structural
            "poisson_p1": p1,
            "poisson_pX": pX,
            "poisson_p2": p2,
            "exp_goals_home": egh,
            "exp_goals_away": ega,
            "goal_diff_exp": egh - ega,
            # Market
            "odd_1": o1,
            "odd_X": oX,
            "odd_2": o2,
            "open_odd_home": ooh,
            "open_odd_away": ooa,
            "open_odd_draw": ood,
            "implied_prob_1": ip1,
            "implied_prob_X": ipX,
            "implied_prob_2": ip2,
            "overround": overround,
            "odds_spread_1_2": abs(o1 - o2),
            "odds_spread_1_X": abs(o1 - oX),
            "odds_spread_X_2": abs(oX - o2),
            "odds_ratio_1_2": o1 / max(o2, 0.01),
            "odds_ratio_X_1": oX / max(o1, 0.01),
            "odds_ratio_2_X": o2 / max(oX, 0.01),
            "favorite_odd": min(o1, oX, o2),
            "underdog_odd": max(o1, oX, o2),
            "mid_odd": sorted([o1, oX, o2])[1],
            "prob_favorite": 1.0 / max(min(o1, oX, o2), 1.01),
            # Temporal
            "month": month,
            "dayofweek": dow,
            "is_weekend": is_weekend,
            "quarter": quarter,
            "dayofyear": dt.dayofyear / 365.0,
            # Polynomial / interaction
            "poisson_p1_sq": p1 ** 2,
            "poisson_pX_sq": pX ** 2,
            "poisson_p2_sq": p2 ** 2,
            "poisson_p1_pX": p1 * pX,
            "poisson_p1_p2": p1 * p2,
            "poisson_pX_p2": pX * p2,
            "log_exp_goals_home": np.log1p(egh),
            "log_exp_goals_away": np.log1p(ega),
            "exp_goals_total": egh + ega,
            "exp_goals_ratio": egh / max(ega, 0.01),
            "goal_diff_exp_abs": abs(egh - ega),
            "ip1_overround": ip1 / max(overround + 1.0, 0.01),
            "ipX_overround": ipX / max(overround + 1.0, 0.01),
            "ip2_overround": ip2 / max(overround + 1.0, 0.01),
            "odds_skew": (o1 + o2) / 2.0 - oX,
            # League context
            "league_hash": (
                hash(str(league)) % 1000 / 1000.0 if league else 0.0
            ),
            "is_top_league": int(
                league
                in {"EPL", "La Liga", "Bundesliga", "Serie A", "Ligue 1"}
            )
            if league
            else 0,
            "home_advantage_league": ha,
            "global_avg_goals": global_avg_goals,
            "rho": rho,
        }

    def _build_features(
        self, df: pd.DataFrame, fit_poisson: bool = False
    ) -> pd.DataFrame:
        """Generate ML features for every row in *df*."""
        if fit_poisson:
            self.poisson.fit(df, calibrate=False)

        rows: list[dict[str, float]] = []
        for _, row in df.iterrows():
            league = row.get("league", row.get("competition", None))
            probs = self.poisson.predict_match_outcome(
                row["home_team"],
                row["away_team"],
                league=league,
                apply_calibration=False,
            )
            feat = self._make_feature_row(
                probs,
                row=row,
                league=league,
                home_advantage_by_league=self.poisson.home_advantage_by_league,
                global_avg_goals=self.poisson.global_avg_goals,
                rho=self.poisson.rho,
                default_home_advantage=self.poisson.home_advantage,
            )
            rows.append(feat)

        return pd.DataFrame(rows)

    # --------------------------------------------------------------------- #
    # Training
    # --------------------------------------------------------------------- #
    def fit(
        self,
        df: pd.DataFrame,
        target_col: str = "result",
        calibration: bool = False,
    ) -> dict[str, Any]:
        """
        Train all base models and the meta-learner.

        Parameters
        ----------
        df : pd.DataFrame
            Match-level dataframe with columns *home_team*, *away_team*,
            *home_goals*, *away_goals*, odds, *date*, etc.
        target_col : str
            Column containing outcomes (``"1"``, ``"X"``, ``"2"``).
        calibration : bool
            Unused — kept for API compatibility.

        Returns
        -------
        dict
            Training statistics.
        """
        logger.info("Fitting FootballEnsemble on %d matches...", len(df))
        if df.empty:
            return {"trained": False, "reason": "empty_data"}

        # 1. Poisson baseline ------------------------------------------------
        self.poisson.fit(df, calibrate=False)

        # 2. ML features -----------------------------------------------------
        X = self._build_features(df, fit_poisson=False)
        self._feature_names = list(X.columns)

        if self.use_feature_selection:
            from src.features.selection import select_features_rfe_temporal

            y_sel = df[target_col].astype(str).values
            self._selected_features = select_features_rfe_temporal(
                X, y_sel, n_features=20, random_state=self.random_state
            )
            X = X[self._selected_features]
            self._feature_names = list(self._selected_features)

        X_arr = X.values
        y_raw = df[target_col].astype(str).values
        y_binary = (y_raw == "1").astype(int)

        # 3. Out-of-fold predictions for meta-learner -----------------------
        oof_xgb = np.full(len(df), 0.5)
        oof_lr = np.zeros((len(df), 3))

        if len(df) >= 30:
            oof_splits = temporal_oof_split(
                df, n_splits=3, embargo_days=2, time_col=None
            )
            for train_idx, val_idx in oof_splits:
                X_tr, X_val = X_arr[train_idx], X_arr[val_idx]
                y_tr_bin = y_binary[train_idx]
                y_tr_raw = y_raw[train_idx]

                if len(np.unique(y_tr_bin)) < 2 or len(np.unique(y_tr_raw)) < 2:
                    continue

                # XGBoost fold
                dtrain = xgb.DMatrix(
                    X_tr, label=y_tr_bin, feature_names=self._feature_names
                )
                fold_xgb = xgb.train(
                    {
                        k: v
                        for k, v in self.xgb_params.items()
                        if k != "n_estimators"
                    },
                    dtrain,
                    num_boost_round=self.xgb_params.get("n_estimators", 100),
                )
                dval = xgb.DMatrix(X_val, feature_names=self._feature_names)
                oof_xgb[val_idx] = fold_xgb.predict(dval)

                # Logistic fold
                scaler_fold = StandardScaler()
                X_tr_s = scaler_fold.fit_transform(X_tr)
                X_val_s = scaler_fold.transform(X_val)
                fold_lr = LogisticRegression(
                    max_iter=1000,
                    random_state=self.random_state,
                )
                fold_lr.fit(X_tr_s, y_tr_raw)
                oof_lr[val_idx] = fold_lr.predict_proba(X_val_s)

        # Poisson predictions (in-sample is acceptable — low-variance model)
        poisson_p1 = (
            X["poisson_p1"].values
            if "poisson_p1" in X.columns
            else np.full(len(df), 1 / 3)
        )
        poisson_pX = (
            X["poisson_pX"].values
            if "poisson_pX" in X.columns
            else np.full(len(df), 1 / 3)
        )
        poisson_p2 = (
            X["poisson_p2"].values
            if "poisson_p2" in X.columns
            else np.full(len(df), 1 / 3)
        )

        # 4. Meta-learner ----------------------------------------------------
        meta_features = np.column_stack(
            [poisson_p1, poisson_pX, poisson_p2, oof_xgb, oof_lr]
        )

        meta_c = 1.0 if self.meta_learner_type == "logistic" else 1e6
        self.meta_model = LogisticRegression(
            max_iter=1000,
            C=meta_c,
            random_state=self.random_state,
        )
        self.meta_model.fit(meta_features, y_raw)

        # 5. Final base models on full data ----------------------------------
        dtrain_full = xgb.DMatrix(
            X_arr, label=y_binary, feature_names=self._feature_names
        )
        self.xgb_model = xgb.train(
            {k: v for k, v in self.xgb_params.items() if k != "n_estimators"},
            dtrain_full,
            num_boost_round=self.xgb_params.get("n_estimators", 100),
        )

        self.scaler.fit(X_arr)
        self.logistic_model = LogisticRegression(
             max_iter=1000, random_state=self.random_state
        )
        self.logistic_model.fit(self.scaler.transform(X_arr), y_raw)

        self._training_count += len(df)
        self.is_fitted = True

        return {
            "trained": True,
            "matches": len(df),
            "features": len(self._feature_names),
            "meta_learner": self.meta_learner_type,
        }

    # --------------------------------------------------------------------- #
    # Prediction
    # --------------------------------------------------------------------- #
    def predict(
        self,
        home_team: str,
        away_team: str,
        league: str | None = None,
        apply_calibration: bool = True,
        **kwargs: Any,
    ) -> dict[str, float]:
        """
        Return blended 1X2 probabilities for a single match.

        Parameters
        ----------
        home_team, away_team : str
        league : str, optional
        apply_calibration : bool
            Ignored — calibration is baked into the meta-learner.
        **kwargs :
            Odds and temporal context (``odd_1``, ``odd_X``, ``odd_2``,
            ``open_odd_home``, ``date``, etc.).

        Returns
        -------
        dict
            Keys: ``1``, ``X``, ``2``, ``expected_goals_home``,
            ``expected_goals_away``, ``poisson_p1``, ``xgb_p1``,
            ``lr_p1``, ``lr_pX``, ``lr_p2``.
        """
        if not self.is_fitted or self.meta_model is None:
            return self.poisson.predict_match_outcome(
                home_team, away_team, league=league, apply_calibration=True
            )

        # Poisson baseline
        poisson_probs = self.poisson.predict_match_outcome(
            home_team, away_team, league=league, apply_calibration=False
        )

        # Feature vector
        feat = self._make_feature_row(
            poisson_probs,
            row=None,
            odd_1=kwargs.get("odd_1", 2.0),
            odd_X=kwargs.get("odd_X", 3.0),
            odd_2=kwargs.get("odd_2", 3.0),
            open_odd_home=kwargs.get("open_odd_home"),
            open_odd_away=kwargs.get("open_odd_away"),
            open_odd_draw=kwargs.get("open_odd_draw"),
            date=pd.to_datetime(kwargs.get("date", "2023-01-01")),
            league=league,
            home_advantage_by_league=self.poisson.home_advantage_by_league,
            global_avg_goals=self.poisson.global_avg_goals,
            rho=self.poisson.rho,
            default_home_advantage=self.poisson.home_advantage,
        )

        X_pred = np.zeros((1, len(self._feature_names)))
        for i, col in enumerate(self._feature_names):
            X_pred[0, i] = feat.get(col, 0.0)

        # Base predictions
        xgb_prob = self.xgb_model.predict(
            xgb.DMatrix(X_pred, feature_names=self._feature_names)
        )[0]
        lr_probs = self.logistic_model.predict_proba(
            self.scaler.transform(X_pred)
        )[0]

        # Meta-learner blend
        meta_input = np.array(
            [
                [
                    poisson_probs["1"],
                    poisson_probs["X"],
                    poisson_probs["2"],
                    xgb_prob,
                    lr_probs[0],
                    lr_probs[1],
                    lr_probs[2],
                ]
            ]
        )
        meta_probs = self.meta_model.predict_proba(meta_input)[0]
        classes = self.meta_model.classes_

        probs: dict[str, float] = {"1": 0.0, "X": 0.0, "2": 0.0}
        for cls, p in zip(classes, meta_probs):
            probs[str(cls)] = float(p)

        total = probs["1"] + probs["X"] + probs["2"]
        if total > 0:
            probs = {k: v / total for k, v in probs.items()}

        return {
            **probs,
            "expected_goals_home": poisson_probs["expected_goals_home"],
            "expected_goals_away": poisson_probs["expected_goals_away"],
            "poisson_p1": poisson_probs["1"],
            "xgb_p1": xgb_prob,
            "lr_p1": lr_probs[0],
            "lr_pX": lr_probs[1],
            "lr_p2": lr_probs[2],
        }

    # --------------------------------------------------------------------- #
    # Serialization  (JSON + joblib — no raw pickle)
    # --------------------------------------------------------------------- #
    def save(self, path: str) -> None:
        """Serialize ensemble to disk."""
        base_path = Path(path)
        base_path.parent.mkdir(parents=True, exist_ok=True)

        # Poisson -> JSON
        poisson_path = base_path.with_suffix(".poisson.json")
        self.poisson.save(str(poisson_path))

        # XGBoost -> native JSON
        xgb_path = base_path.with_suffix(".xgb.json")
        if self.xgb_model is not None:
            self.xgb_model.save_model(str(xgb_path))

        # Sklearn models -> joblib
        logistic_path = base_path.with_suffix(".logistic.joblib")
        scaler_path = base_path.with_suffix(".scaler.joblib")
        meta_path = base_path.with_suffix(".meta.joblib")

        if self.logistic_model is not None:
            joblib.dump(self.logistic_model, logistic_path)
        joblib.dump(self.scaler, scaler_path)
        if self.meta_model is not None:
            joblib.dump(self.meta_model, meta_path)

        # Metadata -> JSON
        meta = {
            "meta_learner_type": self.meta_learner_type,
            "random_state": self.random_state,
            "use_feature_selection": self.use_feature_selection,
            "_feature_names": self._feature_names,
            "_selected_features": self._selected_features,
            "_training_count": self._training_count,
            "is_fitted": self.is_fitted,
        }
        meta_json_path = base_path.with_suffix(".meta.json")
        with open(meta_json_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, default=str)

        logger.info("FootballEnsemble saved to %s", path)

    @classmethod
    def load(cls, path: str) -> FootballEnsemble:
        """Deserialize ensemble from disk."""
        base_path = Path(path)

        with open(base_path.with_suffix(".meta.json"), encoding="utf-8") as f:
            meta = json.load(f)

        instance = cls(
            meta_learner=meta.get("meta_learner_type", "logistic"),
            random_state=meta.get("random_state", 42),
            use_feature_selection=meta.get("use_feature_selection", False),
        )
        instance._feature_names = meta.get("_feature_names")
        instance._selected_features = meta.get("_selected_features")
        instance._training_count = meta.get("_training_count", 0)
        instance.is_fitted = meta.get("is_fitted", False)

        instance.poisson = FootballPoissonModel.load(
            str(base_path.with_suffix(".poisson.json"))
        )

        xgb_path = base_path.with_suffix(".xgb.json")
        if xgb_path.exists():
            instance.xgb_model = xgb.Booster()
            instance.xgb_model.load_model(str(xgb_path))

        logistic_path = base_path.with_suffix(".logistic.joblib")
        scaler_path = base_path.with_suffix(".scaler.joblib")
        meta_model_path = base_path.with_suffix(".meta.joblib")

        if logistic_path.exists():
            instance.logistic_model = joblib.load(logistic_path)
        if scaler_path.exists():
            instance.scaler = joblib.load(scaler_path)
        if meta_model_path.exists():
            instance.meta_model = joblib.load(meta_model_path)

        logger.info("FootballEnsemble loaded from %s", path)
        return instance
