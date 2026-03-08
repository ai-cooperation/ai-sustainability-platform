"""Tests for WorldBankClimateConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorError
from src.connectors.climate.world_bank_climate import WorldBankClimateConnector


@pytest.fixture
def connector():
    """Create connector with mocked settings."""
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return WorldBankClimateConnector()


@pytest.fixture
def sample_api_response():
    """Sample World Bank Indicators API response ([metadata, data])."""
    return [
        {"page": 1, "pages": 1, "per_page": 500, "total": 3},
        [
            {
                "indicator": {
                    "id": "EG.USE.PCAP.KG.OE",
                    "value": "Energy use (kg of oil "
                    "equivalent per capita)",
                },
                "country": {"id": "WLD", "value": "World"},
                "date": "2022",
                "value": 4.35,
            },
            {
                "indicator": {
                    "id": "EG.USE.PCAP.KG.OE",
                    "value": "Energy use (kg of oil "
                    "equivalent per capita)",
                },
                "country": {"id": "WLD", "value": "World"},
                "date": "2021",
                "value": 4.28,
            },
            {
                "indicator": {
                    "id": "EG.USE.PCAP.KG.OE",
                    "value": "Energy use (kg of oil "
                    "equivalent per capita)",
                },
                "country": {"id": "WLD", "value": "World"},
                "date": "2020",
                "value": 3.98,
            },
        ],
    ]


@pytest.fixture
def sample_normalized_input():
    """Pre-processed input dict as returned by fetch()."""
    return {
        "data": [
            {
                "indicator": {"id": "EG.USE.PCAP.KG.OE"},
                "country": {"id": "WLD"},
                "date": "2022",
                "value": 4.35,
            },
            {
                "indicator": {"id": "EG.USE.PCAP.KG.OE"},
                "country": {"id": "WLD"},
                "date": "2021",
                "value": 4.28,
            },
        ],
        "country": "WLD",
        "indicator": "EG.USE.PCAP.KG.OE",
    }


class TestWorldBankClimateConnectorProperties:
    def test_name(self, connector):
        assert connector.name == "world_bank_climate"

    def test_domain(self, connector):
        assert connector.domain == "climate"


class TestWorldBankClimateFetch:
    @patch("src.connectors.climate.world_bank_climate.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_api_response):
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = sample_api_response

        result = connector.fetch(country="WLD", indicator="EG.USE.PCAP.KG.OE")

        assert result["country"] == "WLD"
        assert result["indicator"] == "EG.USE.PCAP.KG.OE"
        assert "data" in result
        assert len(result["data"]) == 3

    @patch("src.connectors.climate.world_bank_climate.requests.get")
    def test_fetch_default_params(self, mock_get, connector, sample_api_response):
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = sample_api_response

        result = connector.fetch()

        assert result["country"] == "WLD"
        assert result["indicator"] == "EG.USE.PCAP.KG.OE"

    @patch("src.connectors.climate.world_bank_climate.requests.get")
    def test_fetch_uses_indicator_alias(self, mock_get, connector, sample_api_response):
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = sample_api_response

        result = connector.fetch(indicator="energy_use_per_capita")

        assert result["indicator"] == "EG.USE.PCAP.KG.OE"

    @patch("src.connectors.climate.world_bank_climate.requests.get")
    def test_fetch_api_error(self, mock_get, connector):
        from requests.exceptions import HTTPError

        mock_get.return_value.raise_for_status.side_effect = HTTPError("404")

        with pytest.raises(ConnectorError, match="API request failed"):
            connector.fetch()

    @patch("src.connectors.climate.world_bank_climate.requests.get")
    def test_fetch_invalid_json(self, mock_get, connector):
        from requests.exceptions import JSONDecodeError

        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.side_effect = JSONDecodeError(
            "Expecting value", "doc", 0
        )

        with pytest.raises(ConnectorError, match="invalid JSON"):
            connector.fetch()

    @patch("src.connectors.climate.world_bank_climate.requests.get")
    def test_fetch_unexpected_structure(self, mock_get, connector):
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = {"error": "bad request"}

        with pytest.raises(ConnectorError, match="unexpected response structure"):
            connector.fetch()


class TestWorldBankClimateNormalize:
    def test_normalize_success(self, connector, sample_normalized_input):
        df = connector.normalize(sample_normalized_input)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert df["timestamp"].dtype.kind == "M"
        assert len(df) == 2
        assert "country" in df.columns
        assert "variable" in df.columns
        assert df["country"].iloc[0] == "WLD"
        assert df["variable"].iloc[0] == "EG.USE.PCAP.KG.OE"

    def test_normalize_skips_null_values(self, connector):
        raw_data = {
            "data": [
                {
                    "indicator": {"id": "EG.USE.PCAP.KG.OE"},
                    "country": {"id": "WLD"},
                    "date": "2022",
                    "value": 4.35,
                },
                {
                    "indicator": {"id": "EG.USE.PCAP.KG.OE"},
                    "country": {"id": "WLD"},
                    "date": "2021",
                    "value": None,
                },
            ],
            "country": "WLD",
            "indicator": "EG.USE.PCAP.KG.OE",
        }
        df = connector.normalize(raw_data)
        assert len(df) == 1
        assert df["value"].iloc[0] == 4.35

    def test_normalize_not_dict(self, connector):
        with pytest.raises(ConnectorError, match="expected dict"):
            connector.normalize("not a dict")

    def test_normalize_empty_data(self, connector):
        with pytest.raises(ConnectorError, match="empty data"):
            connector.normalize({"data": [], "country": "WLD", "indicator": "X"})

    def test_normalize_missing_data_key(self, connector):
        with pytest.raises(ConnectorError, match="empty data"):
            connector.normalize({"country": "WLD", "indicator": "X"})

    def test_normalize_all_null_values(self, connector):
        raw_data = {
            "data": [
                {
                    "indicator": {"id": "EG.USE.PCAP.KG.OE"},
                    "country": {"id": "WLD"},
                    "date": "2022",
                    "value": None,
                },
            ],
            "country": "WLD",
            "indicator": "EG.USE.PCAP.KG.OE",
        }
        with pytest.raises(ConnectorError, match="could not extract any records"):
            connector.normalize(raw_data)
