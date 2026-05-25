"""Session state management — persist filters and settings across page navigation."""
from __future__ import annotations

from typing import Any

import streamlit as st


def init_session_state() -> None:
    """Initialize default session state values if not already set."""
    defaults = {
        "data_dir": "data",
        "dark_mode": True,
        "selected_page": "Overview",
        "clv_min_threshold": 1.0,
        "clv_break_even": 2.565,
        "max_drawdown_pct": 20.0,
        "min_win_rate_pct": 45.0,
        "rolling_window_days": 30,
        "league_filter": [],
        "date_range": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_state(key: str, default: Any = None) -> Any:
    """Get a session state value with optional default."""
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    """Set a session state value."""
    st.session_state[key] = value
