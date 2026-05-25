"""LLM-powered sports news feature extraction module.

Integrates LLaMA 3 8B (local via Ollama) or OpenAI API as fallback for
real-time sports news analysis. Extracts structured features from headlines,
Twitter posts, and Reddit discussions to feed into betting prediction models.

Usage:
    >>> extractor = NewsFeatureExtractor(backend="ollama", model="llama3")
    >>> features = extractor.analyze_headline(
    ...     "Star quarterback ruled out with shoulder injury",
    ...     sport="nfl"
    ... )
    >>> print(features)
    {
        'injury_prob': 0.9,
        'key_player_return': 0.0,
        'emotional_impact': -0.7,
        'source_confidence': 0.8,
        'weather_impact': 0.0,
        'lineup_change': 0.85
    }

    >>> # Batch analysis for multiple headlines
    >>> results = extractor.batch_analyze(
    ...     ["Star QB injured", "Weather forecast: heavy rain"],
    ...     sport="nfl"
    ... )
    >>> # Aggregate into a feature vector for ML models
    >>> vector = extractor.build_feature_vector(results)
    >>> print(vector.shape)
    (6,)

    >>> # OpenAI fallback
    >>> extractor = NewsFeatureExtractor(
    ...     backend="openai",
    ...     model="gpt-4",
    ...     openai_api_key="sk-..."
    ... )
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List

import numpy as np
import requests

logger = logging.getLogger("llm_news")

# Default neutral feature values when LLM is unavailable
NEUTRAL_FEATURES: Dict[str, float] = {
    "injury_prob": 0.0,
    "key_player_return": 0.0,
    "emotional_impact": 0.0,
    "source_confidence": 0.0,
    "weather_impact": 0.0,
    "lineup_change": 0.0,
}

# Ordered feature keys for consistent vector construction
FEATURE_KEYS: List[str] = [
    "injury_prob",
    "key_player_return",
    "emotional_impact",
    "source_confidence",
    "weather_impact",
    "lineup_change",
]

# Feature value bounds for validation
FEATURE_BOUNDS: Dict[str, tuple] = {
    "injury_prob": (0.0, 1.0),
    "key_player_return": (0.0, 1.0),
    "emotional_impact": (-1.0, 1.0),
    "source_confidence": (0.0, 1.0),
    "weather_impact": (-1.0, 1.0),
    "lineup_change": (0.0, 1.0),
}

# Prompt template instructing the LLM to output structured JSON
PROMPT_TEMPLATE = """You are a sports news analysis assistant. Analyze the following {sport} news headline and extract structured features.

Headline: "{headline}"

Respond ONLY with a valid JSON object containing exactly these keys and value ranges:
- "injury_prob": float 0-1, probability that a key player is injured
- "key_player_return": float 0-1, probability that a key player is returning from absence
- "emotional_impact": float -1 to 1, emotional impact on team morale (negative = demoralizing, positive = motivating)
- "source_confidence": float 0-1, how reliable/certain the news source appears
- "weather_impact": float -1 to 1, impact of weather conditions (negative = adverse, positive = favorable)
- "lineup_change": float 0-1, probability of a significant lineup change

