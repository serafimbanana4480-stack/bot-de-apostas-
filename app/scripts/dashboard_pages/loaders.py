"""Data loaders — cached access to JSON reports and Parquet data."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.data.local_store import LocalDataStore


@st.cache_data(ttl=60)
def load_reports(data_dir: str = "data") -> dict:
    """Load all JSON reports from data/reports/."""
    reports_path = Path(data_dir) / "reports"
    reports: dict = {}
    if reports_path.exists():
        for f in sorted(reports_path.glob("*.json")):
            try:
                with open(f) as fp:
                    reports[f.name] = json.load(fp)
            except Exception:
                pass
    return reports


@st.cache_data(ttl=60)
def load_clv_report(data_dir: str = "data") -> dict:
    """Load latest CLV report."""
    path = Path(data_dir) / "reports" / "clv_report.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


@st.cache_data(ttl=60)
def load_train_report(data_dir: str = "data") -> dict:
    """Load latest training report."""
    path = Path(data_dir) / "reports" / "last_football_train.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


@st.cache_data(ttl=60)
def load_backtest_reports(data_dir: str = "data") -> list[dict]:
    """Load all backtest reports."""
    reports_path = Path(data_dir) / "reports"
    backtests: list[dict] = []
    if reports_path.exists():
        for f in sorted(reports_path.glob("backtest_*.json")):
            if "comparison" in f.name or "paper" in f.name:
                continue  # Skip non-backtest files that match glob
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    data["_filename"] = f.name
                    backtests.append(data)
            except Exception:
                pass
    return backtests


@st.cache_data(ttl=60)
def load_daily_reports(data_dir: str = "data") -> list[dict]:
    """Load all daily reports."""
    reports_path = Path(data_dir) / "reports"
    dailies: list[dict] = []
    if reports_path.exists():
        for f in sorted(reports_path.glob("daily_*.json")):
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    data["_filename"] = f.name
                    dailies.append(data)
            except Exception:
                pass
    return dailies


@st.cache_data(ttl=60)
def load_data_lake(data_dir: str = "data") -> pd.DataFrame:
    """Load match data from bronze layer."""
    store = LocalDataStore(data_dir)
    df = store.load_matches("football_mock")
    if df.empty:
        csv = Path(data_dir) / "mock_football.csv"
        if csv.exists():
            df = pd.read_csv(csv)
    return df


@st.cache_data(ttl=60)
def load_paper_comparison(data_dir: str = "data") -> dict:
    """Load backtest vs paper trading comparison."""
    path = Path(data_dir) / "reports" / "backtest_paper_comparison.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


@st.cache_data(ttl=60)
def load_financial_viability(data_dir: str = "data") -> dict:
    """Load financial viability report."""
    path = Path(data_dir) / "reports" / "financial_viability.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


@st.cache_data(ttl=60)
def load_bankroll_simulation(data_dir: str = "data") -> dict:
    """Load bankroll simulation report."""
    path = Path(data_dir) / "reports" / "bankroll_simulation.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}
