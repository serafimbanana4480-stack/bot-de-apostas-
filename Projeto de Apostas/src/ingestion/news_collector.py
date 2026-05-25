"""
Sports news collector — RSS + Reddit headline aggregation for LLM analysis.

Collects headlines from free sources (ESPN RSS, BBC Sport, Reddit) and
deduplicates them before passing to the LLM news feature extractor.

Caches collected headlines in Parquet to avoid redundant LLM calls.

Usage:
    from src.ingestion.news_collector import NewsCollector

    collector = NewsCollector(sports=["football", "nba"])
    headlines = collector.collect("football", max_items=20)
    deduped = collector.deduplicate(headlines)

    # Integrate with LLM extractor
    from src.ingestion.llm_news import NewsFeatureExtractor
    extractor = NewsFeatureExtractor(backend="ollama")
    features = extractor.batch_analyze(
        [h.text for h in deduped],
        sport="football",
    )
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger("news_collector")


@dataclass
class HeadlineItem:
    """A single collected news headline."""
    text: str
    source: str          # "rss_espn", "rss_bbc", "reddit", etc.
    url: str
    sport: str
    timestamp: float = field(default_factory=time.time)
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            self.hash = hashlib.md5(f"{self.url}:{self.text}".encode()).hexdigest()[:12]


# RSS feed URLs by sport (free, no API key required)
RSS_FEEDS: dict[str, list[dict[str, str]]] = {
    "football": [
        {"url": "https://www.espn.com/espn/rss/soccer/news", "source": "rss_espn"},
        {"url": "https://feeds.bbci.co.uk/sport/football/rss.xml", "source": "rss_bbc"},
        {"url": "https://www.skysports.com/rss/12040.xml", "source": "rss_sky"},
    ],
    "nba": [
        {"url": "https://www.espn.com/espn/rss/nba/news", "source": "rss_espn"},
        {"url": "https://feeds.bbci.co.uk/sport/basketball/rss.xml", "source": "rss_bbc"},
    ],
    "mma": [
        {"url": "https://www.espn.com/espn/rss/mma/news", "source": "rss_espn"},
    ],
    "tennis": [
        {"url": "https://feeds.bbci.co.uk/sport/tennis/rss.xml", "source": "rss_bbc"},
    ],
}

# Reddit subreddits by sport (read-only, no API key for basic access)
REDDIT_SUBS: dict[str, list[str]] = {
    "football": ["soccer", "PremierLeague", "ChampionsLeague"],
    "nba": ["nba", "nbadiscussion"],
    "mma": ["MMA", "ufc"],
    "tennis": ["tennis"],
}


class NewsCollector:
    """
    Collects sports headlines from free sources for LLM analysis.

    Supports:
    - RSS feeds (ESPN, BBC Sport, Sky Sports)
    - Reddit (subreddit hot posts)
    - Deduplication by URL hash
    - Local Parquet cache to avoid redundant API calls

    Args:
        sports: List of sport names to collect for
        cache_dir: Directory for caching collected headlines
        reddit_user_agent: User agent for Reddit API (required by Reddit ToS)
    """

    def __init__(
        self,
        sports: list[str] | None = None,
        cache_dir: str = "data/news",
        reddit_user_agent: str = "VBQ-NewsCollector/1.0",
    ):
        self.sports = sports or ["football", "nba", "mma"]
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.reddit_user_agent = reddit_user_agent
        self._seen_hashes: set[str] = set()
        self._load_cache_hashes()

    def _load_cache_hashes(self) -> None:
        """Load previously seen headline hashes from cache."""
        cache_file = self.cache_dir / "seen_hashes.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    self._seen_hashes = set(json.load(f))
                logger.info("Loaded %d cached hashes", len(self._seen_hashes))
            except Exception as e:
                logger.warning("Failed to load cache: %s", e)
                self._seen_hashes = set()

    def _save_cache_hashes(self) -> None:
        """Persist seen hashes to cache."""
        cache_file = self.cache_dir / "seen_hashes.json"
        try:
            with open(cache_file, "w") as f:
                json.dump(list(self._seen_hashes), f)
        except Exception as e:
            logger.warning("Failed to save cache: %s", e)

    def collect(
        self,
        sport: str,
        max_items: int = 20,
        sources: list[str] | None = None,
    ) -> list[HeadlineItem]:
        """
        Collect headlines for a sport from all configured sources.

        Args:
            sport: Sport name (e.g. "football", "nba")
            max_items: Maximum number of headlines to return
            sources: Optional filter for sources (e.g. ["rss_espn", "reddit"])

        Returns:
            List of HeadlineItem, newest first, deduplicated.
        """
        all_items: list[HeadlineItem] = []
        source_filter = set(sources) if sources else None

        # --- RSS feeds ---
        rss_feeds = RSS_FEEDS.get(sport, [])
        for feed_config in rss_feeds:
            if source_filter and feed_config["source"] not in source_filter:
                continue
            try:
                items = self._collect_rss(feed_config["url"], feed_config["source"], sport)
                all_items.extend(items)
            except Exception as e:
                logger.warning("RSS collection failed for %s: %s", feed_config["url"], e)

        # --- Reddit ---
        reddit_subs = REDDIT_SUBS.get(sport, [])
        for sub in reddit_subs:
            if source_filter and "reddit" not in source_filter:
                continue
            try:
                items = self._collect_reddit(sub, sport)
                all_items.extend(items)
            except Exception as e:
                logger.warning("Reddit collection failed for r/%s: %s", sub, e)

        # Sort by timestamp (newest first) and deduplicate
        all_items.sort(key=lambda x: x.timestamp, reverse=True)
        deduped = self.deduplicate(all_items)

        # Update cache
        for item in deduped:
            self._seen_hashes.add(item.hash)
        self._save_cache_hashes()

        return deduped[:max_items]

    def _collect_rss(self, url: str, source: str, sport: str) -> list[HeadlineItem]:
        """
        Collect headlines from an RSS feed.

        Uses feedparser if available, falls back to basic XML parsing.
        """
        items: list[HeadlineItem] = []

        try:
            import feedparser
        except ImportError:
            logger.warning("feedparser not installed — RSS collection unavailable. Install: pip install feedparser")
            return items

        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:30]:
                headline = HeadlineItem(
                    text=entry.get("title", ""),
                    source=source,
                    url=entry.get("link", ""),
                    sport=sport,
                )
                if headline.text:
                    items.append(headline)
        except Exception as e:
            logger.warning("Failed to parse RSS %s: %s", url, e)

        return items

    def _collect_reddit(self, subreddit: str, sport: str) -> list[HeadlineItem]:
        """
        Collect hot posts from a Reddit subreddit.

        Uses PRAW if available, falls back to public JSON API.
        """
        items: list[HeadlineItem] = []

        # Try PRAW first (more reliable, respects rate limits)
        try:
            import praw
            reddit = praw.Reddit(
                client_id="",
                client_secret="",
                user_agent=self.reddit_user_agent,
                check_for_async=False,
            )
            sub = reddit.subreddit(subreddit)
            for post in sub.hot(limit=15):
                headline = HeadlineItem(
                    text=post.title,
                    source=f"reddit_r_{subreddit}",
                    url=f"https://reddit.com{post.permalink}",
                    sport=sport,
                )
                if headline.text:
                    items.append(headline)
            return items
        except ImportError:
            pass
        except Exception as e:
            logger.warning("PRAW failed for r/%s: %s", subreddit, e)

        # Fallback: public JSON API (no auth, rate-limited)
        try:
            import requests
            resp = requests.get(
                f"https://www.reddit.com/r/{subreddit}/hot.json",
                headers={"User-Agent": self.reddit_user_agent},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            for post in data.get("data", {}).get("children", [])[:15]:
                post_data = post.get("data", {})
                headline = HeadlineItem(
                    text=post_data.get("title", ""),
                    source=f"reddit_r_{subreddit}",
                    url=f"https://reddit.com{post_data.get('permalink', '')}",
                    sport=sport,
                )
                if headline.text:
                    items.append(headline)
        except Exception as e:
            logger.warning("Reddit JSON API failed for r/%s: %s", subreddit, e)

        return items

    def deduplicate(self, items: list[HeadlineItem]) -> list[HeadlineItem]:
        """
        Remove duplicate headlines by URL hash.

        Keeps the first occurrence of each hash.
        """
        seen: set[str] = set()
        unique: list[HeadlineItem] = []
        for item in items:
            if item.hash not in seen and item.hash not in self._seen_hashes:
                seen.add(item.hash)
                unique.append(item)
        return unique

    def collect_and_analyze(
        self,
        sport: str,
        max_items: int = 20,
        llm_backend: str = "ollama",
        llm_model: str = "llama3",
    ) -> dict[str, Any]:
        """
        Collect headlines and analyze them with LLM in one call.

        Returns a dict with:
        - headlines: collected headlines
        - features: LLM-extracted features per headline
        - aggregate: averaged feature vector
        """
        from src.ingestion.llm_news import FEATURE_KEYS, NewsFeatureExtractor

        headlines = self.collect(sport, max_items)
        if not headlines:
            return {
                "headlines": [],
                "features": [],
                "aggregate": {k: 0.0 for k in FEATURE_KEYS},
                "n_headlines": 0,
            }

        extractor = NewsFeatureExtractor(backend=llm_backend, model=llm_model)
        texts = [h.text for h in headlines]
        features = extractor.batch_analyze(texts, sport)

        # Aggregate features
        aggregate = {}
        for key in FEATURE_KEYS:
            values = [f.get(key, 0.0) for f in features if f.get(key) is not None]
            aggregate[key] = float(np.mean(values)) if values else 0.0

        return {
            "headlines": [{"text": h.text, "source": h.source, "url": h.url} for h in headlines],
            "features": features,
            "aggregate": aggregate,
            "n_headlines": len(headlines),
        }
