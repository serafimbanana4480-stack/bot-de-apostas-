"""
Kelly Criterion Calculation Module.
"""

def calculate_kelly_fraction(probability: float, odds: float) -> float:
    """
    Calculates the full Kelly fraction.
    
    Args:
        probability: Win probability (0 to 1)
        odds: Decimal odds
        
    Returns:
        Fraction of bankroll to bet (0 to 1). Returns 0 if negative edge.
    """
    b = odds - 1  # Net decimal odds
    p = probability
    q = 1 - p
    
    if b <= 0:
        return 0.0
        
    kelly_fraction = (b * p - q) / b
    
    return max(0.0, kelly_fraction)

def calculate_fractional_kelly(probability: float, odds: float, kelly_multiplier: float = 0.25) -> float:
    """
    Calculates fractional Kelly to reduce volatility.
    
    Args:
        probability: Win probability (0 to 1)
        odds: Decimal odds
        kelly_multiplier: Multiplier for Kelly (default 0.25 for Quarter Kelly)
        
    Returns:
        Fraction of bankroll to bet.
    """
    full_kelly = calculate_kelly_fraction(probability, odds)
    return full_kelly * kelly_multiplier
