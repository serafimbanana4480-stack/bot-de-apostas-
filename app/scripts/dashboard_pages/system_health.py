"""System Health page — environment, data lake status, API connectivity, test runner."""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

from src.data.local_store import LocalDataStore
from src.core.config import settings


@st.cache_data(ttl=300, show_spinner=False)
def _check_api_connectivity() -> dict[str, str]:
    """Check external API connectivity (cached for 5 min, not on every render)."""
    results = {}
    try:
        import requests
        try:
            r = requests.head("https://api.football-data.org", timeout=5)
            results["football-data.org"] = "Accessible" if r.status_code < 500 else f"Error {r.status_code}"
        except Exception as e:
            results["football-data.org"] = f"Unreachable ({type(e).__name__})"
    except ImportError:
        results["football-data.org"] = "requests not installed"

    return results


def render_system_health(data_dir: str, dark: bool = True) -> None:
    """Render system health dashboard (with cached API checks)."""
    st.header("System Health")

    # ── Environment ──
    st.subheader("Environment")
    env_data = {
        "ZERO_COST_MODE": settings.ZERO_COST_MODE,
        "PAPER_TRADING_ONLY": settings.PAPER_TRADING_ONLY,
        "DATA_DIR": settings.DATA_DIR,
        "MLFLOW_TRACKING_URI": settings.MLFLOW_TRACKING_URI,
        "Python Version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
    for k, v in env_data.items():
        st.text(f"{k}: {v}")

    # ── Data Lake Status ──
    st.subheader("Data Lake Status")
    store = LocalDataStore(data_dir)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        bronze_path = Path(data_dir) / "bronze"
        bronze = len(list(bronze_path.glob("*.parquet"))) if bronze_path.exists() else 0
        st.metric("Bronze Files", bronze)
    with c2:
        reports_path = Path(data_dir) / "reports"
        reports = len(list(reports_path.glob("*.json"))) if reports_path.exists() else 0
        st.metric("Reports", reports)
    with c3:
        # Fixed: models/ path with try/except
        try:
            models_path = Path(data_dir) / "models"
            if not models_path.exists():
                models_path = Path("models")
            models = len(list(models_path.glob("*.pkl"))) + len(list(models_path.glob("**/*.pkl")))
        except (FileNotFoundError, OSError):
            models = 0
        st.metric("Models", models)
    with c4:
        st.metric("MLflow URI", "SQLite" if "sqlite" in settings.MLFLOW_TRACKING_URI else "Remote")

    # ── Test Suite ──
    st.subheader("Test Suite")
    if st.button("Run Tests"):
        with st.spinner("Running tests..."):
            import subprocess
            project_root = Path(__file__).resolve().parent.parent.parent
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=str(project_root),
                timeout=120,
            )
            if result.returncode == 0:
                st.success("All tests passed!")
            else:
                st.error("Some tests failed")
            st.code(result.stdout[-2000:], language="bash")

    # ── API Connectivity (FIXED: cached, not synchronous on every render) ──
    st.subheader("External API Status")
    with st.spinner("Checking API connectivity..."):
        api_results = _check_api_connectivity()
    for api, status in api_results.items():
        if "Accessible" in status:
            st.success(f"{api}: {status}")
        else:
            st.error(f"{api}: {status}")
