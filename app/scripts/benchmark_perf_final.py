#!/usr/bin/env python3
"""
Final performance benchmark — outputs JSON for reliable capture.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    n_games = 100
    results = {}

    # [1] Ingest
    df = pd.read_parquet(PROJECT_ROOT / "data" / "bronze" / "matches_football_mock.parquet").head(n_games)
    t0 = time.perf_counter()
    for _ in range(10):
        _ = pd.read_parquet(PROJECT_ROOT / "data" / "bronze" / "matches_football_mock.parquet").head(n_games)
    t1 = time.perf_counter()
    results["ingest_ms"] = ((t1 - t0) * 1000) / 10

    # [2] Feature Pipeline
    from src.features.pipeline import FeaturePipeline
    p = FeaturePipeline(include_weather=False)
    games = pd.DataFrame({
        "game_id": [f"g_{i}" for i in range(n_games)],
        "game_date": pd.date_range("2024-01-01", periods=n_games),
        "home_team": np.random.choice(
            ["LAL", "GSW", "BOS", "MIA", "DAL", "CHI", "NYK", "PHX", "TOR", "DEN"], n_games
        ),
        "away_team": np.random.choice(
            ["LAL", "GSW", "BOS", "MIA", "DAL", "CHI", "NYK", "PHX", "TOR", "DEN"], n_games
        ),
        "home_score": np.random.randint(90, 130, n_games),
        "away_score": np.random.randint(90, 130, n_games),
    })
    odds = pd.DataFrame({
        "game_id": games["game_id"],
        "odd_home": np.random.uniform(1.3, 2.5, n_games),
        "odd_away": np.random.uniform(1.3, 2.5, n_games),
        "odd_draw": np.random.uniform(2.5, 4.0, n_games),
        "bookmaker": "mock",
    })
    t0 = time.perf_counter()
    feats = p.run(games, odds)
    t1 = time.perf_counter()
    results["feature_ms"] = (t1 - t0) * 1000
    results["feature_per_game_ms"] = results["feature_ms"] / n_games
    results["n_features"] = len(feats["features_data"].iloc[0].keys()) if len(feats) > 0 else 0

    # [3] Inference
    from sklearn.ensemble import GradientBoostingClassifier
    X = pd.DataFrame(list(feats["features_data"].values)).fillna(0)
    y = np.random.randint(0, 2, len(X))
    model = GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=42)
    model.fit(X.head(min(50, len(X))), y[:min(50, len(X))])
    _ = model.predict_proba(X.head(1))
    t0 = time.perf_counter()
    for _ in range(20):
        _ = model.predict_proba(X)
    t1 = time.perf_counter()
    results["inference_ms"] = ((t1 - t0) * 1000) / 20
    results["inference_per_game_ms"] = results["inference_ms"] / n_games

    # [4] Decision engine
    from src.decision_engine.market_aware import MarketAwareDecisionEngine
    engine = MarketAwareDecisionEngine()
    t0 = time.perf_counter()
    for i in range(n_games):
        opp = {
            "match_id": f"game_{i}",
            "edge": np.random.uniform(0.01, 0.08),
            "bookmaker_odds": np.random.uniform(1.5, 3.0),
            "calibrated_prob": np.random.uniform(0.3, 0.7),
            "predicted_prob": np.random.uniform(0.3, 0.7),
            "liquidity_usd": np.random.uniform(1000, 50000),
            "hours_to_kickoff": np.random.uniform(0.5, 48),
            "recommended_stake": np.random.uniform(5, 100),
            "volatility": np.random.uniform(0.05, 0.3),
        }
        ctx = {"odds_history": [], "hours_to_kickoff": opp["hours_to_kickoff"]}
        engine.decide(opp, ctx)
    t1 = time.perf_counter()
    results["decision_ms"] = (t1 - t0) * 1000
    results["decision_per_game_ms"] = results["decision_ms"] / n_games

    # [5] Full pipeline (with API overhead)
    from src.pipeline.orchestrator import PipelineOrchestrator
    orch = PipelineOrchestrator(sport="football", mode="paper", dry_run=True)
    t0 = time.perf_counter()
    try:
        result = orch.run_daily(dry_run=True)
        results["pipeline_ms"] = (time.perf_counter() - t0) * 1000
        results["pipeline_opportunities"] = result.get("opportunities", 0)
        results["pipeline_bets"] = result.get("bets_placed", 0)
    except Exception as e:
        results["pipeline_ms"] = (time.perf_counter() - t0) * 1000
        results["pipeline_error"] = str(e)
        results["pipeline_opportunities"] = 0
        results["pipeline_bets"] = 0

    results["n_games"] = n_games
    results["criteria_feature_ok"] = results["feature_per_game_ms"] < 500
    results["criteria_inference_ok"] = results["inference_per_game_ms"] < 50
    results["criteria_decision_ok"] = results["decision_per_game_ms"] < 50
    results["criteria_pipeline_ok"] = (
        results["pipeline_ms"] / max(1, results["pipeline_opportunities"]) < 1000
        if results["pipeline_opportunities"] > 0
        else False
    )

    output_path = PROJECT_ROOT / "logs" / "benchmark_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(json.dumps(results, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
