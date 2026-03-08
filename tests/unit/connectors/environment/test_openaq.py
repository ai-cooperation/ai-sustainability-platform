"""Tests for OpenAQConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.environment.openaq import OpenAQConnector


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings_instance = MagicMock()
        settings_instance.openaq_api_key = "test-api-key"
        mock_settings.return_value = settings_instance
        return OpenAQConnector()


@pytest.fixture
def sample_response():
    return {
        "results": [
            {
                "name": "Station A",
                "lastUpdated": "2026-01-15T12:00:00Z",
                "parameter": "pm25",
                "value": 35.2,
                "unit": "ug/m3",
                "country": {"code": "US"},
            },
            {
                "name": "Station B",
                "lastUpdated": "2026-01-15T13:00:00Z",
                "parameter": "pm10",
                "value": 50.1,
                "unit": "ug/m3",
                "country": {"code": "US"},
            },
        ],
    }


class TestOpenAQConnector:
    def test_name(self, connector):
        assert connector.name == "openaq"

    def test_domain(self, connector):
        assert connector.domain == "environment"

    def test_missing_api_key(self):
        with patch("src.connectors.base.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.openaq_api_key = ""
            mock_settings.return_value = settings_instance
            conn = OpenAQConnector()

            with pytest.raises(ConnectorError, match="OPENAQ_API_KEY not configured"):
                conn.fetch()

    @patch("src.connectors.environment.openaq.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch(endpoint="locations", country="US")

        assert "results" in result
        mock_get.assert_called_once()
        # Verify API key header is sent
        call_kwargs = mock_get.call_args
        assert call_kwargs[1]["headers"]["X-API-Key"] == "test-api-key"

    @patch("src.connectors.environment.openaq.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Forbidden")

        with pytest.raises(ConnectorError, match="API request failed"):
            connector.fetch()

    @patch("src.connectors.environment.openaq.requests.get")
    def test_fetch_missing_results(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"meta": {}}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="missing 'results' key"):
            connector.fetch()

    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        assert len(df) == 2
        assert "location" in df.columns
        assert "parameter" in df.columns
        assert "country" in df.columns

    def test_normalize_values(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert df["location"].iloc[0] == "Station A"
        assert df["value"].iloc[0] == 35.2
        assert df["country"].iloc[0] == "US"

    def test_normalize_empty_results(self, connector):
        with pytest.raises(ConnectorError, match="no results"):
            connector.normalize({"results": []})
