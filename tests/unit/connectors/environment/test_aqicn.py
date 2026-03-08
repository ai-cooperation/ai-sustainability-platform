"""Tests for AQICNConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.environment.aqicn import AQICNConnector


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings_instance = MagicMock()
        settings_instance.aqicn_api_token = "test-token"
        mock_settings.return_value = settings_instance
        return AQICNConnector()


@pytest.fixture
def sample_response():
    return {
        "status": "ok",
        "data": {
            "aqi": 85,
            "city": {"name": "Beijing"},
            "time": {"iso": "2026-01-15T12:00:00+08:00"},
            "iaqi": {
                "pm25": {"v": 35.0},
                "pm10": {"v": 50.0},
                "o3": {"v": 28.0},
                "no2": {"v": 15.0},
                "so2": {"v": 5.0},
                "co": {"v": 3.2},
            },
        },
    }


class TestAQICNConnector:
    def test_name(self, connector):
        assert connector.name == "aqicn"

    def test_domain(self, connector):
        assert connector.domain == "environment"

    def test_missing_api_token(self):
        with patch("src.connectors.base.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.aqicn_api_token = ""
            mock_settings.return_value = settings_instance
            conn = AQICNConnector()

            with pytest.raises(ConnectorError, match="AQICN_API_TOKEN not configured"):
                conn.fetch()

    @patch("src.connectors.environment.aqicn.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch(city="beijing")

        assert result["status"] == "ok"
        assert "data" in result

    @patch("src.connectors.environment.aqicn.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Network error")

        with pytest.raises(ConnectorError, match="API request failed"):
            connector.fetch()

    @patch("src.connectors.environment.aqicn.requests.get")
    def test_fetch_api_error_status(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "error",
            "data": "Invalid key",
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="API returned error status"):
            connector.fetch()

    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        assert len(df) == 1
        expected_cols = {
            "timestamp", "city", "aqi", "pm25", "pm10",
            "o3", "no2", "so2", "co",
        }
        assert set(df.columns) == expected_cols

    def test_normalize_values(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert df["city"].iloc[0] == "Beijing"
        assert df["aqi"].iloc[0] == 85
        assert df["pm25"].iloc[0] == 35.0
        assert df["co"].iloc[0] == 3.2

    def test_normalize_empty_data(self, connector):
        with pytest.raises(ConnectorError, match="no data"):
            connector.normalize({"status": "ok", "data": {}})
