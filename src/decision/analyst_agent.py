"""Analyst agent that produces trend analysis from signal data."""

from __future__ import annotations

import json

from src.decision.groq_client import GroqClient
from src.decision.models import SignalData
from src.utils.logging import get_logger

logger = get_logger(__name__)

ANALYST_SYSTEM_PROMPT = (
    "You are a sustainability data analyst. "
    "Analyze the provided data signals and identify key trends, "
    "anomalies, and risk factors. "
    "Be concise and focus on actionable insights."
)


def _serialize_signals(summary: dict) -> str:
    """Convert summary dict to a string for the LLM prompt."""
    clean = {}
    for key, value in summary.items():
        if key == "signals":
            clean[key] = [
                {
                    "source": s.source,
                    "value": s.value,
                    "unit": s.unit,
                    "timestamp": s.timestamp.isoformat(),
                }
                if isinstance(s, SignalData)
                else str(s)
                for s in value
            ]
        else:
            clean[key] = value
    return json.dumps(clean, indent=2, default=str)


class AnalystAgent:
    """Analyzes collected signal data using Groq LLM."""

    def __init__(self, groq_client: GroqClient):
        self._client = groq_client

    def analyze(self, signals: dict) -> str:
        """Analyze signal data and return trend analysis.

        Args:
            signals: Summary dict from SignalAgent.collect().

        Returns:
            Structured analysis text from the LLM.
        """
        signals_text = _serialize_signals(signals)

        messages = [
            {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Analyze these sustainability signals:\n\n{signals_text}"
                ),
            },
        ]

        logger.info("Running analyst agent")
        return self._client.chat(messages, temperature=0.4, max_tokens=1024)
