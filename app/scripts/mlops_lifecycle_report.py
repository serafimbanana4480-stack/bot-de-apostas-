#!/usr/bin/env python3
"""
MLOps Lifecycle Audit Report — validates champion/challenger promotion pipeline.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    print("\n" + "=" * 70)
    print("  MLOPS LIFECYCLE AUDIT REPORT")
    print("=" * 70 + "\n")

    checks = []

    # 1. Champion exists
    champion_path = PROJECT_ROOT / "data" / "models" / "champion" / "football_poisson_champion.pkl"
    champion_metrics_path = PROJECT_ROOT / "data" / "models" / "champion" / "metrics.json"
    check1 = champion_path.exists() and champion_metrics_path.exists()
    checks.append(("Champion model saved", check1))
    print(f"[1] Champion model saved: {'PASS' if check1 else 'FAIL'}")

    # 2. Drift detection
    clv_report_path = PROJECT_ROOT / "data" / "reports" / "clv_report.json"
    report = {}
    check2 = clv_report_path.exists()
    drift_detected = False
    if check2:
        with open(clv_report_path) as f:
            report = json.load(f)
        mean_clv = report.get("mean_clv_pct", 0)
        drift_detected = mean_clv < 0.5
        check2 = drift_detected
    checks.append(("CLV drift detected (<0.5%)", check2))
    print(f"[2] CLV drift detected (<0.5%): {'PASS' if check2 else 'FAIL'} (mean_clv={report.get('mean_clv_pct', 'N/A')}%)")

    # 3. Retraining trigger
    try:
        from src.mlops.retraining.retraining import RetrainingTrigger
        trigger = RetrainingTrigger()
        should = trigger.should_retrain(
            {"psi": 0.35, "brier": 0.22, "ece": 0.10, "avg_clv_pct": -0.70},
            {"psi": 0.05, "brier": 0.18, "ece": 0.04, "avg_clv_pct": 1.36},
        )
        check3 = should is True
    except Exception as e:
        check3 = False
        print(f"[3] Retraining trigger: ERROR {e}")
    checks.append(("Retraining trigger fires", check3))
    print(f"[3] Retraining trigger fires: {'PASS' if check3 else 'FAIL'}")

    # 4. Governance blocks worse models
    try:
        from src.mlops.model_governance.governance import ModelGovernance
        gov = ModelGovernance()
        champion = {"brier": 0.18, "ece": 0.04, "sharpe": 7.23, "max_drawdown": 63.53}
        # Worse challenger
        worse = {"brier": 0.25, "ece": 0.03, "sharpe": 5.0, "max_drawdown": 10.0}
        blocked = gov.validation_gate(worse, champion) is False
        # Better challenger
        better = {"brier": 0.10, "ece": 0.03, "sharpe": 8.0, "max_drawdown": 10.0}
        promoted = gov.validation_gate(better, champion) is True
        check4 = blocked and promoted
    except Exception as e:
        check4 = False
        print(f"[4] Governance gate: ERROR {e}")
    checks.append(("Governance blocks worse / promotes better", check4))
    print(f"[4] Governance blocks worse / promotes better: {'PASS' if check4 else 'FAIL'}")

    # 5. Shadow deployment
    shadow_report = PROJECT_ROOT / "data" / "reports" / "shadow_test.json"
    check5 = shadow_report.exists()
    if check5:
        with open(shadow_report) as f:
            s = json.load(f)
        check5 = s.get("total_tracked", 0) > 0 and s.get("discrepancy_rate", 1.0) >= 0.0
    checks.append(("Shadow deployment works", check5))
    print(f"[5] Shadow deployment works: {'PASS' if check5 else 'FAIL'}")

    # 6. run_pipeline --shadow argument exists
    run_pipeline = (PROJECT_ROOT / "scripts" / "run_pipeline.py").read_text()
    check6 = "--shadow" in run_pipeline
    checks.append(("run_pipeline supports --shadow", check6))
    print(f"[6] run_pipeline supports --shadow: {'PASS' if check6 else 'FAIL'}")

    # Summary
    total = len(checks)
    passed = sum(1 for _, ok in checks if ok)
    print("\n" + "=" * 70)
    print(f"  RESULT: {passed}/{total} checks passed")
    print("=" * 70)

    if passed == total:
        print("\n  [OK] MLOps lifecycle is healthy.")
        return 0
    else:
        print("\n  [!] Some MLOps checks failed — review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
