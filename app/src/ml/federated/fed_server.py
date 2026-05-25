"""
Federated Learning server for collaborative multi-user model training.

Aggregates model updates (gradients or weight deltas) from multiple users
without sharing raw data. Enables a "collaborative betting fund" where
participants contribute model improvements without exposing their data.

Uses FedAvg (Federated Averaging) as the aggregation strategy.

Usage:
    from src.ml.federated.fed_server import FederatedServer

    server = FederatedServer(model_fn=lambda: MetaBettingNet(input_dim=50))
    server.initialize()

    # Each client sends weight updates
    server.receive_update(client_id="user_1", weights=client_weights, n_samples=500)
    server.receive_update(client_id="user_2", weights=client_weights, n_samples=300)

    # Aggregate and distribute new global model
    server.aggregate()
    global_weights = server.get_global_weights()
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np

logger = logging.getLogger("fed_server")


@dataclass
class ClientUpdate:
    """A single client's model update."""
    client_id: str
    weights: Dict[str, np.ndarray]
    n_samples: int
    timestamp: float = field(default_factory=time.time)
    loss: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoundResult:
    """Result of a federated aggregation round."""
    round_number: int
    n_clients: int
    total_samples: int
    avg_loss: float
    weight_norm: float
    timestamp: float = field(default_factory=time.time)


