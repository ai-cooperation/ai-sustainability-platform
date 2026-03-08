"""Tests for SignalAgent."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.decision.models import SignalData
from src.decision.signal_agent import SignalAgent


@pytest.fixture
def agent():
    return SignalAgent()


def _make_carbon_result():
    """Create a mock ConnectorResult for carbon intensity."""
    result = MagicMock()
    result.data = pd.DataFrame(
        {
            "intensity_forecast": [180.0],
            "intensity_actual": [175.0],
            "index": ["moderate"],
        }
    )
    result.fetched_at = datetime(2026, 1, 1, tzinfo=UTC)
    return result


def _make_aqi_result():
    """Create a mock ConnectorResult for air quality."""
    result = MagicMock()
    result.data = pd.DataFrame(
        {
            "aqi": [45.0],
            "pm2_5": [12.0],
        }
    )
    result.fetched_at = datetime(2026, 1, 1, tzinfo=UTC)
    return result


class TestSignalAgentCollect:
    @patch("src.decision.signal_agent.OpenMeteoAirQualityConnector")
    @patch("src.decision.signal_agent.CarbonIntensityUKConnector")
    def test_collect_all_sources_success(self, mock_carbon_cls, mock_aqi_cls, agent):
        mock_carbon_cls.return_value.run.return_value = _make_carbon_result()
        mock_aqi_cls.return_value.run.return_value = _make_aqi_result()

        result = agent.collect()

        assert result["carbon_intensity"] == 180.0
        assert result["carbon_index"] == "moderate"
        assert result["aqi"] == 45.0
        assert len(result["signals"]) == 2
        assert "collected_at" in result

    @patch("src.decision.signal_agent.OpenMeteoAirQualityConnector")
    @patch("src.decision.signal_agent.CarbonIntensityUKConnector")
    def test_collect_carbon_failure_continues(self, mock_carbon_cls, mock_aqi_cls, agent):
        mock_carbon_cls.return_value.run.side_effect = Exception("API down")
        mock_aqi_cls.return_value.run.return_value = _make_aqi_result()

        result = agent.collect()

        assert "carbon_intensity" not in result
        assert result["aqi"] == 45.0
        assert len(result["signals"]) == 1

    @patch("src.decision.signal_agent.OpenMeteoAirQualityConnector")
    @patch("src.decision.signal_agent.CarbonIntensityUKConnector")
    def test_collect_all_failures(self, mock_carbon_cls, mock_aqi_cls, agent):
        mock_carbon_cls.return_value.run.side_effect = Exception("down")
        mock_aqi_cls.return_value.run.side_effect = Exception("down")

        result = agent.collect()

        assert result["signals"] == []
        assert "collected_at" in result

    @patch("src.decision.signal_agent.OpenMeteoAirQualityConnector")
    @patch("src.decision.signal_agent.CarbonIntensityUKConnector")
    def test_signals_are_signal_data_instances(self, mock_carbon_cls, mock_aqi_cls, agent):
        mock_carbon_cls.return_value.run.return_value = _make_carbon_result()
        mock_aqi_cls.return_value.run.return_value = _make_aqi_result()

        result = agent.collect()

        for signal in result["signals"]:
            assert isinstance(signal, SignalData)

    @patch("src.decision.signal_agent.OpenMeteoAirQualityConnector")
    @patch("src.decision.signal_agent.CarbonIntensityUKConnector")
    def test_empty_dataframe_skipped(self, mock_carbon_cls, mock_aqi_cls, agent):
        empty_result = MagicMock()
        empty_result.data = pd.DataFrame()
        mock_carbon_cls.return_value.run.return_value = empty_result
        mock_aqi_cls.return_value.run.side_effect = Exception("down")

        result = agent.collect()

        assert "carbon_intensity" not in result
        assert result["signals"] == []
