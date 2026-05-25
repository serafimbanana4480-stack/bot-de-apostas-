"""Export utilities — CSV/PDF download for visible reports."""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import streamlit as st


def export_csv_button(df: pd.DataFrame, filename: str = "export.csv", label: str = "Export CSV") -> None:
    """Add a CSV download button for a DataFrame."""
    if df.empty:
        return
    csv = df.to_csv(index=False).encode("utf-8")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    fname = f"vbq_{filename.replace('.csv', '')}_{timestamp}.csv"
    st.download_button(label, data=csv, file_name=fname, mime="text/csv")


def export_json_button(data: dict | list, filename: str = "export.json", label: str = "Export JSON") -> None:
    """Add a JSON download button for report data."""
    import json
    if not data:
        return
    json_str = json.dumps(data, indent=2, default=str).encode("utf-8")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    fname = f"vbq_{filename.replace('.json', '')}_{timestamp}.json"
    st.download_button(label, data=json_str, file_name=fname, mime="application/json")
