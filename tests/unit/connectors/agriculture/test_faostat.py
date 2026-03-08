"""Unit tests for FAOSTATConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.agriculture.faostat import FAOSTATConnector
from src.connectors.base import ConnectorError


@pytest.fixture
def connector():
    """Create a FAOSTATConnector with mocked settings."""
    with patch("src.connectors.base.get_settings") as mock_settings, \
         patch("src.connectors.base.get_logger") as mock_logger:
        mock_settings.return_value = MagicMock()
        mock_logger.return_value = MagicMock()
        return FAOSTATConnector()


@pytest.fixture
def sample_response():
    """Sample FAOSTAT API response."""
    return {
        "data": [
            {
                "Year": 2020,
                "Area": "World",
                "Item": "Wheat",
                "Element": "Production",
                "Value": 760925831.0,
                "Unit": "tonnes",
            },
            {
                "Year": 2021,
                "Area": "World",
                "Item": "Wheat",
                "Element": "Production",
                "Value": 770884207.0,
                "Unit": "tonnes",
            },
        ]
    }


class TestFAOSTATProperties:
    def test_name(self, connector):
        assert connector.name == "faostat"

    def test_domain(self, connector):
        assert connector.domain == "agriculture"


class TestFAOSTATFetch:
    @patch("src.connectors.agriculture.faostat.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.fetch(faostat_domain="QCL", year="2020")

        assert result == sample_response
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "QCL" in call_args[0][0] or call_args[1].get("params", {}).get("year") == "2020"

    @patch("src.connectors.agriculture.faostat.requests.get")
    def test_fetch_with_all_params(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        connector.fetch(
            faostat_domain="RL",
            area_code="5000",
            item_code="15",
            element_code="5510",
            year="2020,2021",
        )

        call_kwargs = mock_get.call_args
        params = call_kwargs[1]["params"]
        assert params["area_code"] == "5000"
        assert params["item_code"] == "15"
        assert params["element_code"] == "5510"
        assert params["year"] == "2020,2021"

    @patch("src.connectors.agriculture.faostat.requests.get")
    def test_fetch_default_domain(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        connector.fetch()

        url = mock_get.call_args[0][0]
        assert url.endswith("/QCL")

    @patch("src.connectors.agriculture.faostat.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Connection refused")

        with pytest.raises(ConnectorError, match="FAOSTAT API request failed"):
            connector.fetch()

    @patch("src.connectors.agriculture.faostat.requests.get")
    def test_fetch_non_dict_response(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = "not a dict"
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="unexpected format"):
            connector.fetch()


class TestFAOSTATNormalize:
    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "timestamp" in df.columns
        assert "country" in df.columns
        assert "item" in df.columns
        assert "element" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert df["timestamp"].dtype .kind == "M"

    def test_normalize_timestamp_jan_first(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert df["timestamp"].iloc[0] == pd.Timestamp("2020-01-01")
        assert df["timestamp"].iloc[1] == pd.Timestamp("2021-01-01")

    def test_normalize_non_dict(self, connector):
        with pytest.raises(ConnectorError, match="Expected dict"):
            connector.normalize([1, 2, 3])

    def test_normalize_missing_data_key(self, connector):
        with pytest.raises(ConnectorError, match="Missing 'data' key"):
            connector.normalize({"metadata": {}})

    def test_normalize_empty_data(self, connector):
        with pytest.raises(ConnectorError, match="no records"):
            connector.normalize({"data": []})

    def test_normalize_skips_records_without_year(self, connector):
        raw = {
            "data": [
                {
                    "Year": 2020, "Area": "World",
                    "Item": "Wheat", "Element": "Production",
                    "Value": 100, "Unit": "t",
                },
                {
                    "Area": "World", "Item": "Rice",
                    "Element": "Production",
                    "Value": 200, "Unit": "t",
                },
            ]
        }
        df = connector.normalize(raw)
        assert len(df) == 1

    def test_normalize_all_records_missing_year(self, connector):
        raw = {
            "data": [
                {"Area": "World", "Item": "Wheat"},
            ]
        }
        with pytest.raises(ConnectorError, match="No valid records"):
            connector.normalize(raw)
