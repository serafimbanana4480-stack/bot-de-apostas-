#!/usr/bin/env python3
"""
CLI entry point for API health dashboard.

Usage:
    python scripts/api_health_dashboard.py
    python scripts/api_health_dashboard.py --window 6 --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.monitoring.api_health_dashboard import APIHealthDashboard


def main() -> int:
    parser = argparse.ArgumentParser(description="VBQ API Health Dashboard")
    parser.add_argument("--window", type=int, default=24, help="Hours of history to include")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of pretty print")
    parser.add_argument("--record", nargs=3, metavar=("API", "LATENCY_MS", "SUCCESS"),
                        help="Record a sample: API latency_ms success(true/false)")
    args = parser.parse_args()

    dash = APIHealthDashboard()

    if args.record:
        api, lat, succ = args.record
        dash.record(api, float(lat), succ.lower() in ("true", "1", "yes"))
        print(f"Recorded sample for {api}")
        return 0

    report = dash.report(window_hours=args.window)
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        dash.print_report(window_hours=args.window)
    return 0 if report["overall_status"] == "HEALTHY" else 1


if __name__ == "__main__":
    sys.exit(main())
