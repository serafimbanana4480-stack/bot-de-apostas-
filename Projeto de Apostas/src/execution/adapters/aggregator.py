from typing import Any, Dict, List


class OddsAggregator:
    """
    Aggregates odds from different providers and converts them to decimal format.
    Checks for latency arbitrage opportunities.
    """
    def __init__(self):
        pass

    def normalize_odds(self, provider_odds: Dict[str, Any]) -> Dict[str, float]:
        """
        Converts odds to a uniform decimal format.
        Input format: {'Pinnacle': 1.95, 'Betfair_Lay': 2.02, 'DecimalOddsProvider': 1.91}
        """
        normalized = {}
        for provider, val in provider_odds.items():
            if isinstance(val, (int, float)) and val > 1.0:
                normalized[provider] = float(val)
        return normalized

    def detect_latency_arbitrage(
        self, 
        normalized_odds: Dict[str, float], 
        reference_provider: str = "Pinnacle",
        threshold: float = 0.05
    ) -> List[Dict[str, Any]]:
        """
        Scans for opportunities where lagging providers haven't aligned with a fast reference market.
        If a target bookmaker is offering odds higher than Pinnacle's reference odds + threshold,
        it suggests a latency arb.
        """
        arbitrages = []
        if reference_provider not in normalized_odds:
            return arbitrages
            
        ref_odds = normalized_odds[reference_provider]
        
        for provider, odds in normalized_odds.items():
            if provider == reference_provider:
                continue
                
            # If lagging provider odds are higher than reference odds,
            # it suggests the lagging provider hasn't updated its price yet.
            if odds > ref_odds * (1.0 + threshold):
                arbitrages.append({
                    "lagging_provider": provider,
                    "reference_provider": reference_provider,
                    "reference_odds": ref_odds,
                    "target_odds": odds,
                    "expected_value_edge": (odds / ref_odds) - 1.0
                })
                
        return arbitrages
