"""Tests for debate agents."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from src.decision.debate_agent import (
    OPTIMIST_PROMPT,
    DebateAgent,
    _parse_position,
    create_debate_agents,
)


@pytest.fixture
def mock_groq():
    return MagicMock()


class TestParsePosition:
    def test_valid_json(self):
        raw = json.dumps({
            "probability": 0.75,
            "confidence": "high",
            "reasoning": "Strong trend data supports this.",
        })
        pos = _parse_position("Optimist", raw)

        assert pos.agent_name == "Optimist"
        assert pos.probability == 0.75
        assert pos.confidence == "high"
        assert pos.reasoning == "Strong trend data supports this."

    def test_json_in_text(self):
        raw = (
            'Here is my analysis: {"probability": 0.3, '
            '"confidence": "low", "reasoning": "Weak signals."}'
        )
        pos = _parse_position("Pessimist", raw)

        assert pos.probability == 0.3
        assert pos.confidence == "low"

    def test_probability_clamped_high(self):
        raw = json.dumps({"probability": 1.5, "confidence": "medium", "reasoning": "x"})
        pos = _parse_position("Test", raw)
        assert pos.probability == 1.0

    def test_probability_clamped_low(self):
        raw = json.dumps({"probability": -0.5, "confidence": "medium", "reasoning": "x"})
        pos = _parse_position("Test", raw)
        assert pos.probability == 0.0

    def test_invalid_confidence_defaults_medium(self):
        raw = json.dumps({"probability": 0.5, "confidence": "very_high", "reasoning": "x"})
        pos = _parse_position("Test", raw)
        assert pos.confidence == "medium"

    def test_invalid_json_returns_fallback(self):
        pos = _parse_position("Test", "This is not JSON at all")

        assert pos.agent_name == "Test"
        assert pos.probability == 0.5
        assert pos.confidence == "low"
        assert "This is not JSON at all" in pos.reasoning

    def test_frozen_dataclass(self):
        raw = json.dumps({"probability": 0.6, "confidence": "medium", "reasoning": "ok"})
        pos = _parse_position("Test", raw)
        with pytest.raises(AttributeError):
            pos.probability = 0.9  # type: ignore[misc]


class TestDebateAgent:
    def test_debate_calls_groq(self, mock_groq):
        mock_groq.chat.return_value = json.dumps({
            "probability": 0.65,
            "confidence": "medium",
            "reasoning": "Moderate outlook.",
        })
        agent = DebateAgent("Optimist", OPTIMIST_PROMPT, mock_groq)

        result = agent.debate("Some analysis", "Will renewables reach 50%?")

        assert result.agent_name == "Optimist"
        assert result.probability == 0.65
        mock_groq.chat.assert_called_once()

    def test_debate_agent_name(self, mock_groq):
        agent = DebateAgent("TestAgent", "prompt", mock_groq)
        assert agent.name == "TestAgent"

    def test_debate_includes_question_in_prompt(self, mock_groq):
        mock_groq.chat.return_value = json.dumps({
            "probability": 0.5, "confidence": "medium", "reasoning": "ok"
        })
        agent = DebateAgent("Test", "sys prompt", mock_groq)
        agent.debate("analysis text", "Will X happen?")

        call_messages = mock_groq.chat.call_args[0][0]
        user_msg = call_messages[1]["content"]
        assert "Will X happen?" in user_msg
        assert "analysis text" in user_msg


class TestCreateDebateAgents:
    def test_creates_three_agents(self, mock_groq):
        agents = create_debate_agents(mock_groq)

        assert len(agents) == 3
        names = {a.name for a in agents}
        assert names == {"Optimist", "Pessimist", "Statistician"}

    def test_returns_tuple(self, mock_groq):
        agents = create_debate_agents(mock_groq)
        assert isinstance(agents, tuple)
