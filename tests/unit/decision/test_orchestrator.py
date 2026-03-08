"""Tests for ForecastOrchestrator."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from src.decision.models import ForecastPosition, ForecastResult
from src.decision.orchestrator import ForecastOrchestrator


@pytest.fixture
def mock_groq():
    return MagicMock()


@pytest.fixture
def sample_signals():
    return {
        "carbon_intensity": 180.0,
        "carbon_index": "moderate",
        "aqi": 45.0,
        "signals": [],
        "collected_at": "2026-01-01T00:00:00+00:00",
    }


@pytest.fixture
def sample_positions():
    return [
        ForecastPosition("Optimist", 0.75, "Good outlook.", "high"),
        ForecastPosition("Pessimist", 0.35, "Risks remain.", "medium"),
        ForecastPosition("Statistician", 0.55, "Base rate.", "high"),
    ]


@pytest.fixture
def sample_result(sample_positions):
    return ForecastResult(
        question="Will renewables reach 50%?",
        probability=0.58,
        confidence="medium",
        reasoning="Balanced view.",
        positions=tuple(sample_positions),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestForecastOrchestrator:
    @patch("src.decision.orchestrator.send_telegram")
    @patch("src.decision.orchestrator.JudgeAgent")
    @patch("src.decision.orchestrator.create_debate_agents")
    @patch("src.decision.orchestrator.AnalystAgent")
    @patch("src.decision.orchestrator.SignalAgent")
    def test_full_flow(
        self,
        mock_signal_cls,
        mock_analyst_cls,
        mock_debate_fn,
        mock_judge_cls,
        mock_telegram,
        mock_groq,
        sample_signals,
        sample_positions,
        sample_result,
    ):
        # Setup mocks
        mock_signal_cls.return_value.collect.return_value = sample_signals
        mock_analyst_cls.return_value.analyze.return_value = "Trend analysis text"

        debate_agents = []
        for pos in sample_positions:
            agent = MagicMock()
            agent.name = pos.agent_name
            agent.debate.return_value = pos
            debate_agents.append(agent)
        mock_debate_fn.return_value = tuple(debate_agents)

        mock_judge_cls.return_value.judge.return_value = sample_result

        # Run
        orchestrator = ForecastOrchestrator(groq_client=mock_groq)
        result = orchestrator.run_forecast("Will renewables reach 50%?")

        # Verify
        assert result.question == "Will renewables reach 50%?"
        assert result.probability == 0.58
        mock_signal_cls.return_value.collect.assert_called_once()
        mock_analyst_cls.return_value.analyze.assert_called_once_with(sample_signals)
        for agent in debate_agents:
            agent.debate.assert_called_once_with(
                "Trend analysis text", "Will renewables reach 50%?"
            )
        mock_judge_cls.return_value.judge.assert_called_once()
        mock_telegram.assert_called_once()

    @patch("src.decision.orchestrator.send_telegram")
    @patch("src.decision.orchestrator.JudgeAgent")
    @patch("src.decision.orchestrator.create_debate_agents")
    @patch("src.decision.orchestrator.AnalystAgent")
    @patch("src.decision.orchestrator.SignalAgent")
    def test_telegram_notification_content(
        self,
        mock_signal_cls,
        mock_analyst_cls,
        mock_debate_fn,
        mock_judge_cls,
        mock_telegram,
        mock_groq,
        sample_signals,
        sample_positions,
        sample_result,
    ):
        mock_signal_cls.return_value.collect.return_value = sample_signals
        mock_analyst_cls.return_value.analyze.return_value = "analysis"
        mock_debate_fn.return_value = tuple(
            MagicMock(name=p.agent_name, debate=MagicMock(return_value=p))
            for p in sample_positions
        )
        mock_judge_cls.return_value.judge.return_value = sample_result

        orchestrator = ForecastOrchestrator(groq_client=mock_groq)
        orchestrator.run_forecast("Will renewables reach 50%?")

        telegram_msg = mock_telegram.call_args[0][0]
        assert "Will renewables reach 50%?" in telegram_msg
        assert "58%" in telegram_msg
        assert "Optimist" in telegram_msg

    @patch("src.decision.orchestrator.send_telegram")
    @patch("src.decision.orchestrator.JudgeAgent")
    @patch("src.decision.orchestrator.create_debate_agents")
    @patch("src.decision.orchestrator.AnalystAgent")
    @patch("src.decision.orchestrator.SignalAgent")
    def test_debate_agents_called_sequentially(
        self,
        mock_signal_cls,
        mock_analyst_cls,
        mock_debate_fn,
        mock_judge_cls,
        mock_telegram,
        mock_groq,
        sample_signals,
        sample_positions,
        sample_result,
    ):
        mock_signal_cls.return_value.collect.return_value = sample_signals
        mock_analyst_cls.return_value.analyze.return_value = "analysis"

        call_order = []
        agents = []
        for pos in sample_positions:
            agent = MagicMock()
            agent.name = pos.agent_name

            def make_debate(p, name):
                def debate_fn(analysis, question):
                    call_order.append(name)
                    return p
                return debate_fn

            agent.debate.side_effect = make_debate(pos, pos.agent_name)
            agents.append(agent)

        mock_debate_fn.return_value = tuple(agents)
        mock_judge_cls.return_value.judge.return_value = sample_result

        orchestrator = ForecastOrchestrator(groq_client=mock_groq)
        orchestrator.run_forecast("Test?")

        assert call_order == ["Optimist", "Pessimist", "Statistician"]
