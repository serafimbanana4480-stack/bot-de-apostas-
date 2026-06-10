"""
Safe model serialization using joblib + SHA-256 integrity verification.

Replaces raw pickle to mitigate deserialization RCE vulnerabilities.
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

import joblib

logger = logging.getLogger(__name__)


def _compute_sha256(path: Path) -> str:
    """Compute SHA-256 hex digest of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_save(obj: Any, path: str) -> str:
    """
    Save object with joblib and write SHA-256 hash sidecar file.

    Returns:
        SHA-256 hex digest of the saved file.
    """
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(obj, path_obj)
    digest = _compute_sha256(path_obj)

    hash_path = path_obj.with_suffix(path_obj.suffix + ".sha256")
    with open(hash_path, "w", encoding="utf-8") as f:
        f.write(digest)

    logger.info("Saved object to %s (SHA-256: %s)", path_obj, digest)
    return digest


def safe_load(path: str) -> Any:
    """
    Load object with joblib and verify SHA-256 integrity.

    Raises:
        RuntimeError: If hash file missing or integrity check fails.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Model file not found: {path_obj}")

    hash_path = path_obj.with_suffix(path_obj.suffix + ".sha256")
    if not hash_path.exists():
        raise RuntimeError(
            f"Integrity hash missing for {path_obj}. "
            "Refusing to load untrusted artifact."
        )

    with open(hash_path, "r", encoding="utf-8") as f:
        expected_hash = f.read().strip()

    actual_hash = _compute_sha256(path_obj)
    if actual_hash != expected_hash:
        raise RuntimeError(
            f"Integrity check FAILED for {path_obj}. "
            f"Expected {expected_hash}, got {actual_hash}. "
            "Artifact may be tampered with."
        )

    obj = joblib.load(path_obj)
    logger.info("Loaded object from %s (integrity verified)", path_obj)
    return obj
