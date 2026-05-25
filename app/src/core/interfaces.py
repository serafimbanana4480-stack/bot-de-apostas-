"""
Core Interfaces for the VBQ-UNIFIED System.
This module defines the sport-agnostic architecture.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseSport(ABC):
    """
    Abstract Base Class representing a specific sport implementation.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def get_ingestion_pipeline(self):
        pass
        
    @abstractmethod
    def get_feature_engineer(self):
        pass
        
    @abstractmethod
    def get_model_trainer(self):
        pass


class BaseOddsProvider(ABC):
    """
    Interface for fetching odds from APIs or scrapers.
    """
    @abstractmethod
    def fetch_odds(self, game_id: str, market_type: str) -> Dict[str, Any]:
        pass


class BaseFeatureEngineer(ABC):
    """
    Interface for transforming raw data into ML features.
    """
    @abstractmethod
    def build_features(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        pass


class BaseModelTrainer(ABC):
    """
    Interface for ML Model training and prediction.
    """
    @abstractmethod
    def train(self, X: Any, y: Any) -> None:
        pass
        
    @abstractmethod
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        pass


class BaseMarketNormalizer(ABC):
    """
    Interface to normalize odds from different bookmakers/formats to decimal.
    """
    @abstractmethod
    def normalize(self, raw_odds: Any, format_in: str) -> float:
        pass
