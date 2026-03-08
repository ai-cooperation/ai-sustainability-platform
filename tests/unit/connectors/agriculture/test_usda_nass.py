"""Unit tests for USDANASSConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.agriculture.usda_nass import USDANASSConnector
from src.connectors.base import ConnectorError


@pytest.fixture
def connector():
    """Create a USDANASSConnector with mocked settings and API key."""
    with patch("src.connectors.base.get_settings") as mock_settings, \
         patch("src.connectors.base.get_logger") as mock_logger:
        settings = MagicMock()
        settings.usda_nass_api_key = "test-api-key-12345"
        mock_settings.return_value = settings
        mock_logger.return_value = MagicMock()
        return USDANASSConnector()


@pytest.fixture
def connector_no_key():
    """Create a USDANASSConnector without API key."""
    with patch("src.connectors.base.get_settings") as mock_settings, \
         patch("src.connectors.base.get_logger") as mock_logger:
        settings = MagicMock()
        settings.usda_nass_api_key = ""
        mock_settings.return_value = settings
        mock_logger.return_value = MagicMock()
        return USDANASSConnector()


@pytest.fixture
def sample_response():
    """Sample USDA NASS API response."""
    return {
        "data": [
            {
                "year": 2023,
                "state_name": "IOWA",
                "commodity_desc": "CORN",
                "statisticcat_desc": "PRODUCTION",
                "Value": "2,296,200,000",
                "unit_desc": "BU",
            },
            {
                "year": 2023,
                "state_name": "ILLINOIS",
                "commodity_desc": "CORN",
                "statisticcat_desc": "PRODUCTION",
                "Value": "2,162,400,000",
                "unit_desc": "BU",
            },
        ]
    }


class TestUSDANASSProperties:
    def test_name(self, connector):
        assert connector.name == "usda_nass"

    def test_domain(self, connector):
        assert connector.domain == "agriculture"


class TestUSDANASSFetch:
    @patch("src.connectors.agriculture.usda_nass.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.fetch(commodity_desc="CORN", year="2023")

        assert result == sample_response
        params = mock_get.call_args[1]["params"]
        assert params["key"] == "test-api-key-12345"
        assert params["commodity_desc"] == "CORN"
        assert params["year"] == "2023"
        assert params["format"] == "JSON"

    @patch("src.connectors.agriculture.usda_nass.requests.get")
    def test_fetch_with_all_params(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        connector.fetch(
            commodity_desc="WHEAT",
            year="2022",
            state_name="KANSAS",
            statisticcat_desc="YIELD",
        )

        params = mock_get.call_args[1]["params"]
        assert params["commodity_desc"] == "WHEAT"
        assert params["state_name"] == "KANSAS"
        assert params["statisticcat_desc"] == "YIELD"

    def test_fetch_missing_api_key(self, connector_no_key):
        with pytest.raises(ConnectorError, match="API key is required"):
            connector_no_key.fetch()

    @patch("src.connectors.agriculture.usda_nass.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Server error")

        with pytest.raises(ConnectorError, match="USDA NASS API request failed"):
            connector.fetch()

    @patch("src.connectors.agriculture.usda_nass.requests.get")
    def test_fetch_api_error_response(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": ["exceeds limit of 50000"]}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="USDA NASS API error"):
            connector.fetch()

    @patch("src.connectors.agriculture.usda_nass.requests.get")
    def test_fetch_non_dict_response(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = "invalid"
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="unexpected format"):
            connector.fetch()


class TestUSDANASSNormalize:
    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "timestamp" in df.columns
        assert "state" in df.columns
        assert "commodity" in df.columns
        assert "statistic" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert df["timestamp"].dtype .kind == "M"

    def test_normalize_timestamp_jan_first(self, connector, sample_response):
        df = connector.normalize(sample_response)
        assert df["timestamp"].iloc[0] == pd.Timestamp("2023-01-01")

    def test_normalize_comma_separated_values(self, connector, sample_response):
        df = connector.normalize(sample_response)
        assert df["value"].iloc[0] == 2296200000.0

    def test_normalize_non_numeric_value(self, connector):
        raw = {
            "data": [
                {
                    "year": 2023,
                    "state_name": "IOWA",
                    "commodity_desc": "CORN",
                    "statisticcat_desc": "AREA",
                    "Value": "(D)",
                    "unit_desc": "ACRES",
                },
            ]
        }
        df = connector.normalize(raw)
        assert len(df) == 1
        assert df["value"].iloc[0] is None

    def test_normalize_non_dict(self, connector):
        with pytest.raises(ConnectorError, match="Expected dict"):
            connector.normalize([1, 2])

    def test_normalize_missing_data_key(self, connector):
        with pytest.raises(ConnectorError, match="Missing 'data' key"):
            connector.normalize({"status": "ok"})

    def test_normalize_empty_data(self, connector):
        with pytest.raises(ConnectorError, match="no records"):
            connector.normalize({"data": []})

    def test_normalize_skips_records_without_year(self, connector):
        raw = {
            "data": [
                {"year": 2023, "state_name": "IOWA", "commodity_desc": "CORN", "statisticcat_desc": "YIELD", "Value": "200", "unit_desc": "BU / ACRE"},
                {"state_name": "OHIO", "commodity_desc": "CORN", "Value": "180"},
            ]
        }
        df = connector.normalize(raw)
        assert len(df) == 1

    def test_normalize_all_records_missing_year(self, connector):
        raw = {
            "data": [
                {"state_name": "IOWA", "commodity_desc": "CORN"},
            ]
        }
        with pytest.raises(ConnectorError, match="No valid records"):
            connector.normalize(raw)
