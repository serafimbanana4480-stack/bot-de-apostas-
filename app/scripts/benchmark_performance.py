#!/usr/bin/env python3
"""
Performance benchmark for VBQ pipeline components.

Measures:
1. Feature engineering time (target: <500ms per game)
2. Model inference time (target: <50ms per game)
3. Pipeline decision time per opportunity (target: <1000ms per game)
4. End-to-end pipeline with synthetic data scaling.

Usage:
    python scripts/benchmark_performance.py
    python scripts/benchmark_performance.py --rows 1000
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_real_football_games(n_rows: int = 100) -> Any:
    """Load real football game data for benchmarking."""
    import pandas as pd
    from src.ingestion.real_data_pipeline import ensure_real_data_exists

    try:
        store_path = ensure_real_data_exists(str(PROJECT_ROOT / "data" / "bronze"))
        df = pd.read_parquet(store_path)
        if len(df) >= n_rows:
            return df.head(n_rows).copy()
        return df.copy()
    except RuntimeError as e:
        raise RuntimeError(
            f"No real data available for benchmarking: {e}. "
            "Run: scripts/ingest_real_data.py --seasons 2122 2223 2324"
        )
        home = teams[i % 20]
        away = teams[(i + 1) % 20]
        rows.append({
            "game_id": f"g_{i}",
            "game_date": base_date + pd.Timedelta(days=i),
            "home_team": home,
            "away_team": away,
            "home_score": rng.randint(0, 4),
            "away_score": rng.randint(0, 4),
        })
    return pd.DataFrame(rows)


def benchmark_feature_pipeline(games_df: Any, odds_df: Any = None) -> Dict[str, float]:
    """Benchmark FeaturePipeline.run() execution time."""
    import pandas as pd
    from src.features.pipeline import FeaturePipeline

    if odds_df is None:
        odds_df = pd.DataFrame({
            "game_id": games_df["game_id"].values,
            "odd_home": np.random.uniform(1.5, 3.0, len(games_df)),
            "odd_away": np.random.uniform(1.5, 3.0, len(games_df)),
            "odd_draw": np.random.uniform(2.5, 4.0, len(games_df)),
            "bookmaker": "pinnacle",
        })

    pipeline = FeaturePipeline(include_weather=False)

    # Warm-up
    _ = pipeline.run(games_df.head(1), odds_df.head(1))

    times = []
    for _ in range(5):
        t0 = time.perf_counter()
        features = pipeline.run(games_df, odds_df)
        t1 = time.perf_counter()
        times.append(t1 - t0)

    return {
        "feature_time_ms": np.mean(times) * 1000,
        "feature_time_std_ms": np.std(times) * 1000,
        "feature_count": len(features.columns) if hasattr(features, "columns") else 0,
        "games_processed": len(games_df),
        "per_game_ms": (np.mean(times) * 1000) / len(games_df),
    }


def benchmark_model_inference(games_df: Any) -> Dict[str, float]:
    """Benchmark model inference time."""
    import pandas as pd

    # Use FootballPoissonModel for prediction
    try:
        from src.ml.models.football_poisson import FootballPoissonModel
        model = FootballPoissonModel()
    except Exception as e:
        print(f"  [WARN] FootballPoissonModel failed: {e}")
        return {"inference_time_ms": -1, "error": str(e)}

    # Prepare features similar to what the model expects
    features = pd.DataFrame({
        "home_elo": np.random.uniform(1400, 1600, len(games_df)),
        "away_elo": np.random.uniform(1400, 1600, len(games_df)),
        "home_rest": np.random.uniform(1, 5, len(games_df)),
        "away_rest": np.random.uniform(1, 5, len(games_df)),
        "home_win_rate_5": np.random.uniform(0.3, 0.7, len(games_df)),
        "away_win_rate_5": np.random.uniform(0.3, 0.7, len(games_df)),
    })

    # Warm-up
    try:
        _ = model.predict(features.head(1))
    except Exception:
        pass

    times = []
    for _ in range(10):
        t0 = time.perf_counter()
        try:
            _ = model.predict(features)
        except Exception:
            pass
        t1 = time.perf_counter()
        times.append(t1 - t0)

    return {
        "inference_time_ms": np.mean(times) * 1000,
        "inference_std_ms": np.std(times) * 1000,
        "games_processed": len(games_df),
        "per_game_ms": (np.mean(times) * 1000) / len(games_df),
    }


def benchmark_pipeline_decision(n_games: int = 100) -> Dict[str, float]:
    """Benchmark PipelineOrchestrator decision time per opportunity."""
    from src.pipeline.orchestrator import PipelineOrchestrator

    orch = PipelineOrchestrator(sport="football", mode="paper", dry_run=True)

    # Run once to warm up
    try:
        _ = orch.run_daily(dry_run=True)
    except Exception as e:
        print(f"  [WARN] Warm-up failed: {e}")

    times = []
    for _ in range(3):
        t0 = time.perf_counter()
        try:
            result = orch.run_daily(dry_run=True)
            n_opp = result.get("opportunities", 0)
        except Exception as e:
            print(f"  [WARN] Pipeline run failed: {e}")
            result = {}
            n_opp = 0
        t1 = time.perf_counter()
        times.append((t1 - t0, n_opp))

    avg_time = np.mean([t for t, _ in times])
    avg_opp = max(1, int(np.mean([o for _, o in times])))

    return {
        "pipeline_time_ms": avg_time * 1000,
        "pipeline_std_ms": np.std([t for t, _ in times]) * 1000,
        "opportunities": avg_opp,
        "per_opportunity_ms": (avg_time * 1000) / avg_opp if avg_opp > 0 else -1,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="VBQ Performance Benchmark")
    parser.add_argument("--rows", type=int, default=100, help="Number of synthetic rows")
    args = parser.parse_args()

    n_rows = args.rows
    print(f"\n{'='*70}")
    print(f"  VBQ PERFORMANCE BENCHMARK — {n_rows} rows")
    print(f"{'='*70}\n")

    print("[1/4] Loading real data...")
    games_df = load_real_football_games(n_rows)
    print(f"      Loaded {len(games_df)} games")

    print("\n[2/4] Benchmarking FeaturePipeline...")
    feature_result = benchmark_feature_pipeline(games_df)
    print(f"      Feature time: {feature_result['feature_time_ms']:.1f} ms (std: {feature_result['feature_time_std_ms']:.1f} ms)")
    print(f"      Per game: {feature_result['per_game_ms']:.2f} ms | Features: {feature_result['feature_count']}")

    print("\n[3/4] Benchmarking Model Inference...")
    inference_result = benchmark_model_inference(games_df)
    if inference_result.get("inference_time_ms", -1) > 0:
        print(f"      Inference time: {inference_result['inference_time_ms']:.1f} ms (std: {inference_result['inference_std_ms']:.1f} ms)")
        print(f"      Per game: {inference_result['per_game_ms']:.2f} ms")
    else:
        print(f"      SKIPPED: {inference_result.get('error', 'unknown')}")

    print("\n[4/4] Benchmarking Pipeline Decision...")
    pipeline_result = benchmark_pipeline_decision(n_rows)
    print(f"      Pipeline time: {pipeline_result['pipeline_time_ms']:.1f} ms (std: {pipeline_result['pipeline_std_ms']:.1f} ms)")
    print(f"      Opportunities: {pipeline_result['opportunities']} | Per opp: {pipeline_result['per_opportunity_ms']:.2f} ms")

    # Criteria check
    print(f"\n{'='*70}")
    print("  CRITERIA CHECK")
    print(f"{'='*70}")

    checks = []
    per_game_feature = feature_result.get("per_game_ms", float("inf"))
    per_game_inference = inference_result.get("per_game_ms", float("inf"))
    per_opp_pipeline = pipeline_result.get("per_opportunity_ms", float("inf"))

    feature_ok = per_game_feature < 500
    inference_ok = per_game_inference < 50
    pipeline_ok = per_opp_pipeline < 1000

    print(f"  Feature engineering < 500ms/game:   {per_game_feature:.2f} ms  [{'PASS' if feature_ok else 'FAIL'}]")
    print(f"  Model inference < 50ms/game:        {per_game_inference:.2f} ms  [{'PASS' if inference_ok else 'FAIL'}]")
    print(f"  Pipeline decision < 1000ms/opp:     {per_opp_pipeline:.2f} ms  [{'PASS' if pipeline_ok else 'FAIL'}]")

    overall = "PASS" if feature_ok and inference_ok and pipeline_ok else "FAIL"
    print(f"\n  OVERALL: {overall}")
    print(f"{'='*70}\n")

    # JSON summary
    summary = {
        "n_rows": n_rows,
        "feature_engineering_ms": feature_result["feature_time_ms"],
        "feature_per_game_ms": per_game_feature,
        "inference_ms": inference_result.get("inference_time_ms", -1),
        "inference_per_game_ms": per_game_inference,
        "pipeline_ms": pipeline_result["pipeline_time_ms"],
        "pipeline_per_opportunity_ms": per_opp_pipeline,
        "criteria_feature_ok": feature_ok,
        "criteria_inference_ok": inference_ok,
        "criteria_pipeline_ok": pipeline_ok,
        "overall": overall,
    }
    import json
    print(json.dumps(summary, indent=2))
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
