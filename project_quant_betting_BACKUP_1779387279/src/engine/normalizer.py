"""
Odds Normalization Engine.
Converts various odds formats to a universal decimal format.
"""
from src.core.interfaces import BaseMarketNormalizer
from typing import Any

class UniversalMarketNormalizer(BaseMarketNormalizer):
    def normalize(self, raw_odds: float, format_in: str) -> float:
        """
        Normalizes odds from different formats to decimal.
        """
        if format_in == 'decimal':
            return raw_odds
            
        if format_in == 'american':
            if raw_odds > 0:
                return (raw_odds / 100.0) + 1.0
            else:
                return (100.0 / abs(raw_odds)) + 1.0
                
        if format_in == 'fractional':
            return raw_odds + 1.0
            
        raise ValueError(f"Unknown odds format: {format_in}")
