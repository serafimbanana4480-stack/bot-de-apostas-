"""
Fallback data provider — serves local Parquet data when external APIs are offline.

Provides graceful degradation: try API first, fall back to cached local data,
mark data as stale, and alert if data freshness drops below threshold.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import pandas as pd

from src.core.config import settings
from src.monitoring.metrics import update_data_staleness

logger = logging.getLogger("fallback_provider")


class FallbackProvider:
    """
    Wraps an external API client with local Parquet fallback.

    Strategy:
    1. Try the external API (with retry via tenacity)
    2. If API fails, load from local Parquet cache
    3. Mark data as stale with timestamp
    4. Alert if data is older than threshold
    """

    def __init__(
        self,
        data_dir: Optional[str] = None,
        staleness_threshold_hours: int = 6,
        alert_callback: Optional[Callable] = None,
    ):
        self.data_dir = Path(data_dir or settings.DATA_DIR) / "fallback_cache"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.staleness_threshold_hours = staleness_threshold_hours
        self.alert_callback = alert_callback
        self._last_success_time: Dict[str, float] = {}

    def fetch_with_fallback(
        self,
        source_name: str,
        api_fetch_fn: Callable[[], pd.DataFrame],
        sport: str = "football",
    ) -> Dict[str, Any]:
        """
        Attempt API fetch, fall back to local cache on failure.

        Args:
            source_name: Name of the data source (e.g., "football_data_org")
            api_fetch_fn: Callable that returns a DataFrame from the API
            sport: Sport category for caching

        Returns:
            Dict with: data (DataFrame), source (api/local), stale (bool), error (str|None)
        """
        error = None
        source = "api"

        # Try API first
        try:
            df = api_fetch_fn()
            if df is not None and not df.empty:
                # Cache successful result
                self._save_cache(source_name, sport, df)
                self._last_success_time[source_name] = time.time()
                update_data_staleness(source=source_name, seconds=0)
                return {
                    "data": df,
                    "source": "api",
                    "stale": False,
                    "error": None,
                }
        except Exception as e:
            error = str(e)
            logger.warning("API fetch failed for %s: %s — falling back to local cache", source_name, e)

        # Fallback to local cache
        cached_df = self._load_cache(source_name, sport)
        if cached_df is not None and not cached_df.empty:
            staleness = self._get_staleness(source_name)
            is_stale = staleness > self.staleness_threshold_hours * 3600

            update_data_staleness(source=source_name, seconds=staleness)

            if is_stale and self.alert_callback:
                try:
                    self.alert_callback(
                        level="WARNING",
                        title="Data Stale",
                        message=f"Source {source_name} is using cached data from {staleness/3600:.1f}h ago. API error: {error}",
                        data={"source": source_name, "staleness_hours": round(staleness / 3600, 1)},
                    )
                except Exception:
                    pass

            logger.info(
                "Using cached data for %s (%.1fh old, stale=%s)",
                source_name, staleness / 3600, is_stale,
            )
            return {
                "data": cached_df,
                "source": "local_cache",
                "stale": is_stale,
                "error": error,
            }

        # No cache available either
        logger.error("No data available for %s (API failed, no local cache)", source_name)
        update_data_staleness(source=source_name, seconds=999999)

        return {
            "data": pd.DataFrame(),
            "source": "none",
            "stale": True,
            "error": error or "No data available from API or local cache",
        }

    def _save_cache(self, source_name: str, sport: str, df: pd.DataFrame) -> None:
        """Save DataFrame to local Parquet cache."""
        cache_path = self.data_dir / sport / f"{source_name}.parquet"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path, index=False)
        # Also save metadata with timestamp
        meta_path = self.data_dir / sport / f"{source_name}_meta.json"
        meta_path.write_text(f'{{"cached_at": "{datetime.now(timezone.utc).isoformat()}"}}')

    def _load_cache(self, source_name: str, sport: str) -> Optional[pd.DataFrame]:
        """Load DataFrame from local Parquet cache."""
        cache_path = self.data_dir / sport / f"{source_name}.parquet"
        if not cache_path.exists():
            return None
        try:
            return pd.read_parquet(cache_path)
        except Exception as e:
            logger.warning("Failed to read cache %s: %s", cache_path, e)
            return None

    def _get_staleness(self, source_name: str) -> float:
        """Get seconds since last successful API fetch."""
        last_success = self._last_success_time.get(source_name, 0)
        if last_success == 0:
            # Try reading from metadata
            return 999999.0  # Unknown — assume very stale
        return time.time() - last_success

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached data sources."""
        info = {}
        for sport_dir in self.data_dir.iterdir():
            if sport_dir.is_dir():
                for cache_file in sport_dir.glob("*.parquet"):
                    name = cache_file.stem
                    stat = cache_file.stat()
                    info[f"{sport_dir.name}/{name}"] = {
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
        return info
