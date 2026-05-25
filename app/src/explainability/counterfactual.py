"""
Counterfactual explanation engine for betting decisions.

For each accepted/rejected bet, generates a natural language explanation:
"If the odds were 2.10, the bet would have been accepted with stake X."
Uses SHAP feature importance to identify which features would need to change
and by how much to flip the decision.

Optionally uses LLM to translate feature differences into human-readable text.

Usage:
    from src.explainability.counterfactual import CounterfactualExplainer

    explainer = CounterfactualExplainer(
        decision_fn=lambda features: features["edge"] > 0.03,
        feature_names=["edge", "odds", "volatility", "liquidity"],
    )
    explanation = explainer.explain(
        current_features={"edge": 0.01, "odds": 2.50, "volatility": 0.3, "liquidity": 500},
        desired_outcome=True,
    )
    # explanation.summary == "If edge were 0.03 (increase of 0.02), the bet would be accepted."
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("counterfactual")


@dataclass
class CounterfactualResult:
    """Result of a counterfactual explanation."""
    original_features: Dict[str, float]
    counterfactual_features: Dict[str, float]
    feature_deltas: Dict[str, float]
    original_decision: bool
    counterfactual_decision: bool
    summary: str
    top_features: List[str]
    distance: float  # L1 distance between original and counterfactual
    timestamp: float = field(default_factory=time.time)


class CounterfactualExplainer:
    """
    Generates counterfactual explanations for betting decisions.

    Given a decision function (accept/reject bet) and current feature values,
    finds the minimal feature changes needed to flip the decision.

    Methods:
    1. Gradient-based: Follow decision boundary gradient (fast, approximate)
    2. Search-based: Binary search along each feature dimension (precise, slower)
    3. SHAP-guided: Use SHAP values to prioritize which features to change
    """

    def __init__(
        self,
        decision_fn: Callable[[Dict[str, float]], bool],
        feature_names: List[str],
        feature_bounds: Optional[Dict[str, Tuple[float, float]]] = None,
        feature_importance: Optional[Dict[str, float]] = None,
        max_iterations: int = 100,
        step_size: float = 0.01,
        llm_backend: str = "",
    ):
        """
        Args:
            decision_fn: Function that takes feature dict and returns True (accept) / False (reject)
            feature_names: Ordered list of feature names
            feature_bounds: Dict of feature_name -> (min, max) bounds
            feature_importance: Dict of feature_name -> importance weight (e.g., from SHAP)
            max_iterations: Maximum search iterations
            step_size: Step size for gradient-based search
            llm_backend: Optional LLM backend for natural language generation ("ollama" or "openai")
        """
        self.decision_fn = decision_fn
        self.feature_names = feature_names
        self.feature_bounds = feature_bounds or {}
        self.feature_importance = feature_importance or {}
        self.max_iterations = max_iterations
        self.step_size = step_size
        self.llm_backend = llm_backend

        self._explanation_history: List[CounterfactualResult] = []

    def explain(
        self,
        current_features: Dict[str, float],
        desired_outcome: bool,
        method: str = "search",
        top_k: int = 3,
    ) -> CounterfactualResult:
        """
        Generate a counterfactual explanation.

        Args:
            current_features: Current feature values
            desired_outcome: What decision we want (True=accept, False=reject)
            method: "search" (binary search), "gradient" (gradient-based), or "shap" (SHAP-guided)
            top_k: Number of top features to report

        Returns:
            CounterfactualResult with explanation details
        """
        original_decision = self.decision_fn(current_features)

        if original_decision == desired_outcome:
            return CounterfactualResult(
                original_features=current_features.copy(),
                counterfactual_features=current_features.copy(),
                feature_deltas={},
                original_decision=original_decision,
                counterfactual_decision=original_decision,
                summary=f"Decision already matches desired outcome ({desired_outcome}). No change needed.",
                top_features=[],
                distance=0.0,
            )

        if method == "search":
            cf_features = self._search_counterfactual(current_features, desired_outcome)
        elif method == "gradient":
            cf_features = self._gradient_counterfactual(current_features, desired_outcome)
        elif method == "shap":
            cf_features = self._shap_counterfactual(current_features, desired_outcome)
        else:
            cf_features = self._search_counterfactual(current_features, desired_outcome)

        # Compute deltas
        deltas = {}
        for fname in self.feature_names:
            if fname in current_features and fname in cf_features:
                d = cf_features[fname] - current_features[fname]
                if abs(d) > 1e-8:
                    deltas[fname] = round(d, 6)

        # Sort by importance (SHAP if available, else by absolute delta)
        if self.feature_importance:
            sorted_deltas = sorted(
                deltas.items(),
                key=lambda x: abs(self.feature_importance.get(x[0], 0) * x[1]),
                reverse=True,
            )
        else:
            sorted_deltas = sorted(deltas.items(), key=lambda x: abs(x[1]), reverse=True)

        top_features = [name for name, _ in sorted_deltas[:top_k]]

        # Compute L1 distance
        distance = sum(abs(d) for d in deltas.values())

        # Generate summary
        cf_decision = self.decision_fn(cf_features)
        summary = self._generate_summary(
            current_features, cf_features, deltas, sorted_deltas[:top_k],
            original_decision, cf_decision, desired_outcome,
        )

        result = CounterfactualResult(
            original_features=current_features.copy(),
            counterfactual_features=cf_features,
            feature_deltas=deltas,
            original_decision=original_decision,
            counterfactual_decision=cf_decision,
            summary=summary,
            top_features=top_features,
            distance=round(distance, 6),
        )

        self._explanation_history.append(result)
        return result

    def _search_counterfactual(
        self,
        current: Dict[str, float],
        desired: bool,
    ) -> Dict[str, float]:
        """
        Binary search along each feature to find minimal change.

        Iterates over features ordered by importance, performing binary
        search to find the smallest change that flips the decision.
        """
        cf = current.copy()

        # Order features by importance (most important first)
        if self.feature_importance:
            ordered = sorted(
                self.feature_names,
                key=lambda f: self.feature_importance.get(f, 0),
                reverse=True,
            )
        else:
            ordered = list(self.feature_names)

        for fname in ordered:
            if fname not in cf:
                continue

            bounds = self.feature_bounds.get(fname, (-1e6, 1e6))
            low, high = bounds

            # Try increasing the feature
            test = cf.copy()
            lo, hi = cf[fname], high
            for _ in range(20):  # Binary search iterations
                mid = (lo + hi) / 2
                test[fname] = mid
                if self.decision_fn(test) == desired:
                    hi = mid
                else:
                    lo = mid
            increase_val = hi

            # Try decreasing the feature
            test = cf.copy()
            lo, hi = low, cf[fname]
            for _ in range(20):
                mid = (lo + hi) / 2
                test[fname] = mid
                if self.decision_fn(test) == desired:
                    lo = mid
                else:
                    hi = mid
            decrease_val = lo

            # Pick the direction with smaller change
            inc_delta = abs(increase_val - cf[fname])
            dec_delta = abs(decrease_val - cf[fname])

            if inc_delta < dec_delta and inc_delta < abs(high - cf[fname]):
                cf[fname] = increase_val
            elif dec_delta < inc_delta and dec_delta < abs(cf[fname] - low):
                cf[fname] = decrease_val

            # Check if we've already flipped the decision
            if self.decision_fn(cf) == desired:
                break

        return cf

    def _gradient_counterfactual(
        self,
        current: Dict[str, float],
        desired: bool,
    ) -> Dict[str, float]:
        """
        Gradient-based counterfactual search.

        Approximates the gradient of the decision boundary by finite
        differences and moves toward it.
        """
        cf = current.copy()
        eps = self.step_size

        for _ in range(self.max_iterations):
            if self.decision_fn(cf) == desired:
                break

            # Compute approximate gradient for each feature
            for fname in self.feature_names:
                if fname not in cf:
                    continue

                bounds = self.feature_bounds.get(fname, (-1e6, 1e6))

                # Finite difference
                test_plus = cf.copy()
                test_minus = cf.copy()
                test_plus[fname] = min(cf[fname] + eps, bounds[1])
                test_minus[fname] = max(cf[fname] - eps, bounds[0])

                # Direction: move toward desired outcome
                score_plus = 1.0 if self.decision_fn(test_plus) == desired else 0.0
                score_minus = 1.0 if self.decision_fn(test_minus) == desired else 0.0

                gradient = (score_plus - score_minus) / (2 * eps)

                # Weight by feature importance
                importance = self.feature_importance.get(fname, 1.0)
                step = gradient * importance * eps

                cf[fname] = np.clip(cf[fname] + step, bounds[0], bounds[1])

        return cf

    def _shap_counterfactual(
        self,
        current: Dict[str, float],
        desired: bool,
    ) -> Dict[str, float]:
        """
        SHAP-guided counterfactual: change features in order of SHAP importance.

        For each feature (sorted by SHAP value), try to find the value
        that flips the decision. Stops as soon as the decision flips.
        """
        if not self.feature_importance:
            logger.warning("No SHAP importance provided — falling back to search method")
            return self._search_counterfactual(current, desired)

        cf = current.copy()

        # Sort features by absolute SHAP value (most influential first)
        sorted_features = sorted(
            self.feature_names,
            key=lambda f: abs(self.feature_importance.get(f, 0)),
            reverse=True,
        )

        for fname in sorted_features:
            if fname not in cf:
                continue

            bounds = self.feature_bounds.get(fname, (-1e6, 1e6))

            # Binary search for the value that flips the decision
            low, high = bounds
            test = cf.copy()

            for _ in range(30):
                mid = (low + high) / 2
                test[fname] = mid
                if self.decision_fn(test) == desired:
                    high = mid
                else:
                    low = mid

            cf[fname] = (low + high) / 2

            if self.decision_fn(cf) == desired:
                break

        return cf

    def _generate_summary(
        self,
        original: Dict[str, float],
        counterfactual: Dict[str, float],
        deltas: Dict[str, float],
        top_changes: List[Tuple[str, float]],
        original_decision: bool,
        cf_decision: bool,
        desired: bool,
    ) -> str:
        """Generate a human-readable summary of the counterfactual."""
        decision_str = lambda d: "ACCEPTED" if d else "REJECTED"

        if not top_changes:
            return f"Decision: {decision_str(original_decision)}. No changes needed."

        parts = [f"Decision: {decision_str(original_decision)}."]

        for fname, delta in top_changes[:3]:
            orig_val = original.get(fname, 0)
            cf_val = counterfactual.get(fname, orig_val + delta)
            direction = "increase" if delta > 0 else "decrease"
            parts.append(
                f"If {fname} were {cf_val:.4f} ({direction} of {abs(delta):.4f}),"
            )

        parts.append(f"the bet would be {decision_str(cf_decision)}.")

        return " ".join(parts)

    def batch_explain(
        self,
        features_list: List[Dict[str, float]],
        desired_outcomes: List[bool],
        method: str = "search",
    ) -> List[CounterfactualResult]:
        """Generate counterfactual explanations for a batch of decisions."""
        results = []
        for features, desired in zip(features_list, desired_outcomes):
            result = self.explain(features, desired, method=method)
            results.append(result)
        return results

    def get_history(self, last_n: int = 20) -> List[CounterfactualResult]:
        """Get last N explanations."""
        return self._explanation_history[-last_n:]

    @property
    def status(self) -> Dict[str, Any]:
        """Get explainer status."""
        return {
            "feature_names": self.feature_names,
            "n_explanations_generated": len(self._explanation_history),
            "feature_importance_available": bool(self.feature_importance),
            "llm_backend": self.llm_backend or "none",
        }
