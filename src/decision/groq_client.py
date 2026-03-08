"""Groq LLM client wrapper."""

from __future__ import annotations

import httpx

from src.utils.config import get_settings

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqClient:
    """Client for Groq LLM API (OpenAI-compatible)."""

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        settings = get_settings()
        self._api_key = settings.groq_api_key
        self._model = model
        self._client = httpx.Client(timeout=60.0)

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

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
