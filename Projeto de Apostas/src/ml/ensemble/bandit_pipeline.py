"""
Bandit-driven ensemble pipeline for dynamic model selection in betting.

Integrates the LinUCB contextual bandit into the full betting pipeline,
dynamically selecting which model to use for each betting opportunity
based on context features (regime, liquidity, volatility, time-to-kickoff).

The bandit learns which model maximizes CLV for each context, balancing
exploration of under-used models with exploitation of known performers.

Usage:
    from src.ml.ensemble.bandit_pipeline import BanditEnsemblePipeline

    pipeline = BanditEnsemblePipeline(
        models={"xgb": xgb_model, "lgbm": lgbm_model},
        context_dim=10,
        alpha=1.0,
    )

    # Register models with their prediction functions
    pipeline.register_model("xgb", xgb_model, predict_fn=lambda m, x: m.predict_proba(x)[:, 1])
    pipeline.register_model("lgbm", lgbm_model, predict_fn=lambda m, x: m.predict(x))

    # Build context from raw features
    context = pipeline.build_context(
        event_features=np.array([1.5, 2.0, 0.8]),
        regime="normal",
        liquidity=0.85,
        volatility=0.12,
        time_to_kickoff=3.5,
    )

    # Select best model and get prediction
    model_name, prediction, weights = pipeline.predict(features, context)

    # After bet settles, update bandit with CLV reward
    pipeline.update_with_reward(model_name, context, reward=0.03)

    # Weighted ensemble prediction (soft selection)
    weighted_pred = pipeline.auto_weighted_predict(features, context)

    # Inspect state
    status = pipeline.status
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Tuple

import numpy as np

from src.ml.ensemble.contextual_bandit import LinUCBEnsemble

logger = logging.getLogger("bandit_pipeline")

# Regime string to numeric mapping
REGIME_MAP: Dict[str, float] = {
    "low_vol": 0.0,
    "normal": 0.5,
    "high_vol": 1.0,
}


class BanditEnsemblePipeline:
    """
    Pipeline that integrates LinUCB contextual bandit for dynamic model
    selection in the betting workflow.

    Each registered model is an "arm" of the bandit. For every betting
    opportunity the pipeline:
      1. Builds a context vector from raw event features and market state.
      2. Asks the bandit which model (arm) to use.
      3. Returns the selected model's prediction along with bandit weights.
      4. After the bet settles, updates the bandit with the observed CLV reward.

    The bandit continuously learns which model performs best under each
    market regime, automatically adapting to changing conditions without
    requiring a full retrain of the ensemble.

    Args:
        models: Dictionary mapping model names to model objects.
        context_dim: Dimension of the context feature vector passed to the bandit.
        alpha: Exploration parameter for LinUCB (higher = more exploration).
        decay_factor: Exponential decay for old observations (0.995 = slow decay).

    Example:
        >>> pipeline = BanditEnsemblePipeline(
        ...     models={"xgb": xgb_model, "lgbm": lgbm_model},
        ...     context_dim=10,
        ...     alpha=1.0,
        ... )
        >>> pipeline.register_model("xgb", xgb_model, lambda m, x: m.predict(x))
        >>> context = pipeline.build_context(np.zeros(5), "normal", 0.9, 0.1, 2.0)
        >>> name, pred, weights = pipeline.predict(np.ones(20), context)
    """

    def __init__(
        self,
        models: Dict[str, Any],
        context_dim: int = 10,
        alpha: float = 1.0,
        decay_factor: float = 0.995,
    ) -> None:
        self._models: Dict[str, Any] = dict(models)
        self._predict_fns: Dict[str, Callable] = {}
        self._context_dim = context_dim

        # Build initial arm names from model keys
        arm_names = list(self._models.keys())

        self._bandit = LinUCBEnsemble(
            n_arms=len(arm_names),
            context_dim=context_dim,
            alpha=alpha,
            arm_names=arm_names,
            decay_factor=decay_factor,
        )

        # Mapping from model name to arm index and vice-versa
        self._name_to_arm: Dict[str, int] = {
            name: idx for idx, name in enumerate(arm_names)
        }
        self._arm_to_name: Dict[int, str] = {
            idx: name for idx, name in enumerate(arm_names)
        }

        # Default predict_fn: call model.predict() directly
        for name, model in self._models.items():
            self._predict_fns[name] = lambda m=model: None  # placeholder

        logger.info(
            "BanditEnsemblePipeline initialised with %d model(s): %s",
            len(arm_names),
            arm_names,
        )

    # ------------------------------------------------------------------
    # Model registration
    # ------------------------------------------------------------------

    def register_model(
        self,
        name: str,
        model: Any,
        predict_fn: Callable,
    ) -> None:
        """
        Register a model with its prediction function.

        If the model name already exists, its entry is updated in-place.
        If it is new, a new arm is added to the bandit.

        Args:
            name: Unique identifier for the model (e.g. "xgb_v2").
            model: The model object itself.
            predict_fn: A callable with signature ``predict_fn(model, features) -> float``
                        that produces a scalar prediction from the model.

        Example:
            >>> pipeline.register_model(
            ...     "xgb",
            ...     xgb_model,
            ...     predict_fn=lambda m, x: m.predict_proba(x)[:, 1],
            ... )
        """
        self._models[name] = model
        self._predict_fns[name] = predict_fn

        if name in self._name_to_arm:
            # Existing arm -- just refresh the references
            logger.debug("Updated existing model arm: %s", name)
        else:
            # New arm -- rebuild the bandit with the additional arm
            self._rebuild_bandit()
            logger.info("Registered new model arm: %s (total: %d)", name, len(self._models))

    def _rebuild_bandit(self) -> None:
        """Rebuild the underlying LinUCB bandit when arms change."""
        arm_names = list(self._models.keys())
        old_bandit = self._bandit

        self._bandit = LinUCBEnsemble(
            n_arms=len(arm_names),
            context_dim=self._context_dim,
            alpha=old_bandit.alpha,
            arm_names=arm_names,
            decay_factor=old_bandit.decay_factor,
        )

        self._name_to_arm = {name: idx for idx, name in enumerate(arm_names)}
        self._arm_to_name = {idx: name for idx, name in enumerate(arm_names)}

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(
        self,
        features: np.ndarray,
        context: np.ndarray,
    ) -> Tuple[str, float, np.ndarray]:
        """
        Select the best model for the given context and return its prediction.

        The bandit selects the arm (model) with the highest upper confidence
        bound, balancing exploitation of known good models with exploration
        of under-used ones.

        Args:
            features: Feature vector passed to the selected model's predict_fn.
            context: Context feature vector (shape: context_dim,) used by the
                     bandit to decide which model to select.

        Returns:
            Tuple of:
              - selected_model_name (str): Name of the chosen model.
              - prediction (float): Scalar prediction from the chosen model.
              - weights (np.ndarray): Softmax weights over all arms for this context.

        Raises:
            RuntimeError: If no models have been registered.

        Example:
            >>> name, pred, weights = pipeline.predict(features, context)
            >>> print(f"Using {name}, prediction={pred:.4f}")
        """
        if not self._models:
            raise RuntimeError(
                "No models registered in BanditEnsemblePipeline. "
                "Call register_model() before predict()."
            )

        arm_idx, ucb_score = self._bandit.select(context)
        model_name = self._arm_to_name[arm_idx]

        # Get the prediction from the selected model
        predict_fn = self._predict_fns.get(model_name)
        if predict_fn is None:
            prediction = float(self._models[model_name].predict(features))
        else:
            prediction = float(predict_fn(self._models[model_name], features))

        # Get softmax weights for all arms (useful for diagnostics)
        weights = self._bandit.get_weights(context)

        logger.debug(
            "Selected model=%s (arm=%d, ucb=%.4f), prediction=%.4f",
            model_name,
            arm_idx,
            ucb_score,
            prediction,
        )

        return model_name, prediction, weights

    def auto_weighted_predict(
        self,
        features: np.ndarray,
        context: np.ndarray,
    ) -> float:
        """
        Produce a weighted ensemble prediction using bandit-learned weights.

        Instead of selecting a single model (hard selection), this method
        computes a weighted average of all model predictions, where the
        weights are derived from the bandit's expected reward estimates
        via a softmax transformation.

        This is useful when you want a more stable prediction that
        incorporates information from all models rather than relying
        on a single one.

        Args:
            features: Feature vector passed to each model's predict_fn.
            context: Context feature vector for the bandit.

        Returns:
            Weighted prediction (float) combining all models.

        Raises:
            RuntimeError: If no models have been registered.

        Example:
            >>> weighted_pred = pipeline.auto_weighted_predict(features, context)
        """
        if not self._models:
            raise RuntimeError(
                "No models registered in BanditEnsemblePipeline. "
                "Call register_model() before auto_weighted_predict()."
            )

        weights = self._bandit.get_weights(context)

        # Collect predictions from every model
        predictions = np.zeros(len(self._models))
        for idx, name in enumerate(self._arm_to_name.values()):
            predict_fn = self._predict_fns.get(name)
            if predict_fn is None:
                predictions[idx] = float(self._models[name].predict(features))
            else:
                predictions[idx] = float(predict_fn(self._models[name], features))

        weighted_prediction = float(np.dot(weights, predictions))

        logger.debug(
            "Auto-weighted prediction=%.4f (weights=%s)",
            weighted_prediction,
            np.round(weights, 3).tolist(),
        )

        return weighted_prediction

    # ------------------------------------------------------------------
    # Reward update
    # ------------------------------------------------------------------

    def update_with_reward(
        self,
        model_name: str,
        context: np.ndarray,
        reward: float,
    ) -> None:
        """
        Update the bandit after observing the CLV reward for a selected model.

        This is the feedback loop that allows the bandit to learn which
        model performs best under each context. Call this after each bet
        settles and the CLV (Closing Line Value) is known.

        Args:
            model_name: Name of the model that was used for the bet.
            context: Context feature vector that was used when the bet was placed.
            reward: Observed CLV reward (e.g., 0.03 for +3% CLV).

        Raises:
            KeyError: If model_name is not registered.

        Example:
            >>> pipeline.update_with_reward("xgb", context, reward=0.03)
        """
        if model_name not in self._name_to_arm:
            raise KeyError(
                f"Model '{model_name}' is not registered. "
                f"Available models: {list(self._name_to_arm.keys())}"
            )

        arm_idx = self._name_to_arm[model_name]
        self._bandit.update(arm_idx, context, reward)

        logger.debug(
            "Updated bandit: model=%s (arm=%d), reward=%.4f",
            model_name,
            arm_idx,
            reward,
        )

    # ------------------------------------------------------------------
    # Context building
    # ------------------------------------------------------------------

    def build_context(
        self,
        event_features: np.ndarray,
        regime: str,
        liquidity: float,
        volatility: float,
        time_to_kickoff: float,
    ) -> np.ndarray:
        """
        Build a context vector from raw event and market features.

        The context vector is what the bandit uses to differentiate between
        betting situations. It combines:
          - Event features (e.g., team strength, form) -- padded or truncated
          - Market regime (mapped from string to numeric)
          - Liquidity (0-1 scale)
          - Volatility (0-1 scale)
          - Time to kickoff (in hours)

        The final vector is padded or truncated to ``context_dim``.

        Args:
            event_features: Raw event feature vector (e.g., team stats).
            regime: Market regime string. One of "low_vol", "normal", "high_vol".
            liquidity: Market liquidity in [0, 1] range.
            volatility: Market volatility in [0, 1] range.
            time_to_kickoff: Hours until kickoff.

        Returns:
            Context vector of shape (context_dim,).

        Example:
            >>> ctx = pipeline.build_context(
            ...     event_features=np.array([1.5, 2.0, 0.8]),
            ...     regime="normal",
            ...     liquidity=0.85,
            ...     volatility=0.12,
            ...     time_to_kickoff=3.5,
            ... )
        """
        event_features = np.asarray(event_features, dtype=np.float64).flatten()

        # Map regime string to numeric value
        regime_value = REGIME_MAP.get(regime, 0.5)  # default to "normal" if unknown

        # Compose the raw context: event features + market metadata
        market_meta = np.array([regime_value, liquidity, volatility, time_to_kickoff])
        raw_context = np.concatenate([event_features, market_meta])

        # Pad or truncate to context_dim
        if len(raw_context) < self._context_dim:
            context = np.pad(raw_context, (0, self._context_dim - len(raw_context)))
        elif len(raw_context) > self._context_dim:
            context = raw_context[: self._context_dim]
        else:
            context = raw_context

        return context

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def get_model_rankings(
        self,
        context: np.ndarray,
    ) -> List[Tuple[str, float]]:
        """
        Rank models by their expected reward for the given context.

        Returns models sorted from highest to lowest expected reward
        (theta^T * context, without the exploration bonus). Useful for
        diagnostics and understanding which models the bandit prefers
        under specific conditions.

        Args:
            context: Context feature vector.

        Returns:
            List of (model_name, expected_reward) tuples sorted descending.

        Example:
            >>> rankings = pipeline.get_model_rankings(context)
            >>> for name, reward in rankings:
            ...     print(f"{name}: expected_reward={reward:.4f}")
        """
        context = np.asarray(context, dtype=np.float64).flatten()
        if len(context) != self._context_dim:
            if len(context) < self._context_dim:
                context = np.pad(context, (0, self._context_dim - len(context)))
            else:
                context = context[: self._context_dim]

        rankings: List[Tuple[str, float]] = []
        for arm_idx in range(self._bandit.n_arms):
            theta = self._bandit._theta[arm_idx]
            expected_reward = float(theta @ context)
            model_name = self._arm_to_name[arm_idx]
            rankings.append((model_name, expected_reward))

        # Sort by expected reward descending
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings

    @property
    def status(self) -> Dict[str, Any]:
        """
        Return the current bandit status combined with model statistics.

        Includes:
          - Bandit-level info (arm counts, average rewards, alpha, decay)
          - Per-model registration info

        Returns:
            Dictionary with bandit and model status.

        Example:
            >>> status = pipeline.status
            >>> print(status["bandit"]["arm_counts"])
        """
        bandit_status = self._bandit.status

        model_info: Dict[str, Any] = {}
        for name, model in self._models.items():
            arm_idx = self._name_to_arm[name]
            model_info[name] = {
                "arm_index": arm_idx,
                "has_predict_fn": name in self._predict_fns and self._predict_fns[name] is not None,
                "selection_count": int(bandit_status["arm_counts"][arm_idx]),
                "avg_reward": float(bandit_status["avg_rewards"][arm_idx]),
            }

        return {
            "bandit": bandit_status,
            "models": model_info,
            "n_registered": len(self._models),
            "context_dim": self._context_dim,
        }
