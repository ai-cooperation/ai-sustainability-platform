"""Debate agents with specialized perspectives for forecasting."""

from __future__ import annotations

import json
import re

from src.decision.groq_client import GroqClient
from src.decision.models import ForecastPosition
from src.utils.logging import get_logger

logger = get_logger(__name__)

OPTIMIST_PROMPT = (
    "You are an optimistic sustainability forecaster. "
    "You emphasize positive trends: green energy transition, improving efficiency, "
    "policy momentum, technological breakthroughs, and growing public awareness. "
    "You acknowledge risks but believe progress will continue."
)

PESSIMIST_PROMPT = (
    "You are a cautious sustainability forecaster. "
    "You emphasize risks: fossil fuel dependency, policy failures, greenwashing, "
    "rebound effects, and insufficient pace of change. "
    "You acknowledge progress but believe obstacles are underestimated."
)

STATISTICIAN_PROMPT = (
    "You are a statistical sustainability forecaster. "
    "You emphasize historical data, base rates, regression to the mean, "
    "and quantitative evidence. You avoid narrative bias and focus on "
    "what the numbers actually show."
)

RESPONSE_FORMAT_INSTRUCTION = (
    "\n\nRespond with a JSON object containing exactly these fields:\n"
    '- "probability": a float between 0.0 and 1.0\n'
    '- "confidence": one of "low", "medium", or "high"\n'
    '- "reasoning": a brief explanation (2-3 sentences)\n'
    "Return ONLY the JSON object, no other text."
)


def _parse_position(agent_name: str, raw_response: str) -> ForecastPosition:
    """Parse LLM response into a ForecastPosition.

    Falls back to defaults if JSON parsing fails.
    """
    try:
        match = re.search(r"\{[^}]+\}", raw_response, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            data = json.loads(raw_response)

        probability = max(0.0, min(1.0, float(data.get("probability", 0.5))))
        confidence = data.get("confidence", "medium")
        if confidence not in ("low", "medium", "high"):
            confidence = "medium"
        reasoning = str(data.get("reasoning", raw_response))

        return ForecastPosition(
            agent_name=agent_name,
            probability=probability,
            reasoning=reasoning,
            confidence=confidence,
        )
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning(f"Failed to parse {agent_name} response: {e}")
        return ForecastPosition(
            agent_name=agent_name,
            probability=0.5,
            reasoning=raw_response[:500],
            confidence="low",
        )


class DebateAgent:
    """A debate agent with a specific perspective."""

    def __init__(
        self,
        agent_name: str,
        system_prompt: str,
        groq_client: GroqClient,
    ):
        self._name = agent_name
        self._system_prompt = system_prompt
        self._client = groq_client

    @property
    def name(self) -> str:
        return self._name

    def debate(self, analysis: str, question: str) -> ForecastPosition:
        """Produce a forecast position on the given question.

        Args:
            analysis: Trend analysis from the AnalystAgent.
            question: The forecast question to debate.

        Returns:
            A ForecastPosition with probability, reasoning, and confidence.
        """
        messages = [
            {"role": "system", "content": self._system_prompt + RESPONSE_FORMAT_INSTRUCTION},
            {
                "role": "user",
                "content": (
                    f"Analysis:\n{analysis}\n\n"
                    f"Forecast question: {question}\n\n"
                    "What is your probability estimate?"
                ),
            },
        ]

        logger.info(f"Debate agent '{self._name}' responding")
        raw = self._client.chat(messages, temperature=0.7, max_tokens=512)
        return _parse_position(self._name, raw)


def create_debate_agents(groq_client: GroqClient) -> tuple[DebateAgent, ...]:
    """Create the standard trio of debate agents.

    Returns:
        Tuple of (OptimistAgent, PessimistAgent, StatisticianAgent).
    """
    return (
        DebateAgent("Optimist", OPTIMIST_PROMPT, groq_client),
        DebateAgent("Pessimist", PESSIMIST_PROMPT, groq_client),
        DebateAgent("Statistician", STATISTICIAN_PROMPT, groq_client),
    )
