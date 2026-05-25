"""
Hierarchical Bayesian optimizer — searches across model types (XGBoost, LightGBM, CatBoost)
and their type-specific hyperparameter spaces.

Instead of a flat search space, this uses a hierarchical approach:
  Level 1: Choose model type (xgboost, lightgbm, catboost)
  Level 2: Choose type-specific hyperparameters

This finds globally optimal solutions across model families, not just
within one family. Uses Optuna with a GP sampler (TPESampler) for
efficient Bayesian optimization.

Usage:
    from src.ml.training.hierarchical_optimizer import HierarchicalOptimizer

    opt = HierarchicalOptimizer(n_trials=100, objective="clv")
    result = opt.optimize(X_train, y_train, odds_train, X_val, y_val, odds_val)
    best_model = opt.train_final(result.best_trial)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import xgboost as xgb

try:
    import optuna
    from optuna.samplers import TPESampler
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False

try:
    import lightgbm as lgb
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False

try:
    import catboost as cb
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

from src.ml.training.clv_metrics import roi_at_k, sharpe_ratio
from src.ml.training.clv_objective import clv_xgb_objective

logger = logging.getLogger("hierarchical_optimizer")


# Per-model-type hyperparameter search spaces
XGB_SPACE = {
    "max_depth": (int, 2, 8),
    "eta": (float, 0.01, 0.3, True),  # log=True
    "min_child_weight": (int, 1, 20),
    "subsample": (float, 0.5, 1.0),
    "colsample_bytree": (float, 0.5, 1.0),
    "lambda": (float, 1e-3, 10.0, True),
    "alpha": (float, 0.0, 5.0),
    "n_estimators": (int, 50, 300),
}

LGBM_SPACE = {
    "num_leaves": (int, 20, 100),
    "learning_rate": (float, 0.01, 0.3, True),
    "min_child_samples": (int, 5, 50),
    "subsample": (float, 0.5, 1.0),
    "colsample_bytree": (float, 0.5, 1.0),
    "reg_lambda": (float, 1e-3, 10.0, True),
    "n_estimators": (int, 50, 300),
}

CATBOOST_SPACE = {
    "depth": (int, 4, 10),
    "learning_rate": (float, 0.01, 0.3, True),
    "l2_leaf_reg": (float, 1e-3, 10.0, True),
    "min_data_in_leaf": (int, 1, 50),
    "n_estimators": (int, 50, 300),
}


def _suggest_params(trial: optuna.Trial, space: Dict) -> Dict[str, Any]:
    """Suggest hyperparameters from a search space definition."""
    params = {}
    for name, spec in space.items():
        dtype = spec[0]
        low, high = spec[1], spec[2]
        log = spec[3] if len(spec) > 3 else False

        if dtype == int:
            params[name] = trial.suggest_int(name, low, high)
        elif dtype == float:
            params[name] = trial.suggest_float(name, low, high, log=log)
    return params


class HierarchicalOptimizer:
    """
    Hierarchical Bayesian optimizer that searches across model families.

    Level 1: Model type (xgboost, lightgbm, catboost)
    Level 2: Type-specific hyperparameters

    Uses TPE sampler for efficient Bayesian optimization.
    Supports multi-objective mode (ROI + Sharpe + Drawdown).
    """

    def __init__(
        self,
        n_trials: int = 100,
        objective: str = "logloss",
        multi_objective: bool = False,
        min_edge: float = 0.03,
        commission_rate: float = 0.05,
        model_types: Optional[List[str]] = None,
    ):
        if not HAS_OPTUNA:
            raise ImportError("optuna required: poetry add optuna")

        self.n_trials = n_trials
        self.objective = objective
        self.multi_objective = multi_objective
        self.min_edge = min_edge
        self.commission_rate = commission_rate

        available = ["xgboost"]
        if HAS_LGBM:
            available.append("lightgbm")
        if HAS_CATBOOST:
            available.append("catboost")
        self.model_types = model_types or available

        self._study: Optional[optuna.Study] = None

    def _train_and_evaluate(
        self,
        model_type: str,
        params: Dict[str, Any],
        X_train: np.ndarray,
        y_train: np.ndarray,
        odds_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        odds_val: np.ndarray,
        closing_odds_train: Optional[np.ndarray] = None,
        closing_odds_val: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """Train a model and evaluate on validation set."""
        if model_type == "xgboost":
            if self.objective == "clv" and closing_odds_train is not None:
                dtrain = xgb.DMatrix(X_train, label=y_train)
                dval = xgb.DMatrix(X_val, label=y_val)
                dtrain.set_float_info("opening_odds", odds_train)
                dtrain.set_float_info("closing_odds", closing_odds_train)
                dval.set_float_info("opening_odds", odds_val)
                dval.set_float_info("closing_odds", closing_odds_val)

                model = xgb.train(
                    params={"tree_method": "hist", "max_depth": params.get("max_depth", 4),
                            "eta": params.get("eta", 0.05), "verbosity": 0},
                    dtrain=dtrain,
                    num_boost_round=params.get("n_estimators", 100),
                    obj=clv_xgb_objective,
                    evals=[(dval, "val")],
                    verbose_eval=False,
                )
                raw = model.predict(dval)
                preds = 1.0 / (1.0 + np.exp(-raw))
            else:
                clf = xgb.XGBClassifier(
                    n_estimators=params.get("n_estimators", 100),
                    max_depth=params.get("max_depth", 4),
                    learning_rate=params.get("eta", 0.05),
                    min_child_weight=params.get("min_child_weight", 1),
                    subsample=params.get("subsample", 0.8),
                    colsample_bytree=params.get("colsample_bytree", 0.8),
                    reg_lambda=params.get("lambda", 1.0),
                    reg_alpha=params.get("alpha", 0.0),
                    eval_metric="logloss",
                    verbosity=0,
                )
                clf.fit(X_train, y_train)
                preds = clf.predict_proba(X_val)[:, 1]

        elif model_type == "lightgbm" and HAS_LGBM:
            clf = lgb.LGBMClassifier(
                n_estimators=params.get("n_estimators", 100),
                num_leaves=params.get("num_leaves", 31),
                learning_rate=params.get("learning_rate", 0.05),
                min_child_samples=params.get("min_child_samples", 20),
                subsample=params.get("subsample", 0.8),
                colsample_bytree=params.get("colsample_bytree", 0.8),
                reg_lambda=params.get("reg_lambda", 1.0),
                verbose=-1,
            )
            clf.fit(X_train, y_train)
            preds = clf.predict_proba(X_val)[:, 1]

        elif model_type == "catboost" and HAS_CATBOOST:
            clf = cb.CatBoostClassifier(
                iterations=params.get("n_estimators", 100),
                depth=params.get("depth", 6),
                learning_rate=params.get("learning_rate", 0.05),
                l2_leaf_reg=params.get("l2_leaf_reg", 3.0),
                min_data_in_leaf=params.get("min_data_in_leaf", 1),
                verbose=0,
            )
            clf.fit(X_train, y_train)
            preds = clf.predict_proba(X_val)[:, 1]
        else:
            preds = np.full(len(y_val), 0.5)

        # Evaluate
        roi_result = roi_at_k(preds, y_val, odds_val, k=50,
                              commission_rate=self.commission_rate, min_edge=self.min_edge)
        from src.ml.training.multi_objective import _compute_drawdown, _simulate_betting_returns
        sim_returns = _simulate_betting_returns(preds, y_val, odds_val,
                                                 min_edge=self.min_edge, commission_rate=self.commission_rate)
        sharpe = sharpe_ratio(sim_returns, annualize=False)
        max_dd = _compute_drawdown(sim_returns)

        metrics = {
            "roi": roi_result["roi"],
            "sharpe": sharpe,
            "max_drawdown": max_dd,
            "brier": float(np.mean((preds - y_val) ** 2)),
        }
        return preds, metrics

    def _objective_single(self, trial: optuna.Trial) -> float:
        """Single-objective: minimize Brier score."""
        model_type = trial.suggest_categorical("model_type", self.model_types)

        if model_type == "xgboost":
            params = _suggest_params(trial, XGB_SPACE)
        elif model_type == "lightgbm":
            params = _suggest_params(trial, LGBM_SPACE)
        else:
            params = _suggest_params(trial, CATBOOST_SPACE)

        _, metrics = self._train_and_evaluate(
            model_type, params,
            self._X_train, self._y_train, self._odds_train,
            self._X_val, self._y_val, self._odds_val,
            self._closing_train, self._closing_val,
        )
        return metrics["brier"]

    def _objective_multi(self, trial: optuna.Trial) -> Tuple[float, float, float]:
        """Multi-objective: minimize (-ROI, -Sharpe, MaxDD)."""
        model_type = trial.suggest_categorical("model_type", self.model_types)

        if model_type == "xgboost":
            params = _suggest_params(trial, XGB_SPACE)
        elif model_type == "lightgbm":
            params = _suggest_params(trial, LGBM_SPACE)
        else:
            params = _suggest_params(trial, CATBOOST_SPACE)

        _, metrics = self._train_and_evaluate(
            model_type, params,
            self._X_train, self._y_train, self._odds_train,
            self._X_val, self._y_val, self._odds_val,
            self._closing_train, self._closing_val,
        )
        return -metrics["roi"], -metrics["sharpe"], metrics["max_drawdown"]

    def optimize(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        odds_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        odds_val: np.ndarray,
        closing_odds_train: Optional[np.ndarray] = None,
        closing_odds_val: Optional[np.ndarray] = None,
    ) -> optuna.Study:
        """
        Run hierarchical optimization across model families.
        """
        self._X_train = X_train
        self._y_train = y_train
        self._odds_train = odds_train
        self._X_val = X_val
        self._y_val = y_val
        self._odds_val = odds_val
        self._closing_train = closing_odds_train
        self._closing_val = closing_odds_val

        sampler = TPESampler(seed=42, multivariate=True, warn_independent_sampling=False)

        if self.multi_objective:
            from optuna.samplers import NSGAIISampler
            sampler = NSGAIISampler(population_size=50)
            directions = ["minimize", "minimize", "minimize"]
        else:
            directions = ["minimize"]

        self._study = optuna.create_study(
            directions=directions,
            sampler=sampler,
            study_name="vbq_hierarchical",
        )

        obj_fn = self._objective_multi if self.multi_objective else self._objective_single
        self._study.optimize(obj_fn, n_trials=self.n_trials, show_progress_bar=False)

        # Log results
        if self.multi_objective:
            pareto = self._study.best_trials
            logger.info("Hierarchical Pareto front: %d solutions across %s",
                        len(pareto), self.model_types)
            for t in pareto[:3]:
                logger.info("  %s: ROI=%.4f Sharpe=%.4f DD=%.4f params=%s",
                            t.params.get("model_type", "?"),
                            -t.values[0], -t.values[1], t.values[2], t.params)
        else:
            best = self._study.best_trial
            logger.info("Hierarchical best: model=%s brier=%.6f",
                        best.params.get("model_type", "?"), best.value)

        return self._study

    def train_final(self, trial: optuna.FrozenTrial) -> Any:
        """Train the final model with the best trial's parameters."""
        model_type = trial.params.get("model_type", "xgboost")
        params = {k: v for k, v in trial.params.items() if k != "model_type"}

        logger.info("Training final %s model with params: %s", model_type, params)

        if model_type == "xgboost":
            model = xgb.XGBClassifier(
                n_estimators=params.get("n_estimators", 100),
                max_depth=params.get("max_depth", 4),
                learning_rate=params.get("eta", 0.05),
                min_child_weight=params.get("min_child_weight", 1),
                subsample=params.get("subsample", 0.8),
                colsample_bytree=params.get("colsample_bytree", 0.8),
                reg_lambda=params.get("lambda", 1.0),
                reg_alpha=params.get("alpha", 0.0),
                eval_metric="logloss",
                verbosity=0,
            )
        elif model_type == "lightgbm" and HAS_LGBM:
            model = lgb.LGBMClassifier(
                n_estimators=params.get("n_estimators", 100),
                num_leaves=params.get("num_leaves", 31),
                learning_rate=params.get("learning_rate", 0.05),
                min_child_samples=params.get("min_child_samples", 20),
                subsample=params.get("subsample", 0.8),
                colsample_bytree=params.get("colsample_bytree", 0.8),
                reg_lambda=params.get("reg_lambda", 1.0),
                verbose=-1,
            )
        elif model_type == "catboost" and HAS_CATBOOST:
            model = cb.CatBoostClassifier(
                iterations=params.get("n_estimators", 100),
                depth=params.get("depth", 6),
                learning_rate=params.get("learning_rate", 0.05),
                l2_leaf_reg=params.get("l2_leaf_reg", 3.0),
                min_data_in_leaf=params.get("min_data_in_leaf", 1),
                verbose=0,
            )
        else:
            model = xgb.XGBClassifier(verbosity=0)

        model.fit(self._X_train, self._y_train)
        return model
