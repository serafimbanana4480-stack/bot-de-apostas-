from typing import Any, Dict, List


class PortfolioRiskAllocator:
    """
    Balances capital allocation across concurrent bets.
    Clusters bets by risk factors (e.g. division, game date) to avoid joint drawdown.
    """
    def __init__(self, max_portfolio_exposure: float = 0.20, max_cluster_exposure: float = 0.08):
        self.max_portfolio_exposure = max_portfolio_exposure
        self.max_cluster_exposure = max_cluster_exposure

    def cluster_bets(self, bet_requests: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Groups bets by team or division to track exposure correlation.
        """
        clusters = {}
        for bet in bet_requests:
            # Group by home/away team to avoid double exposure on the same game or teams
            team = bet.get("home_team", "unknown")
            if team not in clusters:
                clusters[team] = []
            clusters[team].append(bet)
        return clusters

    def allocate_capital(
        self, 
        bet_requests: List[Dict[str, Any]], 
        current_bankroll: float
    ) -> List[Dict[str, Any]]:
        """
        Applies portfolio-wide exposure caps. Rescales individual stakes to maintain risk bounds.
        """
        if not bet_requests or current_bankroll <= 0:
            return []
            
        clusters = self.cluster_bets(bet_requests)
        adjusted_bets = []
        
        total_requested_exposure = 0.0
        
        # 1. Cap individual clusters first
        for cluster_id, cluster_bets in clusters.items():
            cluster_requested = sum(b.get("requested_stake", 0.0) for b in cluster_bets)
            max_cluster_cash = current_bankroll * self.max_cluster_exposure
            
            scale = 1.0
            if cluster_requested > max_cluster_cash:
                scale = max_cluster_cash / cluster_requested
                
            for b in cluster_bets:
                b["allocated_stake"] = b.get("requested_stake", 0.0) * scale
                total_requested_exposure += b["allocated_stake"]

        # 2. Cap global portfolio exposure
        max_portfolio_cash = current_bankroll * self.max_portfolio_exposure
        if total_requested_exposure > max_portfolio_cash:
            global_scale = max_portfolio_cash / total_requested_exposure
            for b in bet_requests:
                b["allocated_stake"] = b.get("allocated_stake", 0.0) * global_scale
        else:
            for b in bet_requests:
                # Ensure key is initialized even if no scaling was applied
                if "allocated_stake" not in b:
                    b["allocated_stake"] = b.get("requested_stake", 0.0)
                    
        return bet_requests
