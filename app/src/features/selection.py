"""
Temporal feature selection using Recursive Feature Elimination.

Reduces high-dimensional feature sets to a robust subset using
RFE with TimeSeriesSplit to prevent data leakage.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.feature_selection import RFECV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit

logger = logging.getLogger(__name__)


def select_features_rfe_temporal(
    X: pd.DataFrame,
    y: np.ndarray,
    n_features: int = 20,
    n_splits: int = 3,
    scoring: str = "neg_log_loss",
    random_state: int = 42,
    use_permutation: bool = True,
) -> list[str]:
    """
    Select robust features using Recursive Feature Elimination with
    temporal cross-validation (TimeSeriesSplit).

    Parameters
    ----------
    X : pd.DataFrame
        Feature matrix (e.g. ~80 features).
    y : np.ndarray
        Target vector (string or int labels).
    n_features : int
        Target number of features (used as ``min_features_to_select``).
    n_splits : int
        Number of temporal splits for the internal CV.
    scoring : str
        Scoring metric for RFECV. Defaults to ``neg_log_loss``.
    random_state : int
        Random seed for the base estimator.
    use_permutation : bool
        If True, refine the selected set with permutation importance
        and keep exactly the top ``n_features``.

    Returns
    -------
    List[str]
        Names of the selected features.
    """
    y_arr = np.asarray(y).ravel()

    tscv = TimeSeriesSplit(n_splits=n_splits)

    estimator = LogisticRegression(
        max_iter=1000,
        random_state=random_state,
        solver="lbfgs",
    )

    rfecv = RFECV(
        estimator=estimator,
        step=0.2,
        cv=tscv,
        scoring=scoring,
        min_features_to_select=n_features,
        n_jobs=-1,
    )

    try:
        rfecv.fit(X.values, y_arr)
    except ValueError as exc:
        if "log_loss" in str(exc):
            logger.warning(
                "neg_log_loss failed (%s), falling back to accuracy", exc
            )
            rfecv.set_params(scoring="accuracy")
            rfecv.fit(X.values, y_arr)
        else:
            raise

    selected = X.columns[rfecv.support_].tolist()
    best_score = float(np.max(rfecv.cv_results_["mean_test_score"]))
    logger.info(
        "RFE selected %d features (best CV score: %.4f)",
        len(selected),
        best_score,
    )

    if use_permutation and len(selected) > n_features:
        from sklearn.inspection import permutation_importance

        estimator.fit(X[selected].values, y_arr)
        perm_imp = permutation_importance(
            estimator,
            X[selected].values,
            y_arr,
            n_repeats=10,
            random_state=random_state,
            scoring=rfecv.scoring,
        )
        ranking = np.argsort(perm_imp.importances_mean)[::-1]
        selected = [selected[i] for i in ranking[:n_features]]
        logger.info(
            "Permutation importance refined selection to %d features", len(selected)
        )

    return selected
