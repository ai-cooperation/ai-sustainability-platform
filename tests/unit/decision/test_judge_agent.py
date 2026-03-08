"""Tests for JudgeAgent."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from src.decision.judge_agent import JudgeAgent, _format_positions
from src.decision.models import ForecastPosition, ForecastResult


@pytest.fixture
def mock_groq():
    return MagicMock()


@pytest.fixture
def sample_positions():
    return [
        ForecastPosition(
            agent_name="Optimist",
            probability=0.75,
            reasoning="Strong green transition momentum.",
            confidence="high",
        ),
        ForecastPosition(
            agent_name="Pessimist",
            probability=0.35,
            reasoning="Policy uncertainty remains high.",
            confidence="medium",
        ),
        ForecastPosition(
            agent_name="Statistician",
            probability=0.55,
            reasoning="Historical base rate suggests moderate probability.",
            confidence="high",
        ),
    ]


class TestFormatPositions:
    def test_formats_all_positions(self, sample_positions):
        text = _format_positions(sample_positions)

        assert "Optimist" in text
        assert "Pessimist" in text
        assert "Statistician" in text
        assert "0.75" in text
        assert "0.35" in text

    def test_empty_positions(self):
        text = _format_positions([])
        assert text == ""


class TestJudgeAgent:
    def test_successful_judgment(self, mock_groq, sample_positions):
        mock_groq.chat.return_value = json.dumps({
            "probability": 0.58,
            "confidence": "medium",
            "reasoning": "Balanced assessment favoring moderate optimism.",
        })

        judge = JudgeAgent(mock_groq)
        result = judge.judge(sample_positions, "Some analysis", "Will X happen?")

        assert isinstance(result, ForecastResult)
        assert result.question == "Will X happen?"
        assert result.probability == 0.58
        assert result.confidence == "medium"
        assert len(result.positions) == 3
        assert result.created_at is not None

    def test_malformed_response_uses_average(self, mock_groq, sample_positions):
        mock_groq.chat.return_value = "I cannot parse this into JSON properly"

        judge = JudgeAgent(mock_groq)
        result = judge.judge(sample_positions, "analysis", "question?")

        # Falls back to average: (0.75 + 0.35 + 0.55) / 3 = 0.55
        assert abs(result.probability - 0.55) < 0.01
        assert result.confidence == "low"

    def test_prompt_includes_question_and_analysis(self, mock_groq, sample_positions):
        mock_groq.chat.return_value = json.dumps({
            "probability": 0.5, "confidence": "medium", "reasoning": "ok"
        })

        judge = JudgeAgent(mock_groq)
        judge.judge(sample_positions, "trend analysis here", "Big question?")

        call_messages = mock_groq.chat.call_args[0][0]
        user_msg = call_messages[1]["content"]
        assert "Big question?" in user_msg
        assert "trend analysis here" in user_msg

    def test_result_is_frozen(self, mock_groq, sample_positions):
        mock_groq.chat.return_value = json.dumps({
            "probability": 0.5, "confidence": "medium", "reasoning": "ok"
        })

        judge = JudgeAgent(mock_groq)
        result = judge.judge(sample_positions, "analysis", "question?")

        with pytest.raises(AttributeError):
            result.probability = 0.9  # type: ignore[misc]

    def test_probability_clamped(self, mock_groq, sample_positions):
        mock_groq.chat.return_value = json.dumps({
            "probability": 2.5, "confidence": "high", "reasoning": "over"
        })

        judge = JudgeAgent(mock_groq)
        result = judge.judge(sample_positions, "analysis", "question?")

        assert result.probability == 1.0
