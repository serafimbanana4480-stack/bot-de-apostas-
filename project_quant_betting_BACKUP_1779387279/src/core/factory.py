"""
Sport Factory.
Provides Dependency Injection to retrieve the correct sport implementation based on configuration.
"""
from src.core.interfaces import BaseSport
from src.sports.nba import NBASport
from src.sports.football import FootballSport
from src.sports.mma import MMASport

class SportFactory:
    _sports = {
        'nba': NBASport(),
        'football': FootballSport(),
        'mma': MMASport()
    }
    
    @classmethod
    def get_sport(cls, sport_code: str) -> BaseSport:
        sport = cls._sports.get(sport_code.lower())
        if not sport:
            raise ValueError(f"Sport {sport_code} is not supported. Available: {list(cls._sports.keys())}")
        return sport
