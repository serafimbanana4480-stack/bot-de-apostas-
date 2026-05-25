import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

import pandas as pd


class FeatureStoreRegistry:
    """
    Simulates a versioned Feature Store registry tracking schema hashes and metadata.
    Ensures offline/online parity and reproducibility.
    """
    def __init__(self, registry_dir: str = "models/feature_store"):
        self.registry_dir = registry_dir
        os.makedirs(self.registry_dir, exist_ok=True)

    def calculate_schema_hash(self, df: pd.DataFrame) -> str:
        """
        Generates a SHA-256 hash representing the feature schema (columns and types).
        """
        # Create a representation of columns and data types
        schema_info = {
            col: str(dtype) for col, dtype in df.dtypes.items()
        }
        schema_str = json.dumps(schema_info, sort_keys=True)
        return hashlib.sha256(schema_str.encode("utf-8")).hexdigest()

    def register_dataset(self, df: pd.DataFrame, version: str, sport: str = "NBA", market: str = "Moneyline") -> Dict[str, Any]:
        """
        Registers a dataset version, storing its schema hash and volume metrics.
        """
        schema_hash = self.calculate_schema_hash(df)
        
        metadata = {
            "feature_version": version,
            "schema_hash": schema_hash,
            "columns": list(df.columns),
            "num_rows": len(df),
            "num_cols": len(df.columns),
            "sport": sport,
            "market": market,
            "registered_at": datetime.now(timezone.utc).isoformat()
        }
        
        registry_path = os.path.join(self.registry_dir, f"metadata_v{version}.json")
        with open(registry_path, "w") as f:
            json.dump(metadata, f, indent=4)
            
        return metadata

    def verify_parity(self, df: pd.DataFrame, reference_version: str) -> bool:
        """
        Verifies if the current DataFrame schema matches the registered reference schema version.
        """
        registry_path = os.path.join(self.registry_dir, f"metadata_v{reference_version}.json")
        if not os.path.exists(registry_path):
            raise FileNotFoundError(f"Feature metadata version {reference_version} not found in registry.")
            
        with open(registry_path) as f:
            metadata = json.load(f)
            
        current_hash = self.calculate_schema_hash(df)
        return current_hash == metadata["schema_hash"]
