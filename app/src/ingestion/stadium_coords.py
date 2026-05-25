"""
Stadium coordinates database — maps team/stadium names to (lat, lon) for weather lookups.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Football (Soccer) — Major European Leagues
# ---------------------------------------------------------------------------
FOOTBALL_STADIUMS: Dict[str, Tuple[float, float]] = {
    # Premier League
    "Arsenal": (51.555, -0.108), "Emirates Stadium": (51.555, -0.108),
    "Chelsea": (51.482, -0.191), "Stamford Bridge": (51.482, -0.191),
    "Liverpool": (53.431, -2.961), "Anfield": (53.431, -2.961),
    "Manchester City": (53.483, -2.200), "Etihad Stadium": (53.483, -2.200),
    "Manchester United": (53.463, -2.291), "Old Trafford": (53.463, -2.291),
    "Tottenham": (51.604, -0.066), "Tottenham Hotspur Stadium": (51.604, -0.066),
    # La Liga
    "Real Madrid": (40.453, -3.688), "Santiago Bernabeu": (40.453, -3.688),
    "Barcelona": (41.381, 2.123), "Camp Nou": (41.381, 2.123),
    "Atletico Madrid": (40.436, -3.599), "Wanda Metropolitano": (40.436, -3.599),
    # Serie A
    "Juventus": (45.110, 7.641), "Allianz Stadium": (45.110, 7.641),
    "AC Milan": (45.478, 9.124), "San Siro": (45.478, 9.124),
    "Inter Milan": (45.478, 9.124),
    "Roma": (41.934, 12.455), "Stadio Olimpico": (41.934, 12.455),
    "Lazio": (41.934, 12.455),
    # Bundesliga
    "Bayern Munich": (48.219, 11.627), "Allianz Arena": (48.219, 11.627),
    "Borussia Dortmund": (51.493, 7.452), "Signal Iduna Park": (51.493, 7.452),
    # Ligue 1
    "PSG": (48.841, 2.253), "Parc des Princes": (48.841, 2.253),
    "Marseille": (43.270, 5.396), "Stade Velodrome": (43.270, 5.396),
}

# ---------------------------------------------------------------------------
# NBA Arenas
# ---------------------------------------------------------------------------
NBA_ARENAS: Dict[str, Tuple[float, float]] = {
    "ATL": (33.757, -84.396), "BOS": (42.366, -71.062), "BKN": (40.682, -73.975),
    "CHA": (35.225, -80.839), "CHI": (41.880, -87.674), "CLE": (41.496, -81.688),
    "DAL": (32.790, -96.810), "DEN": (39.748, -105.007), "DET": (42.341, -83.055),
    "GSW": (37.767, -122.387), "HOU": (29.750, -95.362), "IND": (39.763, -86.155),
    "LAC": (34.043, -118.266), "LAL": (34.043, -118.266), "MEM": (35.138, -90.052),
    "MIA": (25.781, -80.186), "MIL": (43.045, -87.916), "MIN": (44.979, -93.276),
    "NOP": (29.949, -90.082), "NYK": (40.750, -73.993), "OKC": (35.463, -97.515),
    "ORL": (28.539, -81.383), "PHI": (39.901, -75.172), "PHX": (33.445, -112.071),
    "POR": (45.531, -122.666), "SAC": (38.580, -121.499), "SAS": (29.427, -98.437),
    "TOR": (43.643, -79.379), "UTA": (40.768, -111.901), "WAS": (38.898, -77.020),
}

# Combine all databases
ALL_COORDINATES: Dict[str, Tuple[float, float]] = {}
ALL_COORDINATES.update(FOOTBALL_STADIUMS)
ALL_COORDINATES.update(NBA_ARENAS)


def get_stadium_coords(name: str) -> Optional[Tuple[float, float]]:
    """
    Look up stadium coordinates by team name, abbreviation, or stadium name.

    Args:
        name: Team name, abbreviation, or stadium name

    Returns:
        (latitude, longitude) or None if not found
    """
    # Direct lookup
    if name in ALL_COORDINATES:
        return ALL_COORDINATES[name]

    # Case-insensitive lookup
    name_lower = name.lower()
    for key, coords in ALL_COORDINATES.items():
        if key.lower() == name_lower:
            return coords

    # Partial match
    for key, coords in ALL_COORDINATES.items():
        if name_lower in key.lower() or key.lower() in name_lower:
            return coords

    return None


def is_indoor_sport(sport: str) -> bool:
    """Check if a sport is typically played indoors (weather not relevant)."""
    indoor_sports = {"nba", "basketball", "nhl", "hockey", "volleyball"}
    return sport.lower() in indoor_sports
