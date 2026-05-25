"""
Weather client — fetches match-day weather from Open-Meteo API (free, no API key).

Open-Meteo provides historical and forecast weather data via a simple REST API.
This is used to add weather features (temperature, wind, precipitation) to the
feature pipeline, which significantly impacts over/under markets in outdoor sports.

API docs: https://open-meteo.com/en/docs
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Dict, Tuple

import requests
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

logger = logging.getLogger("weather_client")

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

# Cache: (lat, lon, date) -> WeatherData
_cache: Dict[str, Tuple[float, WeatherData]] = {}
_CACHE_TTL_SECONDS = 3600  # 1 hour


@dataclass
class WeatherData:
    """Weather conditions at match time."""
    temperature_c: float
    wind_speed_kmh: float
    precipitation_mm: float
    humidity_pct: float
    is_outdoor: bool = True

    def to_features(self) -> Dict[str, float]:
        """Convert to feature dict for ML pipeline."""
        return {
            "temperature": self.temperature_c,
            "wind_speed": self.wind_speed_kmh,
            "precipitation": self.precipitation_mm,
            "humidity": self.humidity_pct,
            "is_outdoor": 1.0 if self.is_outdoor else 0.0,
        }


class WeatherClient:
    """
    Fetches weather data from Open-Meteo API.

    Supports both forecast (for upcoming matches) and historical (for backtesting).
    Results are cached to avoid hitting rate limits.
    """

    def __init__(self, cache_ttl: int = _CACHE_TTL_SECONDS):
        self.cache_ttl = cache_ttl

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.5, max=10),
        reraise=True,
    )
    def _fetch_forecast(
        self,
        latitude: float,
        longitude: float,
        date_str: str,
        hour: int = 20,  # Default 8PM local (typical match time)
    ) -> Dict:
        """Fetch forecast weather data from Open-Meteo."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,wind_speed_10m,precipitation,relative_humidity_2m",
            "start_date": date_str,
            "end_date": date_str,
            "timezone": "auto",
        }

        response = requests.get(OPEN_METEO_FORECAST_URL, params=params, timeout=15)
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.5, max=10),
        reraise=True,
    )
    def _fetch_historical(
        self,
        latitude: float,
        longitude: float,
        date_str: str,
        hour: int = 20,
    ) -> Dict:
        """Fetch historical weather data from Open-Meteo."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,wind_speed_10m,precipitation,relative_humidity_2m",
            "start_date": date_str,
            "end_date": date_str,
            "timezone": "auto",
        }

        response = requests.get(OPEN_METEO_HISTORICAL_URL, params=params, timeout=15)
        response.raise_for_status()
        return response.json()

    def get_match_weather(
        self,
        latitude: float,
        longitude: float,
        date_str: str,
        hour: int = 20,
        is_historical: bool = False,
        is_outdoor: bool = True,
    ) -> WeatherData:
        """
        Get weather conditions for a match at given coordinates and time.

        Args:
            latitude: Stadium latitude
            longitude: Stadium longitude
            date_str: Date in YYYY-MM-DD format
            hour: Match start hour (0-23, default 20 = 8PM)
            is_historical: If True, use historical API (for backtesting)
            is_outdoor: Whether the sport is outdoor (affects feature relevance)

        Returns:
            WeatherData with temperature, wind, precipitation, humidity
        """
        # Check cache
        cache_key = f"{latitude:.4f},{longitude:.4f},{date_str},{hour}"
        cached = _cache.get(cache_key)
        if cached:
            cached_time, cached_data = cached
            if time.time() - cached_time < self.cache_ttl:
                return cached_data

        try:
            if is_historical:
                data = self._fetch_historical(latitude, longitude, date_str, hour)
            else:
                data = self._fetch_forecast(latitude, longitude, date_str, hour)

            hourly = data.get("hourly", {})
            times = hourly.get("time", [])
            temps = hourly.get("temperature_2m", [])
            winds = hourly.get("wind_speed_10m", [])
            precips = hourly.get("precipitation", [])
            humidities = hourly.get("relative_humidity_2m", [])

            # Find the closest hour
            target_time = f"{date_str}T{hour:02d}:00"
            idx = 0
            for i, t in enumerate(times):
                if t == target_time:
                    idx = i
                    break
                if t > target_time:
                    idx = max(0, i - 1)
                    break

            weather = WeatherData(
                temperature_c=float(temps[idx]) if idx < len(temps) and temps[idx] is not None else 15.0,
                wind_speed_kmh=float(winds[idx]) if idx < len(winds) and winds[idx] is not None else 10.0,
                precipitation_mm=float(precips[idx]) if idx < len(precips) and precips[idx] is not None else 0.0,
                humidity_pct=float(humidities[idx]) if idx < len(humidities) and humidities[idx] is not None else 60.0,
                is_outdoor=is_outdoor,
            )

            # Cache result
            _cache[cache_key] = (time.time(), weather)
            return weather

        except Exception as e:
            logger.warning("Weather fetch failed for %s: %s — using defaults", cache_key, e)
            return WeatherData(
                temperature_c=15.0,
                wind_speed_kmh=10.0,
                precipitation_mm=0.0,
                humidity_pct=60.0,
                is_outdoor=is_outdoor,
            )

    def get_weather_features(
        self,
        latitude: float,
        longitude: float,
        date_str: str,
        hour: int = 20,
        is_historical: bool = False,
        is_outdoor: bool = True,
    ) -> Dict[str, float]:
        """Convenience: get weather as feature dict directly."""
        weather = self.get_match_weather(
            latitude, longitude, date_str, hour, is_historical, is_outdoor
        )
        return weather.to_features()
