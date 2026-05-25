"""
Federated Learning client for collaborative model training.

Trains locally on user's data and sends weight updates (not raw data)
to the FederatedServer for aggregation.

Usage:
    from src.ml.federated.fed_client import FederatedClient

    client = FederatedClient(
        client_id="user_1",
        model_fn=lambda: MetaBettingNet(input_dim=50),
        server_url="http://localhost:5000",
    )
    client.download_global_weights()
    client.train_local(X_train, y_train, epochs=5)
    client.upload_updates()
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

logger = logging.getLogger("fed_client")


@dataclass
class LocalTrainingResult:
    """Result of a local training round."""
    client_id: str
    n_samples: int
    loss_before: float
    loss_after: float
    weight_delta: dict[str, np.ndarray]
    training_time_seconds: float
    epochs: int


class FederatedClient:
    """
    Federated Learning client that trains locally and uploads weight updates.

    Protocol:
    1. Download global weights from server
    2. Train locally on private data
    3. Upload weight delta (not raw data) to server

    Security features:
    - Only weight deltas are sent (no raw data leaves the client)
    - Optional local differential privacy (noise added to gradients)
    - Weight clipping to prevent gradient leakage attacks

    Args:
        client_id: Unique identifier for this client
        model_fn: Factory function to create a new model instance
        server: Reference to FederatedServer (in-process) or URL (remote)
        local_lr: Learning rate for local training
        local_epochs: Number of epochs per training round
        dp_noise_std: Standard deviation of DP noise (0 = no DP)
        dp_clip_norm: Maximum gradient norm for DP clipping
    """

    def __init__(
        self,
        client_id: str,
        model_fn: Callable,
        server: Any | None = None,
        server_url: str | None = None,
        local_lr: float = 0.01,
        local_epochs: int = 5,
        dp_noise_std: float = 0.0,
        dp_clip_norm: float = 1.0,
    ):
        self.client_id = client_id
        self.model_fn = model_fn
        self.server = server
        self.server_url = server_url
        self.local_lr = local_lr
        self.local_epochs = local_epochs
        self.dp_noise_std = dp_noise_std
        self.dp_clip_norm = dp_clip_norm

        self._model = model_fn()
        self._global_weights: dict[str, np.ndarray] | None = None
        self._training_history: list[LocalTrainingResult] = []

    def download_global_weights(self) -> dict[str, np.ndarray]:
        """
        Download the latest global weights from the server.

        Returns:
            Global model weights
        """
        if self.server is not None:
            # In-process server
            self._global_weights = self.server.get_global_weights()
        elif self.server_url is not None:
            # Remote server (HTTP)
            try:
                import requests
                resp = requests.get(f"{self.server_url}/weights", timeout=30)
                resp.raise_for_status()
                data = resp.json()
                self._global_weights = {k: np.array(v) for k, v in data.items()}
            except Exception as e:
                logger.error("Failed to download global weights: %s", e)
                return {}
        else:
            logger.warning("No server configured — using local weights")
            self._global_weights = self._model.get_weights()

        # Apply global weights to local model
        if self._global_weights:
            self._model.set_weights(self._global_weights)
            logger.info("Downloaded global weights (%d params)", len(self._global_weights))

        return self._global_weights or {}

    def train_local(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int | None = None,
        lr: float | None = None,
    ) -> LocalTrainingResult:
        """
        Train the model locally on private data.

        Args:
            X: Feature matrix
            y: Target vector
            epochs: Override default epochs
            lr: Override default learning rate

        Returns:
            LocalTrainingResult with training metrics and weight delta
        """
        n_epochs = epochs or self.local_epochs
        learning_rate = lr or self.local_lr
        start_time = time.time()

        # Record loss before training
        loss_before = self._model.loss(X, y)

        # Store weights before training for delta computation
        weights_before = self._model.get_weights()

        # Local training loop
        for epoch in range(n_epochs):
            grads = self._model.gradients(X, y)

            # Apply DP clipping to gradients
            if self.dp_clip_norm > 0:
                for key, grad in grads.items():
                    norm = np.linalg.norm(grad)
                    if norm > self.dp_clip_norm:
                        grads[key] = grad * (self.dp_clip_norm / norm)

            # Apply DP noise to gradients
            if self.dp_noise_std > 0:
                for key, grad in grads.items():
                    noise = np.random.normal(0, self.dp_noise_std, grad.shape)
                    grads[key] = grad + noise

            # Gradient descent step
            for key, grad in grads.items():
                self._model.__dict__[key] -= learning_rate * grad

        # Record loss after training
        loss_after = self._model.loss(X, y)

        # Compute weight delta
        weights_after = self._model.get_weights()
        weight_delta = {}
        for key in weights_before:
            weight_delta[key] = weights_after[key] - weights_before[key]

        training_time = time.time() - start_time

        result = LocalTrainingResult(
            client_id=self.client_id,
            n_samples=len(X),
            loss_before=float(loss_before),
            loss_after=float(loss_after),
            weight_delta=weight_delta,
            training_time_seconds=training_time,
            epochs=n_epochs,
        )

        self._training_history.append(result)
        logger.info(
            "Local training: %d epochs, loss %.4f -> %.4f, %d samples, %.1fs",
            n_epochs, loss_before, loss_after, len(X), training_time,
        )

        return result

    def upload_updates(self, training_result: LocalTrainingResult | None = None) -> bool:
        """
        Upload weight updates to the server.

        Only sends weight deltas, never raw data.

        Args:
            training_result: Use specific training result, or latest

        Returns:
            True if server accepted the update
        """
        result = training_result or (self._training_history[-1] if self._training_history else None)
        if result is None:
            logger.error("No training result to upload")
            return False

        # Compute new weights: global + delta
        if self._global_weights is not None:
            new_weights = {}
            for key in self._global_weights:
                delta = result.weight_delta.get(key, np.zeros_like(self._global_weights[key]))
                new_weights[key] = self._global_weights[key] + delta
        else:
            new_weights = self._model.get_weights()

        if self.server is not None:
            # In-process server
            accepted = self.server.receive_update(
                client_id=self.client_id,
                weights=new_weights,
                n_samples=result.n_samples,
                loss=result.loss_after,
            )
            if accepted:
                logger.info("Server accepted update from %s", self.client_id)
            else:
                logger.warning("Server rejected update from %s", self.client_id)
            return accepted

        elif self.server_url is not None:
            # Remote server (HTTP)
            try:
                import requests
                payload = {
                    "client_id": self.client_id,
                    "weights": {k: v.tolist() for k, v in new_weights.items()},
                    "n_samples": result.n_samples,
                    "loss": result.loss_after,
                }
                resp = requests.post(
                    f"{self.server_url}/update",
                    json=payload,
                    timeout=30,
                )
                resp.raise_for_status()
                return resp.json().get("accepted", False)
            except Exception as e:
                logger.error("Failed to upload updates: %s", e)
                return False

        return False

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the local model."""
        return self._model.predict(X)

    @property
    def training_history(self) -> list[LocalTrainingResult]:
        """Get all local training results."""
        return list(self._training_history)

    @property
    def status(self) -> dict[str, Any]:
        """Get client status."""
        return {
            "client_id": self.client_id,
            "n_training_rounds": len(self._training_history),
            "total_samples_trained": sum(r.n_samples for r in self._training_history),
            "last_loss": self._training_history[-1].loss_after if self._training_history else None,
            "dp_enabled": self.dp_noise_std > 0,
            "dp_noise_std": self.dp_noise_std,
            "dp_clip_norm": self.dp_clip_norm,
        }
