"""
Locust load tests for VBQ betting pipeline.

Simulates high-frequency betting traffic to verify system resilience
under peak loads (e.g., NFL weekend with 1000+ bets/minute).

Usage:
    locust -f tests/load/locustfile.py --host http://localhost:8080
    # Or headless:
    locust -f tests/load/locustfile.py --headless -u 100 -r 10 --run-time 60s

Note: Since VBQ is not a web service, this file exercises the Python API
layer directly via FastHttpUser calling a lightweight local endpoint,
or simulates in-memory pipeline load via a custom test server.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from locust import FastHttpUser, task, between


class BetPlacementUser(FastHttpUser):
    """Simulates a bettor placing bets through the VBQ system."""
    wait_time = between(0.5, 2.0)  # 0.5-2s between bets => 30-120 bets/min per user

    def on_start(self):
        """Authenticate or warm up session before betting."""
        self.client.get("/health")

    @task(5)
    def place_bet_football(self):
        """Place a football bet — high volume sport."""
        payload = {
            "sport": "football",
            "event_id": f"match_{random.randint(1, 99999)}",
            "odds": round(random.uniform(1.5, 5.0), 2),
            "stake": round(random.uniform(5.0, 100.0), 2),
            "side": random.choice(["home", "away", "draw"]),
        }
        self.client.post("/api/v1/bets", json=payload)

    @task(3)
    def place_bet_nba(self):
        """Place an NBA bet."""
        payload = {
            "sport": "basketball",
            "event_id": f"nba_{random.randint(1, 99999)}",
            "odds": round(random.uniform(1.3, 3.5), 2),
            "stake": round(random.uniform(10.0, 200.0), 2),
            "side": random.choice(["home", "away"]),
        }
        self.client.post("/api/v1/bets", json=payload)

    @task(2)
    def check_odds(self):
        """Poll odds endpoint — read-heavy traffic."""
        self.client.get("/api/v1/odds?sport=football")

    @task(1)
    def get_health(self):
        """Health check — should always be fast."""
        with self.client.get("/health", catch_response=True) as resp:
            if resp.elapsed.total_seconds() > 1.0:
                resp.failure("Health check too slow >1s")


class IngestionUser(FastHttpUser):
    """Simulates data ingestion load (odds snapshots)."""
    wait_time = between(1.0, 3.0)

    @task
    def ingest_odds_snapshot(self):
        snapshot = {
            "event_id": f"evt_{random.randint(1, 999999)}",
            "sport": random.choice(["football", "basketball", "tennis"]),
            "bookmaker": random.choice(["betfair", "pinnacle", "unibet"]),
            "odds_home": round(random.uniform(1.2, 8.0), 2),
            "odds_away": round(random.uniform(1.2, 8.0), 2),
            "timestamp": "2026-05-21T12:00:00Z",
        }
        self.client.post("/api/v1/ingest/odds", json=snapshot)


# ---------------------------------------------------------------------------
# Standalone Python load test (no web server required)
# ---------------------------------------------------------------------------
def _run_local_load_test(duration_sec: int = 30, target_rps: int = 16):
    """
    Local in-memory load test that exercises the pipeline directly.
    16 RPS * 60 = ~960 bets/minute (close to the 1000/min target).
    """
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from src.monitoring.api_health_dashboard import APIHealthDashboard
    from src.pipeline.orchestrator import PipelineOrchestrator

    print(f"Local load test: {target_rps} RPS for {duration_sec}s")
    dash = APIHealthDashboard()
    orch = PipelineOrchestrator(sport="football", mode="paper", dry_run=True)

    def _fire():
        t0 = time.perf_counter()
        try:
            orch.run_daily(dry_run=True)
            latency_ms = (time.perf_counter() - t0) * 1000
            dash.record("pipeline_run", latency_ms=latency_ms, success=True)
            return True
        except Exception as e:
            latency_ms = (time.perf_counter() - t0) * 1000
            dash.record("pipeline_run", latency_ms=latency_ms, success=False, error_type=type(e).__name__)
            return False

    start = time.time()
    total = 0
    success = 0
    with ThreadPoolExecutor(max_workers=target_rps * 2) as ex:
        futures = []
        while time.time() - start < duration_sec:
            # Launch up to target_rps per second
            for _ in range(target_rps):
                futures.append(ex.submit(_fire))
            time.sleep(1.0)
            # Drain completed
            done = [f for f in futures if f.done()]
            for f in done:
                total += 1
                if f.result():
                    success += 1
            futures = [f for f in futures if not f.done()]
        # Drain remaining
        for f in as_completed(futures, timeout=10):
            total += 1
            if f.result():
                success += 1

    report = dash.report()
    print(f"Total calls: {total} | Success: {success} | Error rate: {(1 - success/total)*100:.1f}%")
    print("API Health Report:")
    print(report)
    return report


if __name__ == "__main__":
    # If run directly without locust web UI, execute local load test
    _run_local_load_test(duration_sec=10, target_rps=8)
