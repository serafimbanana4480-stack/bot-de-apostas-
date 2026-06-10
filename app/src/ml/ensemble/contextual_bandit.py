"""
Contextual bandit (LinUCB) for dynamic ensemble weight selection.

Instead of fixed ensemble weights, LinUCB learns in real-time which
model (or combination) maximizes CLV for each betting context.

Context includes: regime, liquidity, volatility, time-to-kickoff.
Reward: realized CLV per bet.

The algorithm maintains a separate linear model per arm (model), and
uses upper confidence bounds to balance exploration vs exploitation.

Usage:
    from src.ml.ensemble.contextual_bandit import LinUCBEnsemble

    bandit = LinUCBEnsemble(
        n_arms=3,  # e.g., xgboost, lightgbm, baseline
        context_dim=10,
    )
    
    # For each betting opportunity:
    arm = bandit.select(context_features)
    prediction = models[arm].predict(features)
    
    # After bet settles:
    bandit.update(arm, context_features, reward=clv)
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("contextual_bandit")


class LinUCBEnsemble:
    """
    LinUCB (Linear Upper Confidence Bound) for dynamic model selection.

    Each "arm" corresponds to a model in the ensemble. The algorithm
    learns a linear model of expected reward (CLV) as a function of
    context features for each arm. It selects the arm with the highest
    upper confidence bound (expected reward + exploration bonus).

    This provides:
    - Automatic model selection per context (regime, liquidity, etc.)
    - Exploration of under-used models
    - Online learning — no need to retrain the ensemble
    """

    def __init__(
        self,
        n_arms: int = 3,
        context_dim: int = 10,
        alpha: float = 1.0,
        arm_names: Optional[List[str]] = None,
        decay_factor: float = 0.995,
    ):
        """
        Args:
            n_arms: Number of models/arms in the ensemble
            context_dim: Dimension of context feature vector
            alpha: Exploration parameter (higher = more exploration)
            arm_names: Human-readable names for each arm
            decay_factor: Exponential decay for old observations (0.995 = slow decay)
        """
        self.n_arms = n_arms
        self.context_dim = context_dim
        self.alpha = alpha
        self.arm_names = arm_names or [f"model_{i}" for i in range(n_arms)]
        self.decay_factor = decay_factor

        # LinUCB parameters per arm
        self._A = [np.eye(context_dim) for _ in range(n_arms)]  # Context matrix
        self._b = [np.zeros(context_dim) for _ in range(n_arms)]  # Reward vector
        self._theta = [np.zeros(context_dim) for _ in range(n_arms)]  # Weights

        # Statistics
        self._arm_counts = np.zeros(n_arms, dtype=int)
        self._arm_rewards = [[] for _ in range(n_arms)]
        self._total_updates = 0
        self._last_update_time: Optional[float] = None

    def select(
        self,
        context: np.ndarray,
        exclude_arms: Optional[List[int]] = None,
    ) -> Tuple[int, float]:
        """
        Select the best arm given the current context.

        Args:
            context: Context feature vector (shape: context_dim,)
            exclude_arms: Arms to exclude from selection (e.g., unavailable models)

        Returns:
            Tuple of (selected_arm_index, ucb_score)
        """
        context = np.array(context).flatten()
        if len(context) != self.context_dim:
            # Pad or truncate context to match expected dimension
            if len(context) < self.context_dim:
                context = np.pad(context, (0, self.context_dim - len(context)))
            else:
                context = context[:self.context_dim]

        exclude = set(exclude_arms or [])
        best_arm = 0
        best_ucb = -np.inf

        for arm in range(self.n_arms):
            if arm in exclude:
                continue

            # Compute UCB: theta^T * context + alpha * sqrt(context^T * A^{-1} * context)
            try:
                A_inv = np.linalg.inv(self._A[arm])
            except np.linalg.LinAlgError:
                A_inv = np.eye(self.context_dim) * 0.01

            theta = self._theta[arm]
            expected_reward = theta @ context
            confidence = self.alpha * np.sqrt(context @ A_inv @ context)
            ucb = expected_reward + confidence

            if ucb > best_ucb:
                best_ucb = ucb
                best_arm = arm

        return best_arm, float(best_ucb)

    def update(
        self,
        arm: int,
        context: np.ndarray,
        reward: float,
    ) -> None:
        """
        Update the model with observed reward for the selected arm.

        Args:
            arm: Selected arm index
            context: Context feature vector
            reward: Observed reward (e.g., CLV percentage)
        """
        context = np.array(context).flatten()
        if len(context) != self.context_dim:
            if len(context) < self.context_dim:
                context = np.pad(context, (0, self.context_dim - len(context)))
            else:
                context = context[:self.context_dim]

        # Apply decay to old observations (forgetting mechanism)
        if self.decay_factor < 1.0:
            self._A[arm] *= self.decay_factor
            self._b[arm] *= self.decay_factor

        # Update A and b
        self._A[arm] += np.outer(context, context)
        self._b[arm] += reward * context

        # Recompute theta
        try:
            self._theta[arm] = np.linalg.solve(self._A[arm], self._b[arm])
        except np.linalg.LinAlgError:
            self._theta[arm] = np.linalg.lstsq(self._A[arm], self._b[arm], rcond=None)[0]

        # Track statistics
        self._arm_counts[arm] += 1
        self._arm_rewards[arm].append(reward)
        self._total_updates += 1
        self._last_update_time = time.time()

    def batch_update(
        self,
        arms: List[int],
        contexts: np.ndarray,
        rewards: List[float],
    ) -> None:
        """Update with a batch of observations."""
        for arm, ctx, reward in zip(arms, contexts, rewards):
            self.update(arm, ctx, reward)

    def get_weights(self, context: np.ndarray) -> np.ndarray:
        """
        Get the expected reward (weight) for each arm given a context.

        Useful for weighted ensemble predictions instead of hard arm selection.
        """
        context = np.array(context).flatten()
        if len(context) != self.context_dim:
            if len(context) < self.context_dim:
                context = np.pad(context, (0, self.context_dim - len(context)))
            else:
                context = context[:self.context_dim]

        weights = np.array([theta @ context for theta in self._theta])

        # Convert to probabilities via softmax
        exp_weights = np.exp(weights - np.max(weights))  # Numerical stability
        probs = exp_weights / exp_weights.sum()

        return probs

    def predict_weighted(
        self,
        context: np.ndarray,
        model_predictions: np.ndarray,
    ) -> float:
        """
        Make a weighted ensemble prediction using bandit-learned weights.

        Args:
            context: Context feature vector
            model_predictions: Array of predictions from each model

        Returns:
            Weighted prediction
        """
        weights = self.get_weights(context)
        return float(np.dot(weights, model_predictions))

    @property
    def status(self) -> Dict[str, Any]:
        """Get current bandit status."""
        avg_rewards = []
        for arm in range(self.n_arms):
            if self._arm_rewards[arm]:
                avg_rewards.append(round(float(np.mean(self._arm_rewards[arm][-100:])), 4))
            else:
                avg_rewards.append(0.0)

        return {
            "n_arms": self.n_arms,
            "arm_names": self.arm_names,
            "arm_counts": self._arm_counts.tolist(),
            "avg_rewards": avg_rewards,
            "total_updates": self._total_updates,
            "alpha": self.alpha,
            "decay_factor": self.decay_factor,
            "last_update": self._last_update_time,
        }

    def save(self, path: str) -> None:
        """Save bandit state to disk using joblib + SHA-256."""
        from src.ml.safe_io import safe_save
        state = {
            "n_arms": self.n_arms,
            "context_dim": self.context_dim,
            "alpha": self.alpha,
            "arm_names": self.arm_names,
            "decay_factor": self.decay_factor,
            "A": [a.tolist() for a in self._A],
            "b": [b.tolist() for b in self._b],
            "theta": [t.tolist() for t in self._theta],
            "arm_counts": self._arm_counts.tolist(),
            "total_updates": self._total_updates,
        }
        safe_save(state, path)
        logger.info("LinUCB bandit saved to %s", path)

    def load(self, path: str) -> LinUCBEnsemble:
        """Load bandit state from disk using joblib + SHA-256."""
        from src.ml.safe_io import safe_load
        state = safe_load(path)

        self.n_arms = state["n_arms"]
        self.context_dim = state["context_dim"]
        self.alpha = state["alpha"]
        self.arm_names = state["arm_names"]
        self.decay_factor = state.get("decay_factor", 0.995)
        self._A = [np.array(a) for a in state["A"]]
        self._b = [np.array(b) for b in state["b"]]
        self._theta = [np.array(t) for t in state["theta"]]
        self._arm_counts = np.array(state["arm_counts"])
        self._total_updates = state["total_updates"]

        logger.info("LinUCB bandit loaded from %s (%d updates)", path, self._total_updates)
        return self
