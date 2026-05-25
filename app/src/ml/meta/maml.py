"""
MAML (Model-Agnostic Meta-Learning) for fast adaptation to new sports.

Pre-trains a neural network across multiple sports (NBA, football, UFC)
using MAML's bilevel optimization. After meta-training, the model can
adapt to a new sport (tennis, esports) with just 20-30 games, reducing
launch time from months to days.

Inner loop: Task-specific gradient steps on support set.
Outer loop: Meta-gradient on query set across tasks.

Usage:
    from src.ml.meta.maml import MAMLTrainer

    trainer = MAMLTrainer(
        model_fn=lambda: BettingNet(input_dim=50),
        tasks=[football_data, nba_data, ufc_data],
    )
    trainer.meta_train(n_iterations=1000)

    # Adapt to new sport with few samples
    adapted = trainer.adapt(tennis_support_set, n_steps=5)
    preds = adapted.predict(X_tennis_test)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("maml")


# ---------------------------------------------------------------------------
# Simple neural network for meta-learning (pure NumPy)
# ---------------------------------------------------------------------------
class MetaBettingNet:
    """
    3-layer neural network for betting probability prediction.
    Supports MAML's fast gradient steps via manual weight copies.
    """

    def __init__(
        self,
        input_dim: int = 50,
        hidden_dim: int = 64,
        output_dim: int = 1,
    ):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

        # Xavier initialization
        s1 = np.sqrt(2.0 / (input_dim + hidden_dim))
        s2 = np.sqrt(2.0 / (hidden_dim + hidden_dim))
        s3 = np.sqrt(2.0 / (hidden_dim + output_dim))

        self.W1 = np.random.randn(input_dim, hidden_dim) * s1
        self.b1 = np.zeros(hidden_dim)
        self.W2 = np.random.randn(hidden_dim, hidden_dim) * s2
        self.b2 = np.zeros(hidden_dim)
        self.W3 = np.random.randn(hidden_dim, output_dim) * s3
        self.b3 = np.zeros(output_dim)

    def get_weights(self) -> Dict[str, np.ndarray]:
        """Return all weights as a dict (for MAML copy)."""
        return {
            "W1": self.W1.copy(), "b1": self.b1.copy(),
            "W2": self.W2.copy(), "b2": self.b2.copy(),
            "W3": self.W3.copy(), "b3": self.b3.copy(),
        }

    def set_weights(self, weights: Dict[str, np.ndarray]) -> None:
        """Set all weights from a dict."""
        self.W1 = weights["W1"].copy()
        self.b1 = weights["b1"].copy()
        self.W2 = weights["W2"].copy()
        self.b2 = weights["b2"].copy()
        self.W3 = weights["W3"].copy()
        self.b3 = weights["b3"].copy()

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Forward pass — returns probabilities via sigmoid."""
        h1 = np.maximum(0, X @ self.W1 + self.b1)  # ReLU
        h2 = np.maximum(0, h1 @ self.W2 + self.b2)  # ReLU
        logits = h2 @ self.W3 + self.b3
        return 1.0 / (1.0 + np.exp(-logits))  # Sigmoid

    def loss(self, X: np.ndarray, y: np.ndarray) -> float:
        """Binary cross-entropy loss."""
        preds = self.predict(X)
        preds = np.clip(preds, 1e-7, 1 - 1e-7)
        bce = -np.mean(y * np.log(preds) + (1 - y) * np.log(1 - preds))
        return bce

    def gradients(self, X: np.ndarray, y: np.ndarray) -> Dict[str, np.ndarray]:
        """Compute gradients via backpropagation."""
        n = len(X)
        h1 = np.maximum(0, X @ self.W1 + self.b1)
        h2 = np.maximum(0, h1 @ self.W2 + self.b2)
        logits = h2 @ self.W3 + self.b3
        preds = 1.0 / (1.0 + np.exp(-logits))

        # BCE gradient
        d_logits = (preds - y.reshape(-1, 1)) / n

        # Layer 3
        grad_W3 = h2.T @ d_logits
        grad_b3 = d_logits.sum(axis=0)

        # Layer 2
        d_h2 = d_logits @ self.W3.T
        d_h2[h2 <= 0] = 0  # ReLU
        grad_W2 = h1.T @ d_h2
        grad_b2 = d_h2.sum(axis=0)

        # Layer 1
        d_h1 = d_h2 @ self.W2.T
        d_h1[h1 <= 0] = 0  # ReLU
        grad_W1 = X.T @ d_h1
        grad_b1 = d_h1.sum(axis=0)

        return {
            "W1": grad_W1, "b1": grad_b1,
            "W2": grad_W2, "b2": grad_b2,
            "W3": grad_W3, "b3": grad_b3,
        }


