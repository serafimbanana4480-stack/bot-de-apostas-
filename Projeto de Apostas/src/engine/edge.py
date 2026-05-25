"""
Edge Detection Engine.
Calculates CLV and expected edge for opportunities.
"""
from typing import Any, Dict


def calculate_clv(opening_odds: float, closing_odds: float) -> float:
    """
    Calculates the Closed Line Value.
    
    Args:
        opening_odds: Decimal odds at time of bet.
        closing_odds: Decimal odds at closing.
        
    Returns:
        CLV as a percentage.
    """
    if closing_odds <= 0:
        return 0.0
    clv = (opening_odds / closing_odds) - 1
    return clv * 100.0

def calculate_clv_proxy(current_odds: float, market_consensus: float) -> float:
    if market_consensus <= 0:
        return 0.0
    clv_proxy = (current_odds / market_consensus) - 1
    return clv_proxy * 100.0

def calculate_edge(model_probability: float, bookmaker_odds: float) -> float:
    """
    Calculates expected edge.
    
    Args:
        model_probability: Float between 0 and 1.
        bookmaker_odds: Decimal odds.
        
    Returns:
        Edge as a percentage.
    """
    edge = (model_probability * bookmaker_odds) - 1
    return edge * 100.0

def apply_quality_filters(opportunity: Dict[str, Any], filters_config: Dict[str, Any]) -> bool:
    """
    Applies quality filters to reject false positive opportunities.
    """
    odds = opportunity.get('odds', 0.0)
    prob = opportunity.get('probability', 0.0)
    
    if not (filters_config['min_odds'] <= odds <= filters_config['max_odds']):
        return False
        
    if not (filters_config['min_probability'] <= prob <= filters_config['max_probability']):
        return False
        
    if opportunity.get('clv', 0.0) < filters_config.get('min_clv', -100.0):
        return False
        
    return True
