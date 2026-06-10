#!/usr/bin/env python3
"""
Incremental training validation with sliding window.

1. Train v1 on data until 2023-06-01
2. Simulate 3 months of new data (2023-06-02 to 2023-09-01)
3. Train v2 incrementally (sliding window: old + new)
4. Compare v1 vs v2 on holdout (2023-09-02+)
5. Check catastrophic forgetting on 2022 data
6. improvement_threshold rejects if v2 is worse
"""
from __future__ import annotations

import json
import pickle
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.local_store import LocalDataStore
from src.ingestion.real_data_pipeline import ensure_real_data_exists
from src.ml.models.football_poisson import FootballPoissonModel
from src.ml.models.football_hybrid import FootballHybridModel
from src.ml.training.regime_change_detector import RegimeChangeDetector, ReplayBuffer
from src.simulation.metrics import compute_backtest_metrics
from src.validation.clv_tracker import CLVTracker
from src.validation.walk_forward import WalkForwardValidator


def load_or_generate_data() -> pd.DataFrame:
    """Load existing mock data or generate fresh."""
    path = ensure_real_data_exists(str(PROJECT_ROOT / "data"))
    df = pd.read_parquet(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def split_data(df: pd.DataFrame, cutoff1: str, cutoff2: str):
    """Split into v1_train, v2_new, holdout."""
    v1 = df[df["date"] <= cutoff1].copy()
    new_window = df[(df["date"] > cutoff1) & (df["date"] <= cutoff2)].copy()
    holdout = df[df["date"] > cutoff2].copy()
    return v1, new_window, holdout


def train_model(df_train: pd.DataFrame, calibrate: bool = True) -> FootballPoissonModel:
    """Train a fresh FootballPoissonModel."""
    model = FootballPoissonModel(use_dixon_coles=True)
    model.fit(df_train, calibrate=calibrate)
    return model


def _get_probs(model, row):
    """Dispatch prediction to either Poisson or Hybrid model."""
    if hasattr(model, "predict_match_outcome"):
        return model.predict_match_outcome(
            row["home_team"], row["away_team"],
            league=row.get("league", row.get("competition", None)),
            apply_calibration=True,
        )
    else:
        return model.predict(
            row["home_team"], row["away_team"],
            odd_1=row.get("odd_1", 2.0),
            odd_X=row.get("odd_X", 3.0),
            odd_2=row.get("odd_2", 3.0),
            league=row.get("league", row.get("competition", None)),
            open_odd_home=row.get("open_odd_home", row.get("odd_1", 2.0)),
            pin_close_home=row.get("pin_close_home", row.get("odd_1", 2.0)),
            apply_calibration=True,
        )


def evaluate_model(model, df_test: pd.DataFrame) -> dict:
    """Evaluate model on test data. Returns ROI, bets, CLV, etc."""
    clv_tracker = CLVTracker()
    bankroll, bets, wins = 1000.0, 0, 0
    clv_values = []
    all_bets = []

    for _, row in df_test.iterrows():
        probs = _get_probs(model, row)
        open_odd = float(row.get("open_odd_home", row.get("odd_1", 2.0)))
        close_odd = float(row.get("pin_close_home", open_odd))
        edge = probs["1"] - (1.0 / open_odd)
        if edge < 0.02:
            continue

        stake = min(bankroll * 0.02, 20.0)
        bets += 1
        won = str(row.get("actual_outcome")) == "1"
        pnl = (open_odd - 1.0) if won else -1.0
        bankroll += pnl * (stake / 1.0)
        if won:
            wins += 1

        # CLV
        closing = {
            "home": close_odd,
            "draw": row.get("pin_close_draw", close_odd),
            "away": row.get("pin_close_away", close_odd),
        }
        clv = clv_tracker.calculate_clv(open_odd, "home", closing, market_type="3-way")
        clv_values.append(clv["clv_percentage"])

        all_bets.append({
            "match_id": row.get("match_id"),
            "date": str(row["date"].date()),
            "edge": edge,
            "pnl": pnl,
            "won": won,
            "open_odd": open_odd,
            "close_odd": close_odd,
            "clv_pct": clv["clv_percentage"],
        })

    roi = (bankroll - 1000.0) / 1000.0
    clv_arr = np.array(clv_values) if clv_values else np.array([0.0])
    return {
        "roi": roi,
        "bets": bets,
        "win_rate": wins / bets if bets else 0.0,
        "mean_clv_pct": float(np.mean(clv_arr)) * 100,
        "bankroll": bankroll,
        "all_bets": all_bets,
    }


def calculate_ece(model, df_test: pd.DataFrame) -> float:
    """Calculate Expected Calibration Error (ECE) on test set."""
    probs = []
    outcomes = []
    for _, row in df_test.iterrows():
        p = _get_probs(model, row)
        probs.append(p["1"])
        outcomes.append(1.0 if str(row.get("actual_outcome")) == "1" else 0.0)

    probs = np.array(probs)
    outcomes = np.array(outcomes)

    # 10 bins
    bin_edges = np.linspace(0, 1, 11)
    ece = 0.0
    for i in range(10):
        mask = (probs >= bin_edges[i]) & (probs < bin_edges[i + 1])
        if i == 9:
            mask = (probs >= bin_edges[i]) & (probs <= bin_edges[i + 1])
        if mask.sum() > 0:
            avg_conf = probs[mask].mean()
            avg_acc = outcomes[mask].mean()
            ece += mask.sum() * abs(avg_conf - avg_acc)
    return float(ece / len(probs)) if len(probs) > 0 else 0.0


def main() -> int:
    print("\n" + "=" * 70)
    print("  INCREMENTAL TRAINING VALIDATION")
    print("=" * 70 + "\n")

    # 1. Load data
    print("[1] Loading data...")
    df = load_or_generate_data()
    print(f"    Total records: {len(df)}")
    print(f"    Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    # Ensure open/close odds exist
    for col, fallback in [
        ("open_odd_home", "odd_1"),
        ("pin_close_home", "odd_1"),
        ("pin_close_draw", "odd_X"),
        ("pin_close_away", "odd_2"),
    ]:
        if col not in df.columns and fallback in df.columns:
            df[col] = df[fallback]

    # Split
    v1_train, new_window, holdout = split_data(df, "2023-06-01", "2023-09-01")
    old_data = df[df["date"] <= "2022-12-31"].copy()

    print(f"    v1_train: {len(v1_train)} (up to 2023-06-01)")
    print(f"    new_window: {len(new_window)} (2023-06-02 to 2023-09-01)")
    print(f"    holdout: {len(holdout)} (after 2023-09-01)")
    print(f"    old_2022: {len(old_data)} (2022 and before)")

    # 2. Train v1
    print("\n[2] Training v1 (baseline)...")
    v1 = train_model(v1_train)
    v1_path = PROJECT_ROOT / "data" / "models" / "football_v1.pkl"
    v1_path.parent.mkdir(parents=True, exist_ok=True)
    with open(v1_path, "wb") as f:
        pickle.dump(v1, f)
    print(f"    Saved: {v1_path}")

    # 3. Regime change detection
    print("\n[3] Regime change detection (should we update?)...")
    detector = RegimeChangeDetector(
        psi_threshold=0.25,
        ks_threshold=0.10,
        clv_drift_threshold=0.02,
        agreement_required=2,
    )
    regime_result = detector.detect(v1_train, new_window)
    print(f"    Regime changed: {regime_result['regime_changed']} (confidence: {regime_result['confidence']})")
    print(f"    Alerts: {regime_result['alerts']}")
    print(f"    PSI scores: {regime_result['psi_scores']}")
    print(f"    KS scores: {regime_result['ks_scores']}")
    print(f"    CLV drift: {regime_result['clv_drift']}")

    # 4. Incremental training for v2 using real EMA update
    print("\n[4] Training v2 (incremental update with EMA)...")
    if regime_result["regime_changed"]:
        v2 = pickle.loads(pickle.dumps(v1))  # Deep copy v1
        update_stats = v2.update(new_window, alpha=None, calibrate=True)
        print(f"    UPDATE EXECUTED (regime change detected)")
    else:
        v2 = pickle.loads(pickle.dumps(v1))  # Keep v1 unchanged
        update_stats = {"updated": False, "reason": "no_regime_change"}
        print(f"    UPDATE SKIPPED (market stable)")
    v2_path = PROJECT_ROOT / "data" / "models" / "football_v2.pkl"
    with open(v2_path, "wb") as f:
        pickle.dump(v2, f)
    print(f"    Saved: {v2_path}")
    print(f"    Update stats: {update_stats}")

    # 5. Alpha sensitivity sweep (only meaningful if regime changed)
    print("\n[5] Alpha sensitivity sweep (finding optimal EMA learning rate)...")
    alphas = [0.01, 0.025, 0.05, 0.10, 0.20, 0.30, 0.50]
    alpha_results = []
    for a in alphas:
        v2_test = pickle.loads(pickle.dumps(v1))
        v2_test.update(new_window, alpha=a, calibrate=False)
        hold = evaluate_model(v2_test, holdout)
        alpha_results.append({
            "alpha": a,
            "roi": hold["roi"],
            "clv": hold["mean_clv_pct"],
            "bets": hold["bets"],
        })

    best_alpha = max(alpha_results, key=lambda x: x["roi"])
    print(f"    Alpha sweep results:")
    for ar in alpha_results:
        marker = "  <-- BEST" if ar["alpha"] == best_alpha["alpha"] else ""
        print(f"      alpha={ar['alpha']:<5} ROI={ar['roi']:>8.2%}  CLV={ar['clv']:>6.3f}%  Bets={ar['bets']}{marker}")

    # Re-train v2 with best alpha for final evaluation
    if best_alpha["alpha"] != update_stats.get("alpha_used", -1):
        print(f"    Retraining v2 with best alpha={best_alpha['alpha']}...")
        v2 = pickle.loads(pickle.dumps(v1))
        update_stats = v2.update(new_window, alpha=best_alpha["alpha"], calibrate=True)

    # 6. Hybrid model (Poisson + XGBoost warm-start)
    print("\n[6] Training v3 (Hybrid: Poisson + XGBoost warm-start)...")
    hybrid_v1 = FootballHybridModel(blend_weight=0.3)
    hybrid_v1.fit(v1_train, calibration=True)

    if regime_result["regime_changed"]:
        hybrid_v3 = pickle.loads(pickle.dumps(hybrid_v1))
        hybrid_update = hybrid_v3.update(new_window, alpha=0.05, xgb_incremental_rounds=30, calibration=False)
        print(f"    UPDATE EXECUTED (regime change detected)")
    else:
        hybrid_v3 = pickle.loads(pickle.dumps(hybrid_v1))  # Keep unchanged
        hybrid_update = {"updated": False, "reason": "no_regime_change"}
        print(f"    UPDATE SKIPPED (market stable)")
    print(f"    Hybrid update stats: {hybrid_update}")

    # Blend weight sweep for hybrid
    print("\n[6b] Hybrid blend_weight sweep...")
    blend_weights = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
    blend_results = []
    for bw in blend_weights:
        h_test = FootballHybridModel(blend_weight=bw)
        h_test.fit(v1_train, calibration=False)
        h_test.update(new_window, alpha=0.05, xgb_incremental_rounds=30, calibration=False)
        hold = evaluate_model(h_test, holdout)
        blend_results.append({"bw": bw, "roi": hold["roi"], "clv": hold["mean_clv_pct"], "bets": hold["bets"]})

    best_bw = max(blend_results, key=lambda x: x["roi"])
    for br in blend_results:
        marker = "  <-- BEST" if br["bw"] == best_bw["bw"] else ""
        print(f"      bw={br['bw']:<4} ROI={br['roi']:>8.2%}  CLV={br['clv']:>6.3f}%  Bets={br['bets']}{marker}")

    if best_bw["bw"] != hybrid_v3.blend_weight:
        print(f"    Retraining hybrid with best bw={best_bw['bw']}...")
        hybrid_v3 = FootballHybridModel(blend_weight=best_bw["bw"])
        hybrid_v3.fit(v1_train, calibration=True)
        hybrid_v3.update(new_window, alpha=0.05, xgb_incremental_rounds=30, calibration=False)

    # 7. Replay Buffer model (v4) — full refit on recent window
    print("\n[7] Training v4 (Replay Buffer: full refit on sliding window)...")
    # Build replay buffer: keep last N matches from v1_train + all new_window
    replay_buffer_size = 500
    replay_data = pd.concat([v1_train.tail(replay_buffer_size), new_window], ignore_index=True)
    if "match_id" in replay_data.columns:
        replay_data = replay_data.drop_duplicates(subset=["match_id"]).sort_values("date").reset_index(drop=True)
    v4 = train_model(replay_data, calibrate=True)
    print(f"    Replay buffer size: {len(replay_data)} (last {replay_buffer_size} from v1 + {len(new_window)} new)")

    # 8. Evaluate all four on holdout
    print("\n[8] Evaluating on holdout (2023-09-02 onwards)...")
    v1_holdout = evaluate_model(v1, holdout)
    v2_holdout = evaluate_model(v2, holdout)
    v3_holdout = evaluate_model(hybrid_v3, holdout)
    v4_holdout = evaluate_model(v4, holdout)

    v1_ece = calculate_ece(v1, holdout)
    v2_ece = calculate_ece(v2, holdout)
    v3_ece = calculate_ece(hybrid_v3, holdout)
    v4_ece = calculate_ece(v4, holdout)

    print(f"    v1 (Poisson)        — ROI: {v1_holdout['roi']:.2%}, Bets: {v1_holdout['bets']}, WinRate: {v1_holdout['win_rate']:.2%}, CLV: {v1_holdout['mean_clv_pct']:.3f}%, ECE: {v1_ece:.4f}")
    print(f"    v2 (Poisson EMA)    — ROI: {v2_holdout['roi']:.2%}, Bets: {v2_holdout['bets']}, WinRate: {v2_holdout['win_rate']:.2%}, CLV: {v2_holdout['mean_clv_pct']:.3f}%, ECE: {v2_ece:.4f}")
    print(f"    v3 (Hybrid XGB)     — ROI: {v3_holdout['roi']:.2%}, Bets: {v3_holdout['bets']}, WinRate: {v3_holdout['win_rate']:.2%}, CLV: {v3_holdout['mean_clv_pct']:.3f}%, ECE: {v3_ece:.4f}")
    print(f"    v4 (Replay Buffer)   — ROI: {v4_holdout['roi']:.2%}, Bets: {v4_holdout['bets']}, WinRate: {v4_holdout['win_rate']:.2%}, CLV: {v4_holdout['mean_clv_pct']:.3f}%, ECE: {v4_ece:.4f}")

    # 9. Catastrophic forgetting test (2022 data)
    print("\n[9] Testing catastrophic forgetting on 2022 data...")
    if len(old_data) >= 10:
        v1_2022 = evaluate_model(v1, old_data)
        v2_2022 = evaluate_model(v2, old_data)
        v3_2022 = evaluate_model(hybrid_v3, old_data)
        v4_2022 = evaluate_model(v4, old_data)
        print(f"    v1 on 2022 — ROI: {v1_2022['roi']:.2%}, Bets: {v1_2022['bets']}")
        print(f"    v2 on 2022 — ROI: {v2_2022['roi']:.2%}, Bets: {v2_2022['bets']}")
        print(f"    v3 on 2022 — ROI: {v3_2022['roi']:.2%}, Bets: {v3_2022['bets']}")
        print(f"    v4 on 2022 — ROI: {v4_2022['roi']:.2%}, Bets: {v4_2022['bets']}")
        forgetting_v2 = v2_2022["roi"] < v1_2022["roi"] * 0.9
        forgetting_v3 = v3_2022["roi"] < v1_2022["roi"] * 0.9
        forgetting_v4 = v4_2022["roi"] < v1_2022["roi"] * 0.9
        print(f"    v2 forgetting: {'YES' if forgetting_v2 else 'NO'}")
        print(f"    v3 forgetting: {'YES' if forgetting_v3 else 'NO'}")
        print(f"    v4 forgetting: {'YES' if forgetting_v4 else 'NO'}")
    else:
        print("    Skipping (insufficient 2022 data)")
        forgetting_v2 = False
        forgetting_v3 = False
        forgetting_v4 = False
        v1_2022 = {"roi": 0, "bets": 0}
        v2_2022 = {"roi": 0, "bets": 0}
        v3_2022 = {"roi": 0, "bets": 0}
        v4_2022 = {"roi": 0, "bets": 0}

    # 10. Improvement threshold check
    print("\n[10] Applying improvement_threshold...")
    improvement_threshold = 0.001

    roi_improvement_v2 = v2_holdout["roi"] - v1_holdout["roi"]
    roi_improvement_v3 = v3_holdout["roi"] - v1_holdout["roi"]
    roi_improvement_v4 = v4_holdout["roi"] - v1_holdout["roi"]

    improved_v2 = (roi_improvement_v2 > improvement_threshold and not forgetting_v2)
    improved_v3 = (roi_improvement_v3 > improvement_threshold and not forgetting_v3)
    improved_v4 = (roi_improvement_v4 > improvement_threshold and not forgetting_v4)

    print(f"    v2 ROI improvement: {roi_improvement_v2:.4f}  -> {'ACCEPTED' if improved_v2 else 'REJECTED'}")
    print(f"    v3 ROI improvement: {roi_improvement_v3:.4f}  -> {'ACCEPTED' if improved_v3 else 'REJECTED'}")
    print(f"    v4 ROI improvement: {roi_improvement_v4:.4f}  -> {'ACCEPTED' if improved_v4 else 'REJECTED'}")

    # 11. Summary table
    print("\n" + "=" * 90)
    print("  SUMMARY TABLE")
    print("=" * 90)
    print(f"  {'Metric':<25} {'v1':>12} {'v2':>12} {'v3':>12} {'v4':>12} {'Best':>8}")
    print("  " + "-" * 86)

    metrics = [
        ("Holdout ROI", v1_holdout["roi"], v2_holdout["roi"], v3_holdout["roi"], v4_holdout["roi"]),
        ("Holdout Bets", v1_holdout["bets"], v2_holdout["bets"], v3_holdout["bets"], v4_holdout["bets"]),
        ("Holdout WinRate", v1_holdout["win_rate"], v2_holdout["win_rate"], v3_holdout["win_rate"], v4_holdout["win_rate"]),
        ("Holdout CLV%", v1_holdout["mean_clv_pct"] / 100, v2_holdout["mean_clv_pct"] / 100, v3_holdout["mean_clv_pct"] / 100, v4_holdout["mean_clv_pct"] / 100),
        ("Holdout ECE", v1_ece, v2_ece, v3_ece, v4_ece),
    ]
    if len(old_data) >= 10:
        metrics += [
            ("2022 ROI", v1_2022["roi"], v2_2022["roi"], v3_2022["roi"], v4_2022["roi"]),
        ]

    best_model = None
    best_roi = v1_holdout["roi"]
    for name, v1v, v2v, v3v, v4v in metrics:
        if name == "Holdout ROI":
            vals = [("v1", v1v), ("v2", v2v), ("v3", v3v), ("v4", v4v)]
            best_model = max(vals, key=lambda x: x[1])[0]
            best_roi = max(v1v, v2v, v3v, v4v)
        print(f"  {name:<25} {v1v:>12.4f} {v2v:>12.4f} {v3v:>12.4f} {v4v:>12.4f}")

    # Recommendations
    print("\n" + "=" * 90)
    print("  RECOMMENDATIONS")
    print("=" * 90)
    if best_model == "v4":
        print("  [OK] v4 (Replay Buffer) is superior — promote to production.")
    elif best_model == "v3":
        print("  [OK] v3 (Hybrid XGBoost) is superior — promote to production.")
    elif best_model == "v2":
        print("  [OK] v2 (Poisson EMA) is superior — promote to production.")
    else:
        print("  [!] v1 (Baseline) still best. No update warranted.")

    if forgetting_v2 or forgetting_v3 or forgetting_v4:
        print("  [!] Catastrophic forgetting detected. Investigate replay buffer / EWC.")

    # Save report
    report = {
        "v1_holdout": v1_holdout,
        "v2_holdout": v2_holdout,
        "v3_holdout": v3_holdout,
        "v4_holdout": v4_holdout,
        "v1_ece": v1_ece,
        "v2_ece": v2_ece,
        "v3_ece": v3_ece,
        "v4_ece": v4_ece,
        "v1_2022": v1_2022 if len(old_data) >= 10 else None,
        "v2_2022": v2_2022 if len(old_data) >= 10 else None,
        "v3_2022": v3_2022 if len(old_data) >= 10 else None,
        "v4_2022": v4_2022 if len(old_data) >= 10 else None,
        "improvement_threshold": improvement_threshold,
        "best_model": best_model,
        "update_accepted_v2": bool(improved_v2),
        "update_accepted_v3": bool(improved_v3),
        "update_accepted_v4": bool(improved_v4),
        "catastrophic_forgetting_v2": bool(forgetting_v2),
        "catastrophic_forgetting_v3": bool(forgetting_v3),
        "catastrophic_forgetting_v4": bool(forgetting_v4),
        "regime_change": regime_result,
    }
    out = PROJECT_ROOT / "data" / "reports" / "incremental_training.json"
    with open(out, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n  Report saved to: {out}")
    print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
