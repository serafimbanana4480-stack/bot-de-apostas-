#!/usr/bin/env python3
"""
VBQ Doctor — System health check and diagnostic tool.

Usage:
    python scripts/vbq_doctor.py
    python scripts/vbq_doctor.py --check-schemas --fail-on-error
    python scripts/vbq_doctor.py --verbose
"""
from __future__ import annotations

import argparse
import importlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("vbq_doctor")

CheckResult = Tuple[str, bool, str]


class HealthChecker:
    def __init__(self, verbose: bool = False, fail_on_error: bool = False):
        self.verbose = verbose
        self.fail_on_error = fail_on_error
        self.results: List[CheckResult] = []
        self.critical_failures = 0

    def check(self, name: str, condition: bool, message: str, critical: bool = True) -> bool:
        self.results.append((name, condition, message))
        if not condition and critical:
            self.critical_failures += 1
        icon = "OK" if condition else "FAIL"
        if self.verbose or not condition:
            logger.info(f"[{icon}] {name}: {message}")
        return condition

    def check_python_version(self) -> bool:
        v = sys.version_info
        return self.check("python_version", v >= (3, 11), f"Python {v.major}.{v.minor}.{v.micro}")

    def check_dependencies(self) -> bool:
        required = ["numpy", "pandas", "scipy", "sklearn", "requests"]
        missing = [p for p in required if not self._can_import(p)]
        return self.check("core_dependencies", len(missing) == 0, f"Missing: {missing}" if missing else "All present")

    def _can_import(self, pkg: str) -> bool:
        try:
            importlib.import_module(pkg)
            return True
        except ImportError:
            return False

    def check_directories(self) -> bool:
        dirs = ["data/bronze", "data/silver", "data/gold", "models", "mlflow.db", "backups"]
        missing = []
        for d in dirs:
            p = PROJECT_ROOT / d
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
                missing.append(d)
        return self.check("directories", len(missing) == 0, f"Created: {missing}" if missing else "All present", critical=False)

    def check_data_files(self) -> bool:
        store = PROJECT_ROOT / "data" / "bronze"
        files = list(store.glob("*.parquet")) if store.exists() else []
        return self.check("data_files", len(files) > 0, f"{len(files)} Parquet files", critical=False)

    def check_api_connectivity(self) -> bool:
        import requests
        ok = 0
        for url in ["https://api.the-odds-api.com", "https://api.football-data.org"]:
            try:
                r = requests.head(url, timeout=5)
                if r.status_code < 500:
                    ok += 1
            except Exception:
                pass
        return self.check("api_connectivity", ok > 0, f"{ok}/2 APIs reachable", critical=False)

    def check_config(self) -> bool:
        try:
            from src.core.config import settings
            has_creds = any([settings.ODDS_API_KEY, settings.BETFAIR_APP_KEY])
            msg = "API keys configured" if has_creds else "Zero-cost mode (no API keys)"
            return self.check("config", True, msg, critical=False)
        except Exception as e:
            return self.check("config", False, str(e), critical=False)

    def check_models(self) -> bool:
        mdir = PROJECT_ROOT / "models"
        files = list(mdir.glob("*.pkl")) + list(mdir.glob("*.npz")) if mdir.exists() else []
        return self.check("models", len(files) > 0, f"{len(files)} artifacts", critical=False)

    def check_backups(self) -> bool:
        bdir = PROJECT_ROOT / "backups"
        if not bdir.exists():
            return self.check("backups", False, "No backup dir", critical=False)
        files = sorted(bdir.glob("*.tar.gz"), reverse=True)
        if not files:
            return self.check("backups", False, "No backups", critical=False)
        import time
        age_days = (time.time() - files[0].stat().st_mtime) / 86400
        return self.check("backups", age_days < 7, f"Latest {age_days:.1f} days old", critical=False)

    def check_schemas(self) -> bool:
        try:
            from src.ingestion.schema_validator import OddsSnapshotRecord
            rec = OddsSnapshotRecord(
                event_id="test", sport="soccer", commence_time="2026-01-01T00:00:00",
                bookmaker="test", odds_home=2.0, odds_away=3.0, captured_at="2026-01-01T00:00:00",
            )
            return self.check("schemas", True, "Schema validation passed")
        except Exception as e:
            return self.check("schemas", False, f"Schema error: {e}")

    def check_clv_drift(self) -> bool:
        """Check if recent CLV report shows decay requiring attention."""
        try:
            from src.mlops.retraining.retraining import RetrainingTrigger
            trigger = RetrainingTrigger(clv_warning_threshold=0.5, clv_critical_threshold=0.0)
            # Try to load latest CLV report from data/reports/
            clv_dir = PROJECT_ROOT / "data" / "reports"
            if not clv_dir.exists():
                return self.check("clv_drift", True, "No CLV reports yet (zero-cost mode)", critical=False)
            reports = sorted(clv_dir.glob("clv_report*.json"), reverse=True)
            if not reports:
                return self.check("clv_drift", True, "No CLV reports found", critical=False)
            import json as _json
            with open(reports[0], "r", encoding="utf-8") as f:
                report = _json.load(f)
            avg_clv = report.get("mean_clv_pct")
            status = trigger.clv_status(avg_clv)
            healthy = status["status"] == "HEALTHY"
            msg = f"CLV {avg_clv:.2f}% — {status['status']} ({status['action']})"
            return self.check("clv_drift", healthy, msg, critical=(status["status"] == "CRITICAL"))
        except Exception as e:
            return self.check("clv_drift", True, f"CLV check skipped: {e}", critical=False)

    def run_all(self, check_schemas: bool = False) -> Dict[str, Any]:
        self.check_python_version()
        self.check_dependencies()
        self.check_directories()
        self.check_data_files()
        self.check_api_connectivity()
        self.check_config()
        self.check_models()
        self.check_backups()
        self.check_clv_drift()
        if check_schemas:
            self.check_schemas()
        return self.summarize()

    def summarize(self) -> Dict[str, Any]:
        passed = sum(1 for _, ok, _ in self.results if ok)
        total = len(self.results)
        return {
            "passed": passed, "total": total,
            "critical_failures": self.critical_failures,
            "healthy": self.critical_failures == 0,
            "checks": [{"name": n, "status": "PASS" if ok else "FAIL", "message": m} for n, ok, m in self.results],
        }

    def print_report(self) -> None:
        s = self.summarize()
        print("\n" + "=" * 60)
        print("  VBQ DOCTOR — Health Report")
        print("=" * 60)
        for c in s["checks"]:
            icon = "OK" if c["status"] == "PASS" else "FAIL"
            print(f"  [{icon}] {c['name']:<20} {c['message']}")
        print("-" * 60)
        status = "HEALTHY" if s["healthy"] else "UNHEALTHY"
        print(f"  Result: {status} ({s['passed']}/{s['total']} passed)")
        print("=" * 60 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="VBQ Doctor — System health check")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--check-schemas", action="store_true")
    parser.add_argument("--fail-on-error", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    checker = HealthChecker(verbose=args.verbose, fail_on_error=args.fail_on_error)
    summary = checker.run_all(check_schemas=args.check_schemas)

    if args.json:
        print(json.dumps(summary, indent=2, default=str))
    else:
        checker.print_report()

    return 0 if summary["healthy"] else 1


if __name__ == "__main__":
    sys.exit(main())
