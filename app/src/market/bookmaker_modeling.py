
class BookmakerBehaviorModel:
    """
    Profiles bookmakers according to their margin structures, biases, 
    and sensitivity to sharp money movements.
    """
    def __init__(self):
        # Configuration presets for major bookmaker styles
        self.profiles = {
            "pinnacle": {
                "efficiency": 0.98,
                "margin_multiplier": 0.02, # ~2% margin
                "sharp_sensitivity": 0.95,  # quick to move on sharp money
                "bias_profile": "efficient_market"
            },
            "bet365": {
                "efficiency": 0.88,
                "margin_multiplier": 0.05, # ~5% margin
                "sharp_sensitivity": 0.40,  # slower to move, relies on manual caps/bans
                "bias_profile": "favourite_bias"
            },
            "betfair_exchange": {
                "efficiency": 0.96,
                "margin_multiplier": 0.0,   # commissions calculated separately
                "sharp_sensitivity": 0.90,  # purely peer-to-peer liquidity driven
                "bias_profile": "near_efficient"
            }
        }

    def decompose_margin(self, odds_home: float, odds_away: float) -> float:
        """
        Decomposes market book margin.
        Margin = (1/odds_home) + (1/odds_away) - 1.0
        """
        if odds_home <= 0 or odds_away <= 0:
            return 0.0
        return float((1.0 / odds_home) + (1.0 / odds_away) - 1.0)

    def get_responsiveness_score(self, provider: str) -> float:
        """
        Returns responsiveness score indicating how fast the bookmaker moves lines.
        """
        key = provider.lower()
        if key in self.profiles:
            return self.profiles[key]["sharp_sensitivity"]
        return 0.50 # default