class FederatedServer:
    """
    Federated Learning server using FedAvg aggregation.

    Protocol:
    1. Server initializes global model
    2. Clients download global weights
    3. Clients train locally on their data
    4. Clients upload weight updates
    5. Server aggregates using weighted average (by sample count)
    6. Server distributes new global weights

    Security features:
    - Differential privacy: clips gradient norms and adds Gaussian noise
    - Secure aggregation: supports additive secret sharing (placeholder)
    - Staleness detection: rejects updates older than threshold
    """

    def __init__(
        self,
        model_fn: Callable,
        min_clients_per_round: int = 2,
        max_staleness_seconds: float = 3600.0,
        dp_clip_norm: float = 1.0,
        dp_noise_multiplier: float = 0.1,
        min_samples_per_client: int = 50,
    ):
        self.model_fn = model_fn
        self.min_clients = min_clients_per_round
        self.max_staleness = max_staleness_seconds
        self.dp_clip_norm = dp_clip_norm
        self.dp_noise_multiplier = dp_noise_multiplier
        self.min_samples = min_samples_per_client

        self._global_model = None
        self._pending_updates: Dict[str, ClientUpdate] = {}
        self._round_history: List[RoundResult] = []
        self._current_round = 0
        self._client_stats: Dict[str, Dict[str, Any]] = {}

    def initialize(self) -> None:
        """Initialize the global model."""
        self._global_model = self.model_fn()
        self._current_round = 0
        logger.info("Federated server initialized")

    def get_global_weights(self) -> Dict[str, np.ndarray]:
        """Get current global model weights."""
        if self._global_model is None:
            self.initialize()
        return self._global_model.get_weights()

    def receive_update(
        self,
        client_id: str,
        weights: Dict[str, np.ndarray],
        n_samples: int,
        loss: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Receive a model update from a client.

        Validates:
        - Minimum sample count
        - Weight shapes match global model
        - Update not stale

        Returns:
            True if update accepted, False if rejected
        """
        if n_samples < self.min_samples:
            logger.warning(
                "Rejecting update from %s: too few samples (%d < %d)",
                client_id, n_samples, self.min_samples,
            )
            return False

        # Validate weight shapes
        global_weights = self.get_global_weights()
        for key in global_weights:
            if key not in weights:
                logger.warning("Rejecting update from %s: missing key '%s'", client_id, key)
                return False
            if weights[key].shape != global_weights[key].shape:
                logger.warning(
                    "Rejecting update from %s: shape mismatch for '%s' (%s vs %s)",
                    client_id, key, weights[key].shape, global_weights[key].shape,
                )
                return False

        # Apply differential privacy: clip weight norms
        clipped_weights = self._clip_weights(weights)

        update = ClientUpdate(
            client_id=client_id,
            weights=clipped_weights,
            n_samples=n_samples,
            loss=loss,
            metadata=metadata or {},
        )

        self._pending_updates[client_id] = update

        # Track client stats
        if client_id not in self._client_stats:
            self._client_stats[client_id] = {"total_updates": 0, "total_samples": 0}
        self._client_stats[client_id]["total_updates"] += 1
        self._client_stats[client_id]["total_samples"] += n_samples

        logger.info("Received update from %s (%d samples, loss=%.4f)", client_id, n_samples, loss)
        return True

    def _clip_weights(self, weights: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Clip weight update norms for differential privacy."""
        clipped = {}
        for key, w in weights.items():
            norm = np.linalg.norm(w)
            if norm > self.dp_clip_norm:
                clipped[key] = w * (self.dp_clip_norm / norm)
            else:
                clipped[key] = w.copy()
        return clipped

    def _add_dp_noise(self, weights: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Add Gaussian noise for differential privacy."""
        noisy = {}
        for key, w in weights.items():
            noise = np.random.normal(0, self.dp_noise_multiplier * self.dp_clip_norm, w.shape)
            noisy[key] = w + noise
        return noisy

    def aggregate(self) -> RoundResult:
        """
        Aggregate client updates using FedAvg (weighted average by sample count).

        Returns:
            RoundResult with aggregation details
        """
        if self._global_model is None:
            self.initialize()

        # Filter stale updates
        now = time.time()
        valid_updates = {
            cid: upd for cid, upd in self._pending_updates.items()
            if (now - upd.timestamp) < self.max_staleness
        }

        if len(valid_updates) < self.min_clients:
            logger.warning(
                "Insufficient clients for aggregation: %d < %d",
                len(valid_updates), self.min_clients,
            )
            return RoundResult(
                round_number=self._current_round,
                n_clients=0, total_samples=0,
                avg_loss=0.0, weight_norm=0.0,
            )

        # FedAvg: weighted average by sample count
        total_samples = sum(u.n_samples for u in valid_updates.values())
        new_weights: Dict[str, np.ndarray] = {}

        for key in self._global_model.get_weights().keys():
            weighted_sum = np.zeros_like(self._global_model.__dict__[key])
            for upd in valid_updates.values():
                weight = upd.n_samples / total_samples
                weighted_sum += weight * upd.weights[key]
            new_weights[key] = weighted_sum

        # Add differential privacy noise
        new_weights = self._add_dp_noise(new_weights)

        # Update global model
        self._global_model.set_weights(new_weights)

        # Compute metrics
        avg_loss = float(np.mean([u.loss for u in valid_updates.values()]))
        weight_norm = float(np.mean([np.linalg.norm(w) for w in new_weights.values()]))

        result = RoundResult(
            round_number=self._current_round,
            n_clients=len(valid_updates),
            total_samples=total_samples,
            avg_loss=avg_loss,
            weight_norm=weight_norm,
        )

        self._round_history.append(result)
        self._pending_updates.clear()
        self._current_round += 1

        logger.info(
            "Round %d aggregated: %d clients, %d samples, avg_loss=%.4f",
            result.round_number, result.n_clients, result.total_samples, result.avg_loss,
        )

        return result

    def get_client_updates_count(self) -> int:
        """Number of pending client updates."""
        return len(self._pending_updates)

    def get_round_history(self, last_n: int = 10) -> List[RoundResult]:
        """Get last N round results."""
        return self._round_history[-last_n:]

    @property
    def status(self) -> Dict[str, Any]:
        """Get server status."""
        return {
            "current_round": self._current_round,
            "pending_updates": len(self._pending_updates),
            "total_rounds": len(self._round_history),
            "registered_clients": len(self._client_stats),
            "dp_clip_norm": self.dp_clip_norm,
            "dp_noise_multiplier": self.dp_noise_multiplier,
            "client_stats": dict(self._client_stats),
        }
