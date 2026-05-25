from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np


class StochasticInformationArrival:
    """
    Models realistic news arrival timelines. In efficient markets, odds adjust 
    at rumor release (due to sharp money flow) before public announcement.
    """
    def __init__(self, news_announcement_delay_mins: int = 45):
        self.news_announcement_delay_mins = news_announcement_delay_mins

    def simulate_odds_timeline(
        self, 
        initial_odds: float, 
        kickoff_time: datetime,
        injury_severity: float,  # severity scale e.g. 0.0 to 1.0
        rumor_time_before_kickoff_hours: float = 6.0
    ) -> List[Dict[str, Any]]:
        """
        Generates timeline of odds changes.
        """
        rumor_time = kickoff_time - timedelta(hours=rumor_time_before_kickoff_hours)
        public_time = rumor_time + timedelta(minutes=self.news_announcement_delay_mins)
        
        timeline = []
        
        # 1. Opening odds (t-24h)
        timeline.append({
            "timestamp": kickoff_time - timedelta(hours=24),
            "odds": initial_odds,
            "information_state": "NO_NEWS"
        })
        
        # 2. Rumor released (sharp books adjust odds immediately by 80% of total expected drift)
        total_drift = initial_odds * 0.15 * injury_severity
        rumor_odds = initial_odds + (total_drift * 0.80)
        
        timeline.append({
            "timestamp": rumor_time,
            "odds": float(rumor_odds),
            "information_state": "RUMOR_RELEASED"
        })
        
        # 3. Public news scraper index (remaining 20% adjustment happens here when news goes public)
        public_odds = initial_odds + total_drift
        timeline.append({
            "timestamp": public_time,
            "odds": float(public_odds),
            "information_state": "PUBLIC_ANNOUNCED"
        })
        
        # 4. Closing Line
        timeline.append({
            "timestamp": kickoff_time,
            "odds": float(public_odds + np.random.normal(0, 0.01)),
            "information_state": "CLOSING_LINE"
        })
        
        return timeline
