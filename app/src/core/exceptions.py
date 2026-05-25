"""
Core Exceptions for the VBQ-UNIFIED System.
"""

class VBQError(Exception):
    """Base exception for all custom VBQ errors."""
    pass

class DataIngestionError(VBQError):
    """Raised when data ingestion from an external API fails."""
    pass

class FeatureEngineeringError(VBQError):
    """Raised when there is an error calculating features."""
    pass

class ModelPredictionError(VBQError):
    """Raised when a model fails to make a prediction."""
    pass

class RiskLimitExceeded(VBQError):
    """Raised when a bet is blocked by circuit breakers."""
    pass
