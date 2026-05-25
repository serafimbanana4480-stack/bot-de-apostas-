import logging
import re
from typing import Any, Dict

logger = logging.getLogger("news_scraper")

class NewsInjuryParser:
    """
    Parses dynamic sports news texts, extracting injury status updates 
    and outputting adjusting coefficients for team rating indexes.
    """
    def __init__(self):
        self.status_modifiers = {
            "OUT": -0.08,           # decreases team strength rating by 8%
            "DOUBTFUL": -0.05,      # decreases team strength rating by 5%
            "QUESTIONABLE": -0.02,  # decreases team strength rating by 2%
            "AVAILABLE": 0.0        # no penalty
        }

    def parse_injury_headline(self, headline: str) -> Dict[str, Any]:
        """
        Parses single headline using pattern matching rules to find player, status, and impact.
        Example: "LeBron James (Lakers) is ruled OUT tonight with ankle soreness."
        """
        headline_upper = headline.upper()
        
        # Determine status
        status = "AVAILABLE"
        for key in self.status_modifiers.keys():
            if re.search(r'\b' + key + r'\b', headline_upper):
                status = key
                break
                
        # Simple extraction of parenthesized team
        team_match = re.search(r'\((.*?)\)', headline)
        team = team_match.group(1) if team_match else "UNKNOWN"
        
        # Simple name match (assume anything before team or parenthesis)
        name_match = re.match(r'^([A-Za-z\s]+)', headline)
        player_name = name_match.group(1).strip() if name_match else "Unknown Player"
        
        # Assess player impact tier (Star vs Role Player) based on keyword matching
        player_tier = "ROLE_PLAYER"
        star_names = ["LEBRON", "DONCIC", "CURRY", "GIANNIS", "JOKIC", "EMBIID", "TATUM"]
        for star in star_names:
            if star in player_name.upper():
                player_tier = "STAR"
                break
                
        modifier = self.status_modifiers[status]
        if player_tier == "STAR":
            modifier *= 1.5 # stars have 1.5x larger impact on the overall team rating
            
        return {
            "player": player_name,
            "team": team,
            "status": status,
            "tier": player_tier,
            "rating_modifier": float(modifier)
        }
