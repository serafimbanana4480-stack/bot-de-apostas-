"""
Safe serialization utilities for models.
Replaces pickle with JSON and native model formats.
"""
import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
from sklearn.isotonic import IsotonicRegression


def isotonic_to_dict(model: IsotonicRegression) -> Dict[str, Any]:
    """Serialize a fitted IsotonicRegression to a JSON-safe dict."""
    return {
        "X_min_": float(model.X_min_),
        "X_max_": float(model.X_max_),
        "increasing_": bool(model.increasing_),
        "X_thresholds_": np.asarray(model.X_thresholds_).tolist(),
        "y_thresholds_": np.asarray(model.y_thresholds_).tolist(),
        "out_of_bounds": model.out_of_bounds,
    }


def isotonic_from_dict(data: Dict[str, Any]) -> IsotonicRegression:
    """Deserialize an IsotonicRegression from a dict."""
    model = IsotonicRegression(
        out_of_bounds=data.get("out_of_bounds", "clip"),
    )
    # Directly set fitted attributes to avoid requiring training data
    model.X_min_ = np.float64(data["X_min_"])
    model.X_max_ = np.float64(data["X_max_"])
    model.increasing_ = data["increasing_"]
    model.X_thresholds_ = np.array(data["X_thresholds_"], dtype=float)
    model.y_thresholds_ = np.array(data["y_thresholds_"], dtype=float)
    # Rebuild the interpolation function used by transform/predict
    model._build_f(model.X_thresholds_, model.y_thresholds_)
    return model


def save_json(data: Dict[str, Any], path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
