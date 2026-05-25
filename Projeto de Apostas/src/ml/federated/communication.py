"""
Federated Learning communication protocol.

Provides both in-process (direct) and HTTP-based communication between
FederatedClient and FederatedServer. The HTTP server can be deployed
as a lightweight REST API for multi-user federated training.

Usage (in-process):
    server = FederatedServer(model_fn)
    client = FederatedClient(client_id="u1", model_fn=model_fn, server=server)

Usage (HTTP):
    # Start server
    python -m src.ml.federated.communication --port 5000

    # Connect client
    client = FederatedClient(client_id="u1", model_fn=model_fn, server_url="http://localhost:5000")
"""
from __future__ import annotations

import logging
from typing import Any, Callable

import numpy as np

from src.ml.federated.fed_server import FederatedServer

logger = logging.getLogger("fed_communication")


class FederatedCommunication:
    """
    Communication layer for federated learning.

    Wraps a FederatedServer with a REST API for remote client access,
    or provides direct in-process communication.

    REST endpoints:
    - GET  /weights          → Get global model weights
    - POST /update           → Submit client weight update
    - GET  /status           → Get server status
    - POST /aggregate        → Trigger aggregation round
    - GET  /round-result     → Get latest round result
    """

    def __init__(
        self,
        server: FederatedServer,
        host: str = "0.0.0.0",
        port: int = 5000,
        auth_token: str | None = None,
    ):
        self.server = server
        self.host = host
        self.port = port
        self.auth_token = auth_token
        self._app = None

    def _build_app(self):
        """Build the FastAPI application."""
        try:
            from fastapi import FastAPI, Header, HTTPException
            from fastapi.responses import JSONResponse
        except ImportError:
            raise ImportError("FastAPI required for HTTP communication. Install: pip install fastapi uvicorn")

        app = FastAPI(title="VBQ Federated Learning Server")
        server = self.server
        auth_token = self.auth_token

        def verify_auth(authorization: str = Header(default="")):
            if auth_token and authorization != f"Bearer {auth_token}":
                raise HTTPException(status_code=401, detail="Invalid auth token")

        @app.get("/weights")
        async def get_weights():
            """Get current global model weights."""
            weights = server.get_global_weights()
            # Convert numpy arrays to lists for JSON serialization
            serializable = {k: v.tolist() for k, v in weights.items()}
            return JSONResponse(serializable)

        @app.post("/update")
        async def receive_update(payload: dict[str, Any]):
            """Receive a weight update from a client."""
            client_id = payload.get("client_id", "unknown")
            weights_raw = payload.get("weights", {})
            n_samples = payload.get("n_samples", 0)
            loss = payload.get("loss", 0.0)

            # Deserialize weights
            weights = {k: np.array(v) for k, v in weights_raw.items()}

            accepted = server.receive_update(
                client_id=client_id,
                weights=weights,
                n_samples=n_samples,
                loss=loss,
            )

            return JSONResponse({"accepted": accepted, "client_id": client_id})

        @app.get("/status")
        async def get_status():
            """Get server status."""
            return JSONResponse(server.status)

        @app.post("/aggregate")
        async def trigger_aggregation():
            """Trigger an aggregation round."""
            result = server.aggregate()
            return JSONResponse({
                "round_number": result.round_number,
                "n_clients": result.n_clients,
                "total_samples": result.total_samples,
                "avg_loss": result.avg_loss,
            })

        @app.get("/round-result")
        async def get_round_result():
            """Get latest round result."""
            if server._round_history:
                latest = server._round_history[-1]
                return JSONResponse({
                    "round_number": latest.round_number,
                    "n_clients": latest.n_clients,
                    "total_samples": latest.total_samples,
                    "avg_loss": latest.avg_loss,
                })
            return JSONResponse({"status": "no_rounds_yet"})

        self._app = app
        return app

    def run(self) -> None:
        """Start the HTTP server."""
        if self._app is None:
            self._build_app()

        try:
            import uvicorn
            logger.info("Starting federated server on %s:%d", self.host, self.port)
            uvicorn.run(self._app, host=self.host, port=self.port)
        except ImportError:
            raise ImportError("uvicorn required for HTTP server. Install: pip install uvicorn")

    @property
    def app(self):
        """Get the FastAPI app (for testing or custom deployment)."""
        if self._app is None:
            self._build_app()
        return self._app


def run_standalone_federated_round(
    model_fn: Callable,
    client_data: dict[str, tuple],
    n_rounds: int = 5,
) -> dict[str, Any]:
    """
    Run a standalone federated training round without HTTP.

    Useful for testing and single-machine federated simulation.

    Args:
        model_fn: Factory function to create model instances
        client_data: Dict of client_id -> (X, y) training data
        n_rounds: Number of federated rounds

    Returns:
        Summary of all rounds
    """
    from src.ml.federated.fed_client import FederatedClient

    server = FederatedServer(model_fn, min_clients_per_round=1)
    server.initialize()

    clients = {
        cid: FederatedClient(
            client_id=cid,
            model_fn=model_fn,
            server=server,
            local_epochs=3,
        )
        for cid in client_data
    }

    round_results = []

    for round_num in range(n_rounds):
        logger.info("=== Federated Round %d/%d ===", round_num + 1, n_rounds)

        # Each client: download, train, upload
        for cid, client in clients.items():
            X, y = client_data[cid]
            client.download_global_weights()
            result = client.train_local(X, y)
            client.upload_updates(result)

        # Server aggregates
        round_result = server.aggregate()
        round_results.append({
            "round": round_num + 1,
            "n_clients": round_result.n_clients,
            "avg_loss": round_result.avg_loss,
        })
        logger.info(
            "Round %d: %d clients, avg_loss=%.4f",
            round_num + 1, round_result.n_clients, round_result.avg_loss,
        )

    return {
        "n_rounds": n_rounds,
        "n_clients": len(clients),
        "rounds": round_results,
        "final_weights_norm": float(np.mean([
            np.linalg.norm(w) for w in server.get_global_weights().values()
        ])),
    }
