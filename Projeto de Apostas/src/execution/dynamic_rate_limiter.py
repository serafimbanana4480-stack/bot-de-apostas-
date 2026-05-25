"""
Dynamic rate limiter — adjusts request rate based on API response headers.

Reads X-RateLimit-Remaining and X-RateLimit-Reset headers from API responses
to dynamically adjust the delay between requests. This prevents hitting
rate limits and getting banned, while maximizing throughput when limits are generous.

Usage:
    limiter = DynamicRateLimiter(default_rps=5)
    
    # After each API response, update the limiter:
    limiter.update_from_response(response.headers)
    
    # Before each API request, wait as needed:
    limiter.wait_if_needed()
"""
from __future__ import annotations

import logging
import time
from typing import Dict, Optional

logger = logging.getLogger("dynamic_rate_limiter")


class DynamicRateLimiter:
    """
    Dynamic rate limiter that adapts to API rate limit headers.

    Strategy:
    - When X-RateLimit-Remaining > 50%: use fast rate (default_rps)
    - When X-RateLimit-Remaining 25-50%: slow down to 50% of default
    - When X-RateLimit-Remaining < 25%: slow down to 25% of default
    - When X-RateLimit-Remaining = 0: wait until X-RateLimit-Reset
    - If no headers: use default_rps with exponential backoff on 429

    Supports both Betfair and Pinnacle header formats.
    """

    def __init__(
        self,
        default_rps: float = 5.0,
        min_rps: float = 0.5,
        max_rps: float = 20.0,
        jitter_pct: float = 0.1,
    ):
        """
        Args:
            default_rps: Default requests per second
            min_rps: Minimum requests per second (never go slower)
            max_rps: Maximum requests per second (never go faster)
            jitter_pct: Random jitter percentage to add (prevents thundering herd)
        """
        self.default_rps = default_rps
        self.min_rps = min_rps
        self.max_rps = max_rps
        self.jitter_pct = jitter_pct

        self._current_rps = default_rps
        self._last_call_time: float = 0.0
        self._remaining: Optional[int] = None
        self._limit: Optional[int] = None
        self._reset_time: Optional[float] = None

        # Backoff state for 429 responses
        self._consecutive_429s = 0
        self._backoff_until: float = 0.0

    @property
    def current_rps(self) -> float:
        """Current effective requests per second."""
        return self._current_rps

    @property
    def remaining(self) -> Optional[int]:
        """Remaining requests in current window (from API headers)."""
        return self._remaining

    def update_from_response(self, headers: Dict[str, str]) -> None:
        """
        Update rate limit state from API response headers.

        Supports multiple header formats:
        - Betfair: X-RateLimit-Remaining, X-RateLimit-Reset
        - Pinnacle: via response status codes
        - Generic: X-RateLimit-Remaining, X-RateLimit-Limit, X-RateLimit-Reset
        """
        # Parse remaining requests
        remaining_str = headers.get("X-RateLimit-Remaining") or headers.get("x-ratelimit-remaining")
        if remaining_str is not None:
            try:
                self._remaining = int(remaining_str)
            except (ValueError, TypeError):
                pass

        # Parse total limit
        limit_str = headers.get("X-RateLimit-Limit") or headers.get("x-ratelimit-limit")
        if limit_str is not None:
            try:
                self._limit = int(limit_str)
            except (ValueError, TypeError):
                pass

        # Parse reset time
        reset_str = headers.get("X-RateLimit-Reset") or headers.get("x-ratelimit-reset") or headers.get("Retry-After")
        if reset_str is not None:
            try:
                # Could be Unix timestamp or seconds from now
                reset_val = float(reset_str)
                if reset_val < 1e9:  # Likely seconds from now
                    self._reset_time = time.time() + reset_val
                else:  # Likely Unix timestamp
                    self._reset_time = reset_val
            except (ValueError, TypeError):
                pass

        # Adjust rate based on remaining quota
        if self._remaining is not None and self._limit is not None and self._limit > 0:
            ratio = self._remaining / self._limit

            if ratio <= 0:
                # Completely exhausted — wait until reset
                self._current_rps = self.min_rps
                if self._reset_time:
                    wait_seconds = max(0, self._reset_time - time.time())
                    logger.warning(
                        "Rate limit exhausted (0/%d). Waiting %.1fs until reset.",
                        self._limit, wait_seconds,
                    )
                    self._backoff_until = time.time() + wait_seconds
            elif ratio < 0.25:
                self._current_rps = max(self.min_rps, self.default_rps * 0.25)
                logger.info("Rate limit low (%d/%d). Slowing to %.1f rps", self._remaining, self._limit, self._current_rps)
            elif ratio < 0.50:
                self._current_rps = max(self.min_rps, self.default_rps * 0.50)
            else:
                self._current_rps = min(self.max_rps, self.default_rps)

        # Reset 429 counter on successful response
        self._consecutive_429s = 0

    def handle_429(self, headers: Dict[str, str] = None) -> None:
        """
        Handle a 429 Too Many Requests response.

        Applies exponential backoff with jitter.
        """
        self._consecutive_429s += 1

        # Parse Retry-After header
        retry_after = 5.0  # Default
        if headers:
            retry_after_str = headers.get("Retry-After") or headers.get("retry-after")
            if retry_after_str:
                try:
                    retry_after = float(retry_after_str)
                except (ValueError, TypeError):
                    pass

        # Exponential backoff: 5s, 10s, 20s, 40s...
        backoff = min(retry_after * (2 ** (self._consecutive_429s - 1)), 300)  # Cap at 5 min
        self._backoff_until = time.time() + backoff
        self._current_rps = max(self.min_rps, self.default_rps / (2 ** self._consecutive_429s))

        logger.warning(
            "429 rate limited (consecutive: %d). Backing off %.1fs. Current rps: %.1f",
            self._consecutive_429s, backoff, self._current_rps,
        )

    def wait_if_needed(self) -> float:
        """
        Wait before the next API call if rate limiting requires it.

        Returns:
            Seconds waited
        """
        waited = 0.0

        # Check if we're in a backoff period
        now = time.time()
        if now < self._backoff_until:
            wait_seconds = self._backoff_until - now
            time.sleep(wait_seconds)
            waited += wait_seconds
            now = time.time()

        # Calculate minimum interval based on current rps
        min_interval = 1.0 / self._current_rps

        # Add jitter (±jitter_pct)
        import random
        jitter = min_interval * self.jitter_pct * (random.random() * 2 - 1)
        effective_interval = min_interval + jitter

        # Check time since last call
        elapsed = now - self._last_call_time
        if elapsed < effective_interval:
            wait_seconds = effective_interval - elapsed
            time.sleep(wait_seconds)
            waited += wait_seconds

        self._last_call_time = time.time()
        return waited

    def get_status(self) -> Dict[str, any]:
        """Get current rate limiter status for monitoring."""
        return {
            "current_rps": round(self._current_rps, 2),
            "default_rps": self.default_rps,
            "remaining": self._remaining,
            "limit": self._limit,
            "consecutive_429s": self._consecutive_429s,
            "backoff_active": time.time() < self._backoff_until,
        }
