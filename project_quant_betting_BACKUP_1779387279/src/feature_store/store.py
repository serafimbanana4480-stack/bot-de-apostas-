"""
Feature Store Module.
Parquet-based storage for ML features with temporal querying and versioning.
"""
import os
import hashlib
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class FeatureStore:
    """Manages storage and retrieval of ML features using Parquet."""
    
    def __init__(self, storage_path: str = "data/feature_store"):
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        
    def _generate_hash(self, features: Dict[str, Any]) -> str:
        """Generate SHA-256 hash of feature dictionary for versioning."""
        sorted_json = json.dumps(features, sort_keys=True)
        return hashlib.sha256(sorted_json.encode()).hexdigest()[:16]
        
    def save_features(
        self, 
        match_id: str, 
        features: Dict[str, float],
        timestamp: Optional[datetime] = None
    ) -> str:
        """Save a feature vector to the store."""
        if timestamp is None:
            timestamp = datetime.utcnow()
            
        feature_hash = self._generate_hash(features)
        
        # Prepare row
        row = {"match_id": match_id, "timestamp": timestamp, "hash": feature_hash}
        row.update(features)
        
        df = pd.DataFrame([row])
        
        # Partition by year/month for efficiency
        year_month = timestamp.strftime("%Y_%m")
        file_path = os.path.join(self.storage_path, f"features_{year_month}.parquet")
        
        try:
            if os.path.exists(file_path):
                existing_df = pd.read_parquet(file_path)
                
                # Check for duplicates (same match, same hash)
                duplicate = existing_df[
                    (existing_df['match_id'] == match_id) & 
                    (existing_df['hash'] == feature_hash)
                ]
                
                if not duplicate.empty:
                    logger.debug(f"Features for {match_id} with hash {feature_hash} already exist.")
                    return feature_hash
                    
                df = pd.concat([existing_df, df], ignore_index=True)
                
            df.to_parquet(file_path, index=False)
            logger.info(f"Saved features for {match_id} to {file_path}")
            return feature_hash
            
        except Exception as e:
            logger.error(f"Error saving features to store: {str(e)}")
            raise
            
    def get_features_as_of(self, match_id: str, as_of: datetime) -> Optional[Dict[str, Any]]:
        """
        Temporal query: Get features for a match as they existed exactly at a specific time.
        Critical for preventing forward-looking bias in backtesting.
        """
        # Load all relevant partitions (simplified for now to just load all for the match)
        all_files = [f for f in os.listdir(self.storage_path) if f.endswith('.parquet')]
        
        if not all_files:
            return None
            
        dfs = []
        for file in all_files:
            try:
                dfs.append(pd.read_parquet(os.path.join(self.storage_path, file)))
            except Exception:
                continue
                
        if not dfs:
            return None
            
        combined = pd.concat(dfs)
        
        # Filter for match and strict temporal cutoff
        match_features = combined[
            (combined['match_id'] == match_id) & 
            (combined['timestamp'] <= pd.Timestamp(as_of))
        ]
        
        if match_features.empty:
            return None
            
        # Get the most recent valid record before the cutoff
        latest = match_features.sort_values('timestamp', ascending=False).iloc[0]
        
        # Convert back to dict, dropping metadata columns
        result = latest.to_dict()
        for meta_key in ['match_id', 'timestamp', 'hash']:
            result.pop(meta_key, None)
            
        return result
