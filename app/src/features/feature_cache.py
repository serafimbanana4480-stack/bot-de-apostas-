"""
Feature cache with hash-based invalidation — avoids redundant feature computation.

Problem: Features are recalculated on every pipeline run, even when the
source data hasn't changed. For long backtests, this wastes 70-90% of
compute time.

Solution: Cache computed features in Parquet, keyed by a hash of the
source data. If the source data hash matches, reuse the cached features.
Automatic invalidation when source data changes (new results, news, etc.).

Usage:
    from src.features.feature_cache import FeatureCache

    cache = FeatureCache(cache_dir="data/feature_cache")

    # Compute or load features
    features = cache.get_or_compute(
        key="football_2024",
        source_df=raw_matches_df,
        compute_fn=lambda df: build_features(df),
    )
    # If raw_matches_df hasn't changed, features are loaded from cache
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, List

import pandas as pd

logger = logging.getLogger("feature_cache")


class FeatureCache:
    """
    Hash-based feature cache with automatic invalidation.

    Cache structure:
        cache_dir/
            {key}/
                features.parquet      — cached feature DataFrame
                metadata.json         — source hash, timestamp, shape info
    """

    def __init__(
        self,
        cache_dir: str = "data/feature_cache",
        max_age_hours: float = 24.0,
        compress: bool = True,
    ):
        """
        Args:
            cache_dir: Root directory for feature cache
            max_age_hours: Maximum cache age before forced recomputation
            compress: Use Parquet compression (snappy)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_age_hours = max_age_hours
        self.compress = compress

        self._hits = 0
        self._misses = 0

    def _compute_hash(self, df: pd.DataFrame) -> str:
        """Compute a hash of the source DataFrame for cache key validation."""
        # Hash based on: shape, column names, and a sample of values
        hasher = hashlib.sha256()

        # Shape and columns
        hasher.update(f"{df.shape}".encode())
        hasher.update(f"{list(df.columns)}".encode())

        # Sample values (first/last rows + dtypes) — avoids hashing entire DF
        for col in sorted(df.columns):
            hasher.update(f"{df[col].dtype}".encode())
            if len(df) > 0:
                # Hash first and last 10 values + count of NaNs
                sample = df[col].iloc[:10].tolist() + df[col].iloc[-10:].tolist()
                nan_count = int(df[col].isna().sum())
                hasher.update(f"{sample}{nan_count}".encode())

        # Index hash (ensures row order matters)
        if len(df) > 0:
            hasher.update(f"{df.index[0]}{df.index[-1]}".encode())

        return hasher.hexdigest()[:16]  # 16 chars is plenty for collision avoidance

    def _cache_path(self, key: str) -> Path:
        """Get the cache directory for a given key."""
        path = self.cache_dir / key
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _is_valid(
        self,
        key: str,
        source_hash: str,
    ) -> bool:
        """Check if cached features are valid for the current source data."""
        cache_path = self._cache_path(key)
        meta_path = cache_path / "metadata.json"
        feat_path = cache_path / "features.parquet"

        if not meta_path.exists() or not feat_path.exists():
            return False

        try:
            with open(meta_path) as f:
                meta = json.load(f)
        except (json.JSONDecodeError, OSError):
            return False

        # Check hash match
        if meta.get("source_hash") != source_hash:
            return False

        # Check age
        cache_age_hours = (time.time() - meta.get("timestamp", 0)) / 3600
        if cache_age_hours > self.max_age_hours:
            logger.info("Cache expired for '%s' (%.1f hours old)", key, cache_age_hours)
            return False

        return True

    def get_or_compute(
        self,
        key: str,
        source_df: pd.DataFrame,
        compute_fn: Callable[[pd.DataFrame], pd.DataFrame],
        force_recompute: bool = False,
    ) -> pd.DataFrame:
        """
        Get features from cache, or compute and cache them.

        Args:
            key: Cache key (e.g., "football_2024")
            source_df: Source data DataFrame (used for hash)
            compute_fn: Function that computes features from source data
            force_recompute: If True, always recompute

        Returns:
            Feature DataFrame (from cache or freshly computed)
        """
        source_hash = self._compute_hash(source_df)

        if not force_recompute and self._is_valid(key, source_hash):
            # Cache hit
            cache_path = self._cache_path(key)
            feat_path = cache_path / "features.parquet"
            try:
                features = pd.read_parquet(feat_path)
                self._hits += 1
                logger.info(
                    "Cache HIT for '%s' (%d rows, %d cols)",
                    key, len(features), len(features.columns),
                )
                return features
            except Exception as e:
                logger.warning("Cache read failed for '%s': %s — recomputing", key, e)

        # Cache miss — compute features
        self._misses += 1
        logger.info("Cache MISS for '%s' — computing features", key)

        start_time = time.time()
        features = compute_fn(source_df)
        elapsed = time.time() - start_time

        # Store in cache
        cache_path = self._cache_path(key)
        feat_path = cache_path / "features.parquet"
        meta_path = cache_path / "metadata.json"

        try:
            features.to_parquet(feat_path, compression="snappy" if self.compress else None)

            meta = {
                "source_hash": source_hash,
                "source_shape": list(source_df.shape),
                "feature_shape": list(features.shape),
                "feature_columns": list(features.columns),
                "timestamp": time.time(),
                "compute_time_seconds": round(elapsed, 2),
            }
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=2)

            logger.info(
                "Cached features for '%s': %d rows, %d cols (%.1fs compute)",
                key, len(features), len(features.columns), elapsed,
            )
        except Exception as e:
            logger.warning("Cache write failed for '%s': %s", key, e)

        return features

    def invalidate(self, key: str) -> bool:
        """Manually invalidate cache for a given key."""
        cache_path = self._cache_path(key)
        feat_path = cache_path / "features.parquet"
        meta_path = cache_path / "metadata.json"

        removed = False
        for p in (feat_path, meta_path):
            if p.exists():
                p.unlink()
                removed = True

        if removed:
            logger.info("Cache invalidated for '%s'", key)
        return removed

    def invalidate_all(self) -> int:
        """Invalidate all cached features."""
        count = 0
        for key_dir in self.cache_dir.iterdir():
            if key_dir.is_dir():
                for f in key_dir.glob("*.parquet"):
                    f.unlink()
                    count += 1
                for f in key_dir.glob("*.json"):
                    f.unlink()
        logger.info("Invalidated %d cache entries", count)
        return count

    def list_entries(self) -> List[Dict[str, Any]]:
        """List all cache entries with metadata."""
        entries = []
        for key_dir in sorted(self.cache_dir.iterdir()):
            if not key_dir.is_dir():
                continue
            meta_path = key_dir / "metadata.json"
            feat_path = key_dir / "features.parquet"

            entry = {"key": key_dir.name}
            if meta_path.exists():
                try:
                    with open(meta_path) as f:
                        meta = json.load(f)
                    entry.update({
                        "source_hash": meta.get("source_hash"),
                        "feature_shape": meta.get("feature_shape"),
                        "age_hours": round((time.time() - meta.get("timestamp", 0)) / 3600, 1),
                        "compute_time": meta.get("compute_time_seconds"),
                    })
                except Exception:
                    pass
            entry["has_features"] = feat_path.exists()
            entries.append(entry)
        return entries

    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 4),
            "entries": len(list(self.cache_dir.iterdir())),
        }
