from typing import Dict, List, Tuple


class BookmakerLimitsTracker:
    """
    Registers and tracks money wagered in rolling periods across different bookmakers.
    Prevents saturation and individual profile limiting.
    """
    def __init__(self, limit_per_bookmaker: float = 1000.0):
        self.limit_per_bookmaker = limit_per_bookmaker
        # Stores running total of exposure per bookmaker
        self.exposure: Dict[str, float] = {}

    def record_bet(self, bookmaker: str, amount: float) -> None:
        self.exposure[bookmaker] = self.exposure.get(bookmaker, 0.0) + amount

    def get_available_capacity(self, bookmaker: str) -> float:
        current_wagered = self.exposure.get(bookmaker, 0.0)
        return max(0.0, self.limit_per_bookmaker - current_wagered)

    def reset_exposure(self) -> None:
        self.exposure.clear()


class StakeSplitter:
    """
    Splits larger stakes across multiple bookmakers based on their available liquidity and exposure capacities.
    """
    def __init__(self, limits_tracker: BookmakerLimitsTracker):
        self.tracker = limits_tracker

    def split_stake(self, total_stake: float, bookmaker_offers: Dict[str, float]) -> List[Tuple[str, float]]:
        """
        Splits total_stake among bookmakers that offer the best available odds.
        bookmaker_offers maps bookmaker name to its currently offered odds.
        """
        if total_stake <= 0:
            return []

        # Sort bookmakers by odds descending to get best price first
        sorted_offers = sorted(bookmaker_offers.items(), key=lambda x: x[1], reverse=True)
        
        splits = []
        remaining_stake = total_stake
        
        for bookmaker, odds in sorted_offers:
            if remaining_stake <= 0:
                break
                
            capacity = self.tracker.get_available_capacity(bookmaker)
            if capacity <= 0:
                continue
                
            allocated = min(remaining_stake, capacity)
            splits.append((bookmaker, allocated))
            remaining_stake -= allocated
            
        return splits
