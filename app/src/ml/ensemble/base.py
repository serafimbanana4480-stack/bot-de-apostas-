"""
Base interface for ensemble models.

Supports both pandas DataFrame and numpy array inputs for flexibility.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Union

import numpy as np

# Lazy import pandas — not required for numpy-only usage
try:
    import pandas as pd

    ArrayLike = Union[np.ndarray, "pd.DataFrame"]
except ImportError:
    pd = None  # type: ignore[assignment]
    ArrayLike = Union[np.ndarray]  # type: ignore[misc]

ArrayLike = Union[np.ndarray, Any]  # Accept DataFrame when pandas available


def _to_numpy(X: ArrayLike) -> np.ndarray:
    """Convert DataFrame or ndarray to ndarray."""
    if pd is not None and isinstance(X, pd.DataFrame):
        return X.values
    return np.asarray(X)


def _has_column(X: ArrayLike, col: str) -> bool:
    """Check if X has a named column (DataFrame only)."""
    if pd is not None and isinstance(X, pd.DataFrame):
        return col in X.columns
    return False


def _get_column(X: ArrayLike, col: str) -> np.ndarray | None:
    """Get a column by name if X is a DataFrame, else None."""
    if pd is not None and isinstance(X, pd.DataFrame) and col in X.columns:
        return X[col].values
    return None


class EnsembleModel(ABC):
    """
    Abstract base class for ensemble models.

    All ensembles must implement:
    - fit(): Train the ensemble on training data
    - predict(): Generate combined predictions
    - get_model_weights(): Return current model weights (for monitoring)

    Accepts both numpy arrays and pandas DataFrames as input.
    """

    @abstractmethod
    def fit(
        self,
        X_train: ArrayLike,
        y_train: np.ndarray,
        opening_odds: np.ndarray | None = None,
        closing_odds: np.ndarray | None = None,
    ) -> dict[str, Any]:
        """Train the ensemble on training data."""
        ...

    @abstractmethod
    def predict(self, X: ArrayLike) -> np.ndarray:
        """Generate combined predictions for input features."""
        ...

    @abstractmethod
    def get_model_weights(self) -> dict[str, float]:
        """Return current model weights (for monitoring and CLV adjustment)."""
        ...

    def predict_proba(self, X: ArrayLike) -> np.ndarray:
        """
        Generate probability predictions. Default implementation
        uses predict() output directly as probabilities.
        """
        return self.predict(X)

    def evaluate_clv(
        self,
        X: ArrayLike,
        y: np.ndarray,
        opening_odds: np.ndarray,
        closing_odds: np.ndarray,
    ) -> dict[str, float]:
        """
        Evaluate ensemble using CLV metrics.
        """
        from src.ml.training.clv_metrics import evaluate_model_clv

        preds = self.predict(X)
        return evaluate_model_clv(
            predictions=preds,
            labels=y,
            opening_odds=opening_odds,
            closing_odds=closing_odds,
        )
