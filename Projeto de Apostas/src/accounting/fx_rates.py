"""
FX rates client — fetches daily exchange rates from the European Central Bank (ECB).

ECB provides free, reliable daily FX rates. This module caches rates locally
with a 24h TTL and falls back to hardcoded rates if the API is unavailable.

API: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
"""
from __future__ import annotations

import json
import logging
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional

import requests

logger = logging.getLogger("fx_rates")

ECB_DAILY_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"

# Fallback rates (as of 2024, approximate)
FALLBACK_RATES = {
    "EUR": 1.0,
    "USD": 1.085,
    "GBP": 0.858,
    "JPY": 162.5,
    "CHF": 0.942,
    "CAD": 1.47,
    "AUD": 1.66,
    "SEK": 11.35,
    "NOK": 11.55,
    "BRL": 5.45,
}

# Cache file path
_CACHE_DIR = Path("data/fx_cache")
_CACHE_TTL_SECONDS = 86400  # 24 hours


class FXRateProvider:
    """
    Provides EUR-based exchange rates from ECB with local caching.

    All rates are expressed as: 1 EUR = X units of foreign currency.
    To convert foreign amount to EUR: amount / rate[currency]
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        cache_ttl: int = _CACHE_TTL_SECONDS,
    ):
        self.cache_dir = Path(cache_dir or _CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = cache_ttl
        self._rates: Optional[Dict[str, float]] = None
        self._rates_timestamp: float = 0

    def get_rates(self) -> Dict[str, float]:
        """
        Get current EUR-based exchange rates.

        Returns cached rates if fresh (<24h), otherwise fetches from ECB.
        Falls back to hardcoded rates if ECB is unavailable.
        """
        # Check in-memory cache
        if self._rates and (time.time() - self._rates_timestamp) < self.cache_ttl:
            return self._rates

        # Check file cache
        cached = self._load_cache()
        if cached and (time.time() - cached.get("timestamp", 0)) < self.cache_ttl:
            self._rates = cached["rates"]
            self._rates_timestamp = cached["timestamp"]
            return self._rates

        # Fetch from ECB
        try:
            rates = self._fetch_ecb_rates()
            self._rates = rates
            self._rates_timestamp = time.time()
            self._save_cache(rates)
            logger.info("FX rates updated from ECB (%d currencies)", len(rates))
            return rates
        except Exception as e:
            logger.warning("ECB fetch failed: %s — using fallback rates", e)

        # Use fallback
        if self._rates:
            return self._rates

        self._rates = FALLBACK_RATES.copy()
        self._rates_timestamp = time.time()
        return self._rates

    def convert_to_eur(self, amount: float, currency: str) -> float:
        """Convert an amount in foreign currency to EUR."""
        rates = self.get_rates()
        rate = rates.get(currency.upper(), 1.0)
        if rate == 0:
            return amount  # Avoid division by zero
        return amount / rate

    def convert_from_eur(self, amount_eur: float, target_currency: str) -> float:
        """Convert EUR amount to foreign currency."""
        rates = self.get_rates()
        rate = rates.get(target_currency.upper(), 1.0)
        return amount_eur * rate

    def get_cross_rate(self, from_currency: str, to_currency: str) -> float:
        """Get exchange rate from one currency to another."""
        rates = self.get_rates()
        from_rate = rates.get(from_currency.upper(), 1.0)
        to_rate = rates.get(to_currency.upper(), 1.0)
        if from_rate == 0:
            return 1.0
        return to_rate / from_rate

    def _fetch_ecb_rates(self) -> Dict[str, float]:
        """Fetch daily rates from ECB XML feed."""
        response = requests.get(ECB_DAILY_URL, timeout=15)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        rates = {"EUR": 1.0}

        # Parse ECB XML format
        for cube in root.iter():
            if cube.get("currency") and cube.get("rate"):
                currency = cube.get("currency")
                rate = float(cube.get("rate"))
                rates[currency] = rate

        return rates

    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """Load rates from local JSON cache."""
        cache_path = self.cache_dir / "ecb_rates.json"
        if not cache_path.exists():
            return None
        try:
            with open(cache_path) as f:
                return json.load(f)
        except Exception:
            return None

    def _save_cache(self, rates: Dict[str, float]) -> None:
        """Save rates to local JSON cache."""
        cache_path = self.cache_dir / "ecb_rates.json"
        data = {
            "timestamp": time.time(),
            "rates": rates,
            "source": "ecb",
        }
        with open(cache_path, "w") as f:
            json.dump(data, f, indent=2)


from typing import Any
