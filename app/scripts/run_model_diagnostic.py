#!/usr/bin/env python3
"""
Diagnóstico completo do FootballPoissonModelV2 atual.

Gera:
- ECE por bin de probabilidade
- Reliability diagram (PNG)
- Brier decomposition
- p-value do ROI
- Kelly ratio (recomendado vs ideal)
- Halflife grid search resultados
- Feature importance (Random Forest sobre features atuais)
- Overfit diagnostic

Usage:
    py -3 scripts/run_model_diagnostic.py
"""
import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.diagnostics.calibration_metrics import (
    brier_decomposition,
    compute_ece,
    compute_ece_by_bin,
    monte_carlo_risk_of_ruin,
    plot_reliability_diagram,
    statistical_significance_roi,
    kelly_with_sanity,
)
from src.ml.models.football_poisson_v2 import FootballPoissonModelV2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("model_diagnostic")


def load_data(parquet_path: Path) -> pd.DataFrame:
    df = pd.read_parquet(parquet_path)
    df["date"] = pd.to_datetime(df["date"])
    core = [
        "home_team", "away_team", "home_goals", "away_goals",
        "actual_outcome", "date",
    ]
    df = df.dropna(subset=core)
    return df.sort_values("date").reset_index(drop=True)


def generate_predictions(model, df: pd.DataFrame):
    """Generate predictions and extract model features for importance."""
    records = []
    for _, row in df.iterrows():
        probs = model.predict_match_outcome(
            row["home_team"],
            row["away_team"],
            league=row.get("league"),
            apply_calibration=model.is_calibrated,
        )

        # Extract simple features for RF importance
        atk_h = model.attack.get(row["home_team"], 0.0)
        dfn_a = model.defense.get(row["away_team"], 0.0)
        atk_a = model.attack.get(row["away_team"], 0.0)
        dfn_h = model.defense.get(row["home_team"], 0.0)
        form_h = model.get_recent_form(row["home_team"], 5)
        form_a = model.get_recent_form(row["away_team"], 5)

        records.append({
            "date": row["date"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "actual_outcome": str(row["actual_outcome"]),
            "prob_home": probs["1"],
            "prob_draw": probs["X"],
            "prob_away": probs["2"],
            "pred_outcome": max(["1", "X", "2"], key=lambda k: probs[k]),
            # Features
            "feat_atk_h": atk_h,
            "feat_dfn_a": dfn_a,
            "feat_atk_a": atk_a,
            "feat_dfn_h": dfn_h,
            "feat_form_h_pts": form_h["points_per_game"],
            "feat_form_h_gs": form_h["goals_scored"],
            "feat_form_h_gc": form_h["goals_conceded"],
            "feat_form_a_pts": form_a["points_per_game"],
            "feat_form_a_gs": form_a["goals_scored"],
            "feat_form_a_gc": form_a["goals_conceded"],
            "feat_home_adv": model.home_advantage,
            "feat_global_avg": model.global_avg_goals,
        })
    return pd.DataFrame(records)


def compute_kelly_analysis(df_preds: pd.DataFrame, odds_col_map: dict) -> dict:
    """Analyze Kelly recommendations vs reality."""
    kelly_ratios = []
    for _, row in df_preds.iterrows():
        pred = row["pred_outcome"]
        prob = row[f"prob_{['home', 'draw', 'away'][['1', 'X', '2'].index(pred)]}"]
        # Use synthetic fair odds = 1/prob for analysis
        fair_odds = 1.0 / max(prob, 0.001)
        k = kelly_with_sanity(prob, fair_odds, ece=0.05)
        kelly_ratios.append(k["kelly_full"])

    df_preds["kelly_full"] = kelly_ratios

    # Ideal Kelly with true win rate
    win_rate = (df_preds["pred_outcome"] == df_preds["actual_outcome"]).mean()
    avg_odds = 2.5  # rough average
    b = avg_odds - 1.0
    ideal_kelly = max(0.0, (b * win_rate - (1 - win_rate)) / b)

    avg_rec_kelly = df_preds["kelly_full"].mean()
    ratio = avg_rec_kelly / ideal_kelly if ideal_kelly > 0 else 0.0

    return {
        "avg_recommended_kelly": float(avg_rec_kelly),
        "ideal_kelly_with_true_wr": float(ideal_kelly),
        "kelly_ratio": float(ratio),
        "true_win_rate": float(win_rate),
    }


def run_diagnostic(data_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_data(data_path)
    logger.info("Loaded %d matches", len(df))

    # Temporal split
    n = len(df)
    train_end = int(n * 0.60)
    val_end = int(n * 0.80)

    df_train = df.iloc[:train_end].copy()
    df_val = df.iloc[train_end:val_end].copy()
    df_test = df.iloc[val_end:].copy()

    # ------------------------------------------------------------------
    # 1. Fit model
    # ------------------------------------------------------------------
    logger.info("Fitting PoissonV2...")
    model = FootballPoissonModelV2(
        use_dixon_coles=True,
        reg_lambda=0.15,
        time_decay_halflife_days=365.0,
    )
    model.fit(df_train, calibrate=True)

    # ------------------------------------------------------------------
    # 2. Generate predictions on test
    # ------------------------------------------------------------------
    logger.info("Generating predictions on test set...")
    df_preds = generate_predictions(model, df_test)

    # ------------------------------------------------------------------
    # 3. Calibration analysis per outcome
    # ------------------------------------------------------------------
    logger.info("Computing calibration metrics...")
    calibration_results = {}
    for outcome, prob_col in [("1", "prob_home"), ("X", "prob_draw"), ("2", "prob_away")]:
        probs = df_preds[prob_col].values
        actuals = (df_preds["actual_outcome"] == outcome).astype(int).values
        ece = compute_ece(probs, actuals, n_bins=10)
        brier = brier_decomposition(probs, actuals)
        calibration_results[outcome] = {
            "ece": ece,
            "brier_score": brier["brier_score"],
            "reliability": brier["reliability"],
            "resolution": brier["resolution"],
            "uncertainty": brier["uncertainty"],
            "n_samples": int(actuals.sum()),
        }

        # Reliability diagram
        try:
            import matplotlib
            matplotlib.use("Agg")
            fig = plot_reliability_diagram(probs, actuals, title=f"Reliability Diagram — Outcome {outcome}")
            fig.savefig(output_dir / f"reliability_{outcome}.png", dpi=150, bbox_inches="tight")
            logger.info("Saved reliability_%s.png", outcome)
        except Exception as e:
            logger.warning("Could not save reliability diagram: %s", e)

    # Overall ECE (using predicted outcome probability)
    pred_probs = []
    pred_actuals = []
    for _, row in df_preds.iterrows():
        pred = row["pred_outcome"]
        prob = row[["prob_home", "prob_draw", "prob_away"][["1", "X", "2"].index(pred)]]
        pred_probs.append(prob)
        pred_actuals.append(1 if pred == row["actual_outcome"] else 0)

    overall_ece = compute_ece(np.array(pred_probs), np.array(pred_actuals), n_bins=10)

    # ------------------------------------------------------------------
    # 4. ROI & statistical significance
    # ------------------------------------------------------------------
    returns = []
    for _, row in df_preds.iterrows():
        pred = row["pred_outcome"]
        won = pred == row["actual_outcome"]
        # Assume unit stake, fair odds = 1/prob
        fair_odds = 1.0 / row[["prob_home", "prob_draw", "prob_away"][["1", "X", "2"].index(pred)]]
        ret = (fair_odds - 1.0) if won else -1.0
        returns.append(ret)

    returns = np.array(returns)
    roi = returns.mean()
    t_stat, p_value = statistical_significance_roi(returns)

    # ------------------------------------------------------------------
    # 5. Kelly analysis
    # ------------------------------------------------------------------
    kelly_analysis = compute_kelly_analysis(df_preds, {})

    # ------------------------------------------------------------------
    # 6. Halflife grid search
    # ------------------------------------------------------------------
    logger.info("Running halflife grid search...")
    halflife_results = FootballPoissonModelV2.grid_search_halflife(
        df_train,
        halflife_candidates=[30.0, 60.0, 90.0, 120.0, 180.0, 365.0],
        metric="log_likelihood",
        n_splits=3,
    )

    # ------------------------------------------------------------------
    # 7. Regularization grid search
    # ------------------------------------------------------------------
    logger.info("Running regularization grid search...")
    reg_results = FootballPoissonModelV2.grid_search_regularization(
        df_train,
        lambda_candidates=[0.05, 0.10, 0.15, 0.20, 0.30, 0.50],
        n_splits=3,
    )

    # ------------------------------------------------------------------
    # 8. Overfit diagnostic
    # ------------------------------------------------------------------
    logger.info("Running overfit diagnostic...")
    overfit_diag = FootballPoissonModelV2.overfit_diagnostic(
        df_train, df_val, halflife=model.time_decay_halflife_days, reg_lambda=model.reg_lambda
    )

    # ------------------------------------------------------------------
    # 9. Feature importance (Random Forest on current features)
    # ------------------------------------------------------------------
    logger.info("Computing feature importance...")
    feature_cols = [c for c in df_preds.columns if c.startswith("feat_")]
    X = df_preds[feature_cols].fillna(0)
    y = (df_preds["pred_outcome"] == df_preds["actual_outcome"]).astype(int)

    rf = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    importances = dict(zip(feature_cols, map(float, rf.feature_importances_)))
    importances = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))

    # ------------------------------------------------------------------
    # 10. Risk of ruin
    # ------------------------------------------------------------------
    win_rate = (df_preds["pred_outcome"] == df_preds["actual_outcome"]).mean()
    ror = monte_carlo_risk_of_ruin(
        win_rate=win_rate,
        avg_odds=2.5,
        kelly_fraction=0.25,
        n_sims=10000,
    )

    # ------------------------------------------------------------------
    # Compile report
    # ------------------------------------------------------------------
    report = {
        "model": "FootballPoissonModelV2",
        "dataset": str(data_path),
        "n_train": len(df_train),
        "n_test": len(df_test),
        "calibration_per_outcome": calibration_results,
        "overall_ece": overall_ece,
        "roi": float(roi),
        "t_statistic": float(t_stat),
        "p_value_roi": float(p_value),
        "kelly_analysis": kelly_analysis,
        "halflife_grid_search": halflife_results,
        "regularization_grid_search": reg_results,
        "overfit_diagnostic": overfit_diag,
        "feature_importance": importances,
        "risk_of_ruin_mc": ror,
        "win_rate_actual": float(win_rate),
    }

    report_path = output_dir / "diagnostic_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    # ------------------------------------------------------------------
    # Print summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("MODEL DIAGNOSTIC REPORT")
    print("=" * 80)
    print(f"Overall ECE: {overall_ece:.4f} {'PASS' if overall_ece < 0.05 else 'FAIL'}")
    print(f"Win rate (actual): {win_rate:.1%}")
    print(f"ROI (fair odds): {roi:.2%}")
    print(f"p-value (ROI): {p_value:.4f} {'PASS' if p_value < 0.05 else 'NOT SIGNIFICANT'}")
    print(f"Risk of Ruin (MC): {ror:.2%}")
    print(f"Kelly ratio (rec/ideal): {kelly_analysis['kelly_ratio']:.2f}")
    print(f"\nOverfit: {'YES' if overfit_diag['is_overfitting'] else 'No'}")
    if overfit_diag["is_overfitting"]:
        print(f"  Gap: {overfit_diag['gap']:.2%}")
    print(f"\nOptimal halflife: {halflife_results['optimal_halflife']:.0f} days")
    print(f"Optimal lambda: {reg_results['optimal_lambda']:.2f}")
    print("\nTop 5 features:")
    for i, (feat, imp) in enumerate(list(importances.items())[:5], 1):
        print(f"  {i}. {feat}: {imp:.4f}")
    print("\nCalibration per outcome:")
    for out, res in calibration_results.items():
        print(f"  {out}: ECE={res['ece']:.4f}, Brier={res['brier_score']:.4f}")
    print("=" * 80)
    print(f"Full report saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Model Diagnostic")
    parser.add_argument("--data", type=str, default="data/bronze/matches_football_real.parquet")
    parser.add_argument("--output", type=str, default="models/diagnostics")
    args = parser.parse_args()

    data_path = PROJECT_ROOT / args.data
    if not data_path.exists():
        # Try alternative paths
        for alt_name in ["matches_football_real_odds.parquet", "matches_football_real.parquet"]:
            alt = PROJECT_ROOT / "data" / "bronze" / alt_name
            if alt.exists():
                data_path = alt
                break
        else:
            logger.error(
                "Data file not found: %s. Run: scripts/ingest_real_data.py --seasons 2122 2223 2324",
                data_path,
            )
            sys.exit(1)

    run_diagnostic(data_path, PROJECT_ROOT / args.output)


if __name__ == "__main__":
    main()
