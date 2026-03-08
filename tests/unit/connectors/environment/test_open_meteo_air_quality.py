"""Tests for OpenMeteoAirQualityConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.environment.open_meteo_air_quality import (
    OpenMeteoAirQualityConnector,
)


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings"):
        return OpenMeteoAirQualityConnector()


@pytest.fixture
def sample_response():
    return {
        "latitude": 48.85,
        "longitude": 2.35,
        "hourly": {
            "time": [
                "2026-03-01T00:00",
                "2026-03-01T01:00",
                "2026-03-01T02:00",
            ],
            "pm2_5": [12.5, 14.2, 11.8],
            "pm10": [25.0, 28.1, 22.3],
            "carbon_monoxide": [300.0, 310.5, 295.0],
            "nitrogen_dioxide": [18.0, 20.1, 16.5],
            "ozone": [45.0, 42.3, 48.1],
            "european_aqi": [35, 40, 32],
        },
    }


class TestOpenMeteoAirQualityConnector:
    def test_name(self, connector):
        assert connector.name == "open_meteo_air_quality"

    def test_domain(self, connector):
        assert connector.domain == "environment"

    @patch("src.connectors.environment.open_meteo_air_quality.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch(latitude=48.85, longitude=2.35)

        assert "hourly" in result
        mock_get.assert_called_once()

    @patch("src.connectors.environment.open_meteo_air_quality.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Connection error")

        with pytest.raises(ConnectorError, match="API request failed"):
            connector.fetch(latitude=48.85, longitude=2.35)

    @patch("src.connectors.environment.open_meteo_air_quality.requests.get")
    def test_fetch_missing_hourly_key(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"latitude": 48.85}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="missing 'hourly' key"):
            connector.fetch()

    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        assert len(df) == 3
        assert list(df.columns) == [
            "timestamp", "latitude", "longitude",
            "pm2_5", "pm10", "co", "no2", "o3", "aqi",
        ]

    def test_normalize_empty_hourly(self, connector):
        with pytest.raises(ConnectorError, match="no hourly data"):
            connector.normalize({"hourly": {}})

    def test_normalize_missing_time(self, connector):
        with pytest.raises(ConnectorError, match="no hourly data"):
            connector.normalize({"hourly": {"pm2_5": [1, 2]}})

    def test_normalize_values(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert df["pm2_5"].iloc[0] == 12.5
        assert df["latitude"].iloc[0] == 48.85
        assert df["longitude"].iloc[0] == 2.35