Output ONLY the JSON object, no other text."""

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0
BACKOFF_MULTIPLIER = 2.0
REQUEST_TIMEOUT_SECONDS = 30


class NewsFeatureExtractor:
    """Extracts structured features from sports news using LLM analysis.

    Supports two backends:
        - "ollama": Local LLaMA 3 8B via Ollama (localhost:11434)
        - "openai": OpenAI chat completions API (fallback)

    If the LLM backend is unavailable, neutral feature values are returned
    so downstream pipelines continue to function.

    Args:
        backend: LLM backend to use ("ollama" or "openai").
        model: Model name to query (e.g. "llama3", "gpt-4").
        openai_api_key: API key for OpenAI (required if backend is "openai").

    Example:
        >>> extractor = NewsFeatureExtractor(backend="ollama", model="llama3")
        >>> features = extractor.analyze_headline("Star QB injured", sport="nfl")
    """

    def __init__(
        self,
        backend: str = "ollama",
        model: str = "llama3",
        openai_api_key: str = "",
    ) -> None:
        self.backend = backend.lower()
        self.model = model
        self.openai_api_key = openai_api_key

        if self.backend not in ("ollama", "openai"):
            logger.warning(
                "Unknown backend '%s', defaulting to 'ollama'.", self.backend
            )
            self.backend = "ollama"

        if self.backend == "openai" and not self.openai_api_key:
            logger.warning(
                "OpenAI backend selected but no API key provided. "
                "Calls will likely fail with authentication errors."
            )

        logger.info(
            "NewsFeatureExtractor initialized: backend=%s, model=%s",
            self.backend,
            self.model,
        )

    def analyze_headline(self, headline: str, sport: str) -> Dict[str, float]:
        """Analyze a single sports news headline and extract structured features.

        Sends the headline to the configured LLM backend with a structured
        prompt, then parses the JSON response into a feature dictionary.

        Args:
            headline: The news headline text to analyze.
            sport: The sport category (e.g. "nfl", "nba", "soccer", "ufc").

        Returns:
            Dictionary with six feature keys and float values. Returns
            NEUTRAL_FEATURES if the LLM is unavailable or parsing fails.

        Example:
            >>> extractor = NewsFeatureExtractor()
            >>> features = extractor.analyze_headline(
            ...     "Star quarterback ruled out with shoulder injury",
            ...     sport="nfl"
            ... )
            >>> features["injury_prob"] > 0.5
            True
        """
        if not headline or not headline.strip():
            logger.warning("Empty headline received, returning neutral features.")
            return dict(NEUTRAL_FEATURES)

        prompt = PROMPT_TEMPLATE.format(sport=sport, headline=headline)

        try:
            if self.backend == "ollama":
                raw_response = self._query_ollama(prompt)
            else:
                raw_response = self._query_openai(prompt)

            features = self._parse_features(raw_response)
            logger.debug(
                "Extracted features for headline '%s': %s",
                headline[:60],
                features,
            )
            return features

        except Exception as exc:
            logger.error(
                "Failed to analyze headline '%s': %s",
                headline[:60],
                exc,
                exc_info=True,
            )
            return dict(NEUTRAL_FEATURES)

    def batch_analyze(self, headlines: List[str], sport: str) -> List[Dict[str, float]]:
        """Analyze multiple headlines in sequence and return feature dicts.

        Each headline is analyzed independently. If a single headline fails,
        neutral features are returned for that entry without affecting others.

        Args:
            headlines: List of news headline strings to analyze.
            sport: The sport category for all headlines.

        Returns:
            List of feature dictionaries, one per headline, in the same order.

        Example:
            >>> extractor = NewsFeatureExtractor()
            >>> results = extractor.batch_analyze(
            ...     ["Star QB injured", "Weather: heavy rain expected"],
            ...     sport="nfl"
            ... )
            >>> len(results)
            2
        """
        results: List[Dict[str, float]] = []
        for idx, headline in enumerate(headlines):
            logger.debug("Batch analyzing headline %d/%d", idx + 1, len(headlines))
            features = self.analyze_headline(headline, sport)
            results.append(features)
        return results

    def _query_ollama(self, prompt: str) -> str:
        """Query the local Ollama API at localhost:11434 with retry logic.

        Sends a chat completion request to the Ollama server using the
        configured model. Implements exponential backoff on transient failures.

        Args:
            prompt: The full prompt string to send to the model.

        Returns:
            The model's response text content.

        Raises:
            requests.RequestException: If all retries are exhausted.

        Example:
            >>> extractor = NewsFeatureExtractor(backend="ollama")
            >>> response = extractor._query_ollama("Analyze this news...")
        """
        url = "http://localhost:11434/api/chat"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        backoff = INITIAL_BACKOFF_SECONDS
        last_exception: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(
                    "Ollama request attempt %d/%d", attempt, MAX_RETRIES
                )
                response = requests.post(
                    url,
                    json=payload,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()

                data = response.json()
                content = data.get("message", {}).get("content", "")
                if not content:
                    logger.warning("Ollama returned empty content.")
                return content

            except requests.RequestException as exc:
                last_exception = exc
                logger.warning(
                    "Ollama request failed (attempt %d/%d): %s",
                    attempt,
                    MAX_RETRIES,
                    exc,
                )
                if attempt < MAX_RETRIES:
                    sleep_time = backoff
                    logger.debug("Retrying in %.1f seconds...", sleep_time)
                    time.sleep(sleep_time)
                    backoff *= BACKOFF_MULTIPLIER

        logger.error(
            "All %d Ollama retries exhausted. Last error: %s",
            MAX_RETRIES,
            last_exception,
        )
        raise last_exception or RuntimeError("Ollama request failed after retries")

    def _query_openai(self, prompt: str) -> str:
        """Query the OpenAI chat completions API with retry logic.

        Sends a chat completion request to the OpenAI API using the
        configured model and API key. Implements exponential backoff
        on transient failures.

        Args:
            prompt: The full prompt string to send to the model.

        Returns:
            The model's response text content.

        Raises:
            requests.RequestException: If all retries are exhausted.

        Example:
            >>> extractor = NewsFeatureExtractor(
            ...     backend="openai",
            ...     openai_api_key="sk-..."
            ... )
            >>> response = extractor._query_openai("Analyze this news...")
        """
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        }

        backoff = INITIAL_BACKOFF_SECONDS
        last_exception: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(
                    "OpenAI request attempt %d/%d", attempt, MAX_RETRIES
                )
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()

                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    logger.warning("OpenAI returned no choices.")
                    return ""

                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    logger.warning("OpenAI returned empty content.")
                return content

            except requests.RequestException as exc:
                last_exception = exc
                logger.warning(
                    "OpenAI request failed (attempt %d/%d): %s",
                    attempt,
                    MAX_RETRIES,
                    exc,
                )
                if attempt < MAX_RETRIES:
                    sleep_time = backoff
                    logger.debug("Retrying in %.1f seconds...", sleep_time)
                    time.sleep(sleep_time)
                    backoff *= BACKOFF_MULTIPLIER

        logger.error(
            "All %d OpenAI retries exhausted. Last error: %s",
            MAX_RETRIES,
            last_exception,
        )
        raise last_exception or RuntimeError("OpenAI request failed after retries")

    def _parse_features(self, response: str) -> Dict[str, float]:
        """Parse LLM JSON response into a validated feature dictionary.

        Attempts to extract a JSON object from the raw LLM response text.
        Handles cases where the LLM wraps JSON in markdown code blocks or
        includes extra text. Validates each feature value against its
        expected bounds and clamps out-of-range values.

        Args:
            response: Raw text response from the LLM.

        Returns:
            Dictionary with all six feature keys and clamped float values.
            Returns NEUTRAL_FEATURES if parsing fails entirely.

        Example:
            >>> extractor = NewsFeatureExtractor()
            >>> features = extractor._parse_features(
            ...     '{"injury_prob": 0.9, "key_player_return": 0.0, '
            ...     '"emotional_impact": -0.7, "source_confidence": 0.8, '
            ...     '"weather_impact": 0.0, "lineup_change": 0.85}'
            ... )
            >>> features["injury_prob"]
            0.9
        """
        if not response or not response.strip():
            logger.warning("Empty LLM response, returning neutral features.")
            return dict(NEUTRAL_FEATURES)

        # Try to extract JSON from the response, handling markdown code blocks
        json_str = response.strip()

        # Strip markdown code block wrappers if present
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            # Remove first line (```json or ```) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            json_str = "\n".join(lines).strip()

        # Attempt direct JSON parse
        parsed: Dict[str, Any] | None = None
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError:
            # Try to find JSON object within the response text
            start = json_str.find("{")
            end = json_str.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    parsed = json.loads(json_str[start:end])
                except json.JSONDecodeError as exc:
                    logger.warning(
                        "Failed to parse JSON from LLM response: %s", exc
                    )
            else:
                logger.warning("No JSON object found in LLM response.")

        if parsed is None:
            logger.warning("Returning neutral features due to parse failure.")
            return dict(NEUTRAL_FEATURES)

        # Validate and clamp each feature value
        features: Dict[str, float] = {}
        for key in FEATURE_KEYS:
            if key in parsed:
                try:
                    value = float(parsed[key])
                    low, high = FEATURE_BOUNDS[key]
                    if value < low:
                        logger.debug(
                            "Clamping %s from %.4f to %.4f", key, value, low
                        )
                        value = low
                    elif value > high:
                        logger.debug(
                            "Clamping %s from %.4f to %.4f", key, value, high
                        )
                        value = high
                    features[key] = value
                except (TypeError, ValueError) as exc:
                    logger.warning(
                        "Invalid value for feature '%s': %s (%s). Using neutral.",
                        key,
                        parsed[key],
                        exc,
                    )
                    features[key] = NEUTRAL_FEATURES[key]
            else:
                logger.warning(
                    "Missing feature key '%s' in LLM response. Using neutral value.",
                    key,
                )
                features[key] = NEUTRAL_FEATURES[key]

        return features

    def build_feature_vector(self, analyses: List[Dict[str, float]]) -> np.ndarray:
        """Aggregate a list of feature dictionaries into a single numpy vector.

        Computes the element-wise mean across all analysis results for each
        feature key, producing a fixed-length vector suitable for ML model
        input.

        Args:
            analyses: List of feature dictionaries as returned by
                analyze_headline or batch_analyze.

        Returns:
            numpy array of shape (6,) with mean feature values, in the
            order defined by FEATURE_KEYS. Returns a zero vector if the
            input list is empty.

        Example:
            >>> extractor = NewsFeatureExtractor()
            >>> analyses = [
            ...     {"injury_prob": 0.9, "key_player_return": 0.0,
            ...      "emotional_impact": -0.7, "source_confidence": 0.8,
            ...      "weather_impact": 0.0, "lineup_change": 0.85},
            ...     {"injury_prob": 0.1, "key_player_return": 0.5,
            ...      "emotional_impact": 0.3, "source_confidence": 0.6,
            ...      "weather_impact": -0.8, "lineup_change": 0.2},
            ... ]
            >>> vector = extractor.build_feature_vector(analyses)
            >>> vector.shape
            (6,)
        """
        if not analyses:
            logger.warning(
                "Empty analyses list provided, returning zero feature vector."
            )
            return np.zeros(len(FEATURE_KEYS), dtype=np.float64)

        # Stack feature values into a 2D array and compute column means
        rows: List[List[float]] = []
        for analysis in analyses:
            row = [analysis.get(key, NEUTRAL_FEATURES[key]) for key in FEATURE_KEYS]
            rows.append(row)

        matrix = np.array(rows, dtype=np.float64)
        mean_vector = np.mean(matrix, axis=0)

        logger.debug(
            "Built feature vector from %d analyses: %s",
            len(analyses),
            mean_vector,
        )

        return mean_vector
