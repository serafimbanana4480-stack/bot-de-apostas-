"""Parquet feature store with temporal queries (zero-cost)."""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class ParquetFeatureStore:
    def __init__(self, storage_path: str = "data/gold/feature_vectors"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _hash(self, features: Dict[str, Any]) -> str:
        payload = json.dumps(features, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def save(
        self,
        match_id: str,
        features: Dict[str, float],
        timestamp: Optional[datetime] = None,
    ) -> str:
        ts = timestamp or datetime.now(timezone.utc)
        row = {"match_id": match_id, "timestamp": ts, "hash": self._hash(features), **features}
        df = pd.DataFrame([row])
        partition = ts.strftime("%Y_%m")
        path = self.storage_path / f"features_{partition}.parquet"
        if path.exists():
            existing = pd.read_parquet(path)
            dup = existing[(existing["match_id"] == match_id) & (existing["hash"] == row["hash"])]
            if not dup.empty:
                return row["hash"]
            df = pd.concat([existing, df], ignore_index=True)
        df.to_parquet(path, index=False)
        return row["hash"]

    def get_as_of(self, match_id: str, as_of: datetime) -> Optional[Dict[str, Any]]:
        rows = []
        for f in self.storage_path.glob("features_*.parquet"):
            part = pd.read_parquet(f)
            part = part[(part["match_id"] == match_id) & (part["timestamp"] <= as_of)]
            rows.append(part)
        if not rows:
            return None
        combined = pd.concat(rows).sort_values("timestamp", ascending=False)
        if combined.empty:
            return None
        latest = combined.iloc[0]
        skip = {"match_id", "timestamp", "hash"}
        return {k: float(latest[k]) for k in latest.index if k not in skip}
