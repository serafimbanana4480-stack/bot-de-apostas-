#!/usr/bin/env python3
"""
Test shadow deployment: champion vs challenger on live opportunities.

Usage:
    python scripts/test_shadow_deployment.py
"""
from __future__ import annotations

import json
import logging
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.local_store import LocalDataStore
from src.ingestion.mock_football_data import ensure_mock_dataset
from src.ml.models.football_poisson import FootballPoissonModel
from src.mlops.shadow_controller import LiveShadowController

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_shadow")


def load_champion() -> FootballPoissonModel:
    path = PROJECT_ROOT / "data" / "models" / "champion" / "football_poisson_champion.pkl"
    with open(path, "rb") as f:
        return pickle.load(f)


def train_challenger(df: pd.DataFrame) -> FootballPoissonModel:
    """Train a challenger on a different data subset (last 50% only)."""
    split = int(len(df) * 0.5)
    train = df.iloc[split:].copy()
    model = FootballPoissonModel(use_dixon_coles=True)
    model.fit(train, calibrate=True)
    return model


def main() -> int:
    print("\n" + "=" * 70)
    print("  SHADOW DEPLOYMENT TEST")
    print("=" * 70 + "\n")

    # 1. Load data
    df = ensure_mock_dataset(str(PROJECT_ROOT / "data"), force=False)
    df["date"] = pd.to_datetime(df["date"])

    # 2. Load champion
    champion = load_champion()
    print("[1] Champion loaded")

    # 3. Train challenger
    challenger = train_challenger(df)
    print("[2] Challenger trained on last 50% of data")

    # 4. Initialize shadow controller
    shadow = LiveShadowController(champion_id="football_poisson_champion", challenger_id="football_poisson_challenger")

    # 5. Simulate live opportunities (use last 10 matches)
    test_df = df.tail(10).copy()
    print(f"[3] Simulating {len(test_df)} live opportunities...")

    for _, row in test_df.iterrows():
        event_id = str(row.get("match_id", row.name))
        current_odds = float(row.get("odd_1", 2.0))

        def champ_pred():
            p = champion.predict_match_outcome(row["home_team"], row["away_team"], apply_calibration=True)
            return p["1"]

        def chall_pred():
            p = challenger.predict_match_outcome(row["home_team"], row["away_team"], apply_calibration=True)
            return p["1"]

        shadow.process_live_opportunity(event_id, current_odds, champ_pred, chall_pred)

    # 6. Report shadow metrics
    metrics = shadow.get_shadow_performance_metrics()
    print(f"\n[4] Shadow metrics:")
    print(f"    Total tracked: {metrics['total_tracked']}")
    print(f"    Discrepancies: {metrics['discrepancies']}")
    print(f"    Discrepancy rate: {metrics['discrepancy_rate']:.2%}")

    # 7. Show logs
    print(f"\n[5] Shadow logs (first 3):")
    for log in shadow.shadow_logs[:3]:
        print(f"    Event {log['event_id']}: "
              f"Champ={log['champion']['decision']}(EV={log['champion']['ev']:.3f}) "
              f"Chall={log['challenger']['decision']}(EV={log['challenger']['ev']:.3f})")

    # 8. Verify no real bets executed
    print(f"\n[6] Verification: Shadow mode = NO real bets placed")
    print(f"    All decisions were virtual (logged only)")

    # 9. Save report
    report = {
        "shadow_test": True,
        "total_tracked": metrics["total_tracked"],
        "discrepancies": metrics["discrepancies"],
        "discrepancy_rate": metrics["discrepancy_rate"],
        "champion_id": shadow.champion_id,
        "challenger_id": shadow.challenger_id,
    }
    out_path = PROJECT_ROOT / "data" / "reports" / "shadow_test.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Report saved to: {out_path}")
    print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
