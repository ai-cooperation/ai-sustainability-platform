"""Judge agent that synthesizes debate positions into a final forecast."""

from __future__ import annotations

import json
import re

from src.decision.groq_client import GroqClient
from src.decision.models import ForecastPosition, ForecastResult
from src.utils.logging import get_logger

logger = get_logger(__name__)

JUDGE_SYSTEM_PROMPT = (
    "You are a forecasting judge. You receive multiple debate positions "
    "from agents with different perspectives (optimist, pessimist, statistician). "
    "Synthesize their arguments into a balanced final forecast. "
    "Weigh the strength of evidence and reasoning quality, not just average "
    "the probabilities."
)

JUDGE_RESPONSE_FORMAT = (
    "\n\nRespond with a JSON object containing exactly:\n"
    '- "probability": your final probability estimate (float 0.0-1.0)\n'
    '- "confidence": one of "low", "medium", or "high"\n'
    '- "reasoning": your synthesis (3-5 sentences)\n'
    "Return ONLY the JSON object."
)


def _format_positions(positions: list[ForecastPosition]) -> str:
    """Format debate positions for the judge prompt."""
    parts = []
    for pos in positions:
        parts.append(
            f"**{pos.agent_name}** (confidence: {pos.confidence}):\n"
            f"  Probability: {pos.probability:.2f}\n"
            f"  Reasoning: {pos.reasoning}"
        )
    return "\n\n".join(parts)


class JudgeAgent:
    """Synthesizes debate positions into a final forecast."""

    def __init__(self, groq_client: GroqClient):
        self._client = groq_client

    def judge(
        self,
        positions: list[ForecastPosition],
        analysis: str,
        question: str,
    ) -> ForecastResult:
        """Produce a final forecast from debate positions.

        Args:
            positions: List of ForecastPosition from debate agents.
            analysis: Original trend analysis.
            question: The forecast question.

        Returns:
            A ForecastResult with the synthesized forecast.
        """
        positions_text = _format_positions(positions)

        messages = [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT + JUDGE_RESPONSE_FORMAT},
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Analysis:\n{analysis}\n\n"
                    f"Debate Positions:\n{positions_text}\n\n"
                    "Synthesize a final forecast."
                ),
            },
        ]

        logger.info("Judge agent synthesizing forecast")
        raw = self._client.chat(messages, temperature=0.3, max_tokens=1024)
        return self._parse_result(raw, question, positions)

    def _parse_result(
        self,
        raw_response: str,
        question: str,
        positions: list[ForecastPosition],
    ) -> ForecastResult:
        """Parse LLM response into a ForecastResult."""
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
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse judge response: {e}")
            probability = sum(p.probability for p in positions) / max(len(positions), 1)
            confidence = "low"
            reasoning = raw_response[:500]

        return ForecastResult(
            question=question,
            probability=probability,
            confidence=confidence,
            reasoning=reasoning,
            positions=tuple(positions),
        )