# ---------------------------------------------------------------------------
# Task definition
# ---------------------------------------------------------------------------
@dataclass
class MetaTask:
    """A single meta-learning task (one sport)."""
    name: str
    X_support: np.ndarray  # Few-shot adaptation data
    y_support: np.ndarray
    X_query: np.ndarray    # Evaluation data
    y_query: np.ndarray
    odds_support: Optional[np.ndarray] = None
    odds_query: Optional[np.ndarray] = None


# ---------------------------------------------------------------------------
# MAML Trainer
# ---------------------------------------------------------------------------
class MAMLTrainer:
    """
    MAML trainer for cross-sport meta-learning.

    Inner loop: Adapt model to each task's support set with K gradient steps.
    Outer loop: Update meta-parameters to minimize query-set loss across tasks.

    After meta-training, the model can be adapted to a new sport with
    just 20-30 games (5-10 inner gradient steps).
    """

    def __init__(
        self,
        model_fn: Callable[[], MetaBettingNet],
        tasks: Optional[List[MetaTask]] = None,
        inner_lr: float = 0.01,
        outer_lr: float = 0.001,
        inner_steps: int = 5,
        meta_batch_size: int = 4,
    ):
        self.model_fn = model_fn
        self.tasks = tasks or []
        self.inner_lr = inner_lr
        self.outer_lr = outer_lr
        self.inner_steps = inner_steps
        self.meta_batch_size = meta_batch_size

        # Meta-model (shared initialisation)
        self.meta_model = model_fn()
        self._meta_history: List[Dict[str, float]] = []

    def add_task(self, task: MetaTask) -> None:
        """Add a meta-learning task."""
        self.tasks.append(task)
        logger.info("Added task '%s' (support=%d, query=%d)", task.name, len(task.X_support), len(task.X_query))

    def meta_train(
        self,
        n_iterations: int = 1000,
        eval_every: int = 100,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Run MAML meta-training.

        For each iteration:
        1. Sample batch of tasks
        2. For each task: inner-loop adapt on support set
        3. Compute meta-gradient on query set
        4. Update meta-parameters

        Returns:
            Training summary
        """
        if not self.tasks:
            raise ValueError("No tasks added. Use add_task() first.")

        best_meta_loss = np.inf

        for iteration in range(n_iterations):
            # Sample tasks
            batch_indices = np.random.choice(
                len(self.tasks),
                size=min(self.meta_batch_size, len(self.tasks)),
                replace=False,
            )

            meta_grads: Dict[str, np.ndarray] = {}
            meta_loss = 0.0

            for task_idx in batch_indices:
                task = self.tasks[task_idx]

                # Clone meta-model for inner loop
                task_model = self.model_fn()
                task_model.set_weights(self.meta_model.get_weights())

                # Inner loop: adapt on support set
                for _ in range(self.inner_steps):
                    grads = task_model.gradients(task.X_support, task.y_support)
                    for key, grad in grads.items():
                        task_model.__dict__[key] -= self.inner_lr * grad

                # Query loss (this is what meta-learning optimises)
                query_loss = task_model.loss(task.X_query, task.y_query)
                meta_loss += query_loss

                # Compute meta-gradients (through the inner loop)
                query_grads = task_model.gradients(task.X_query, task.y_query)
                for key, grad in query_grads.items():
                    if key not in meta_grads:
                        meta_grads[key] = np.zeros_like(self.meta_model.__dict__[key])
                    meta_grads[key] += grad

            # Average meta-gradients
            for key in meta_grads:
                meta_grads[key] /= len(batch_indices)

            meta_loss /= len(batch_indices)

            # Outer loop: update meta-parameters
            for key, grad in meta_grads.items():
                self.meta_model.__dict__[key] -= self.outer_lr * grad

            if meta_loss < best_meta_loss:
                best_meta_loss = meta_loss

            if verbose and (iteration + 1) % eval_every == 0:
                logger.info(
                    "Meta-iter %d/%d | Meta-loss: %.4f | Best: %.4f",
                    iteration + 1, n_iterations, meta_loss, best_meta_loss,
                )
                self._meta_history.append({
                    "iteration": iteration,
                    "meta_loss": float(meta_loss),
                    "best_meta_loss": float(best_meta_loss),
                })

        return {
            "n_iterations": n_iterations,
            "best_meta_loss": float(best_meta_loss),
            "final_meta_loss": float(meta_loss),
            "n_tasks": len(self.tasks),
            "history": self._meta_history,
        }

    def adapt(
        self,
        X_support: np.ndarray,
        y_support: np.ndarray,
        n_steps: Optional[int] = None,
        lr: Optional[float] = None,
    ) -> MetaBettingNet:
        """
        Adapt the meta-model to a new task with few samples.

        This is the key benefit of MAML: fast adaptation with few gradient steps.

        Args:
            X_support: Few-shot data (20-30 games)
            y_support: Labels
            n_steps: Number of adaptation steps (default: self.inner_steps)
            lr: Learning rate (default: self.inner_lr)

        Returns:
            Adapted model ready for prediction
        """
        adapted = self.model_fn()
        adapted.set_weights(self.meta_model.get_weights())

        steps = n_steps or self.inner_steps
        learning_rate = lr or self.inner_lr

        for step in range(steps):
            loss = adapted.loss(X_support, y_support)
            grads = adapted.gradients(X_support, y_support)
            for key, grad in grads.items():
                adapted.__dict__[key] -= learning_rate * grad

            if step % 2 == 0:
                logger.debug("Adapt step %d/%d | Loss: %.4f", step + 1, steps, loss)

        logger.info("Adapted model in %d steps (final loss: %.4f)", steps, loss)
        return adapted

    def evaluate_adaptation(
        self,
        X_support: np.ndarray,
        y_support: np.ndarray,
        X_query: np.ndarray,
        y_query: np.ndarray,
        n_steps_range: List[int] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate how quickly the meta-model adapts to a new task.
        Compares MAML adaptation vs random initialization.
        """
        if n_steps_range is None:
            n_steps_range = [1, 3, 5, 10, 20]

        results = {"maml": {}, "random": {}}

        for n_steps in n_steps_range:
            # MAML adaptation
            maml_model = self.adapt(X_support, y_support, n_steps=n_steps)
            maml_loss = maml_model.loss(X_query, y_query)
            results["maml"][n_steps] = float(maml_loss)

            # Random init baseline
            random_model = self.model_fn()
            for _ in range(n_steps):
                grads = random_model.gradients(X_support, y_support)
                for key, grad in grads.items():
                    random_model.__dict__[key] -= self.inner_lr * grad
            random_loss = random_model.loss(X_query, y_query)
            results["random"][n_steps] = float(random_loss)

        return results

    @property
    def status(self) -> Dict[str, Any]:
        """Get trainer status."""
        return {
            "n_tasks": len(self.tasks),
            "task_names": [t.name for t in self.tasks],
            "inner_lr": self.inner_lr,
            "outer_lr": self.outer_lr,
            "inner_steps": self.inner_steps,
            "meta_iterations": len(self._meta_history),
        }


# ---------------------------------------------------------------------------
# Sport-specific adapter layers for MAML
# ---------------------------------------------------------------------------
class SportAdapter:
    """
    Lightweight sport-specific adapter that sits on top of the meta-model.

    Instead of fine-tuning the entire network, the adapter adds a small
    linear layer that maps the meta-model's output to a sport-specific
    prediction. This is more parameter-efficient and reduces overfitting
    on the small adaptation set.

    Args:
        input_dim: Dimension of the meta-model's output (typically 1)
        hidden_dim: Adapter hidden dimension (small, e.g. 8)
        output_dim: Output dimension (1 for probability)
    """

    def __init__(self, input_dim: int = 1, hidden_dim: int = 8, output_dim: int = 1):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

        # Small adapter network
        s1 = np.sqrt(2.0 / (input_dim + hidden_dim))
        s2 = np.sqrt(2.0 / (hidden_dim + output_dim))
        self.W1 = np.random.randn(input_dim, hidden_dim) * s1
        self.b1 = np.zeros(hidden_dim)
        self.W2 = np.random.randn(hidden_dim, output_dim) * s2
        self.b2 = np.zeros(output_dim)

    def predict(self, meta_output: np.ndarray) -> np.ndarray:
        """Transform meta-model output through adapter."""
        h = np.maximum(0, meta_output @ self.W1 + self.b1)
        logits = h @ self.W2 + self.b2
        return 1.0 / (1.0 + np.exp(-logits))

    def adapt(self, meta_output: np.ndarray, y: np.ndarray, lr: float = 0.01, n_steps: int = 5) -> None:
        """Quick-adapt the adapter to sport-specific data."""
        for _ in range(n_steps):
            h = np.maximum(0, meta_output @ self.W1 + self.b1)
            logits = h @ self.W2 + self.b2
            preds = 1.0 / (1.0 + np.exp(-logits))
            preds = np.clip(preds, 1e-7, 1 - 1e-7)

            # BCE gradient
            d_logits = (preds - y.reshape(-1, 1)) / len(y)
            self.W2 -= lr * (h.T @ d_logits)
            self.b2 -= lr * d_logits.sum(axis=0)

            d_h = d_logits @ self.W2.T
            d_h[h <= 0] = 0
            self.W1 -= lr * (meta_output.T @ d_h)
            self.b1 -= lr * d_h.sum(axis=0)


class SportAwareMAMLTrainer(MAMLTrainer):
    """
    MAML trainer with sport-specific adapter support.

    After meta-training the shared backbone, each sport gets a lightweight
    adapter layer that can be fine-tuned with very few samples (5-10 games).
    This is more parameter-efficient than full fine-tuning and reduces
    overfitting on small adaptation sets.

    Usage:
        trainer = SportAwareMAMLTrainer(model_fn, tasks=[...])
        trainer.meta_train(n_iterations=1000)

        # Adapt to new sport with adapter
        adapted_model, adapter = trainer.adapt_with_adapter(
            X_support, y_support, sport="tennis", n_steps=5,
        )
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sport_adapters: Dict[str, SportAdapter] = {}

    def adapt_with_adapter(
        self,
        X_support: np.ndarray,
        y_support: np.ndarray,
        sport: str = "unknown",
        n_steps: int = 5,
        adapter_steps: int = 10,
    ) -> Tuple[MetaBettingNet, SportAdapter]:
        """
        Adapt meta-model to a new sport using backbone + adapter.

        1. Adapt the shared backbone with few gradient steps (MAML)
        2. Create a sport-specific adapter on top
        3. Fine-tune the adapter on the support set

        Returns:
            Tuple of (adapted backbone model, sport adapter)
        """
        # Step 1: MAML adaptation of backbone
        adapted = self.adapt(X_support, y_support, n_steps=n_steps)

        # Step 2: Create adapter
        adapter = SportAdapter(input_dim=1, hidden_dim=8, output_dim=1)

        # Step 3: Get backbone predictions and adapt the adapter
        meta_output = adapted.predict(X_support).reshape(-1, 1)
        adapter.adapt(meta_output, y_support, lr=0.01, n_steps=adapter_steps)

        # Cache adapter
        self._sport_adapters[sport] = adapter
        logger.info("Created adapter for %s (%d adaptation steps)", sport, adapter_steps)

        return adapted, adapter

    def predict_with_adapter(
        self,
        X: np.ndarray,
        sport: str,
    ) -> np.ndarray:
        """Predict using backbone + sport-specific adapter."""
        if sport not in self._sport_adapters:
            logger.warning("No adapter for sport '%s', using backbone only", sport)
            return self.meta_model.predict(X)

        backbone_pred = self.meta_model.predict(X).reshape(-1, 1)
        adapter = self._sport_adapters[sport]
        return adapter.predict(backbone_pred).flatten()

    @property
    def sport_adapters(self) -> Dict[str, SportAdapter]:
        """Get all registered sport adapters."""
        return dict(self._sport_adapters)
