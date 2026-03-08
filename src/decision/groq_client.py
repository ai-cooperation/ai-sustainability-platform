"""Groq LLM client wrapper with rate limiting."""

from __future__ import annotations

import time

import httpx

from src.utils.config import get_settings
from src.utils.logging import get_logger

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

logger = get_logger(__name__)


class GroqClient:
    """Client for Groq LLM API with built-in rate limiting.

    Groq free tier limits:
    - 30 requests/minute
    - 14,400 requests/day
    - 6,000 tokens/minute
    """

    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        min_request_interval: float = 2.5,
        max_retries: int = 3,
    ):
        settings = get_settings()
        self._api_key = settings.groq_api_key
        self._model = model
        self._client = httpx.Client(timeout=60.0)
        self._min_interval = min_request_interval
        self._max_retries = max_retries
        self._last_request_time: float = 0

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat completion request to Groq.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.

        Returns:
            The assistant's response text.

        Raises:
            ValueError: If GROQ_API_KEY is not configured.
            httpx.HTTPStatusError: If the API request fails.
        """
        if not self._api_key:
            raise ValueError("GROQ_API_KEY not configured")

        self._wait_for_rate_limit()

        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._client.post(
                    GROQ_API_URL,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429:
                    retry_after = float(
                        exc.response.headers.get("retry-after", 10)
                    )
                    logger.warning(
                        f"Rate limited, retry {attempt}/{self._max_retries}"
                        f" after {retry_after}s"
                    )
                    time.sleep(retry_after)
                    continue
                raise
        raise RuntimeError(
            f"Groq API failed after {self._max_retries} retries"
        )

    def _wait_for_rate_limit(self) -> None:
        """Enforce minimum interval between requests."""
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self._min_interval:
            wait = self._min_interval - elapsed
            logger.debug(f"Rate limit: waiting {wait:.1f}s")
            time.sleep(wait)
        self._last_request_time = time.monotonic()

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
