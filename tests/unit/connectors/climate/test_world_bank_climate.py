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
def sample_response():
    """Sample World Bank Climate API response (annual average format)."""
    return {
        "data": [
            {
                "scenario": "historical",
                "fromYear": 1980,
                "toYear": 1999,
                "monthVals": [15.2, 16.1, 18.5, 22.3, 25.8, 28.1,
                              29.5, 29.2, 27.6, 24.1, 20.3, 16.8],
            },
            {
                "scenario": "rcp45",
                "fromYear": 2020,
                "toYear": 2039,
                "annualVal": 24.5,
            },
        ],
        "var": "tas",
        "aggregation": "mavg",
        "country_iso": "TWN",
    }


class TestWorldBankClimateConnectorProperties:
    def test_name(self, connector):
        assert connector.name == "world_bank_climate"

    def test_domain(self, connector):
        assert connector.domain == "climate"


class TestWorldBankClimateFetch:
    @patch("src.connectors.climate.world_bank_climate.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = sample_response["data"]

        result = connector.fetch(var="tas", country_iso="TWN")

        assert result["var"] == "tas"
        assert result["country_iso"] == "TWN"
        assert "data" in result

    @patch("src.connectors.climate.world_bank_climate.requests.get")
    def test_fetch_default_params(self, mock_get, connector):
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = []

        result = connector.fetch()

        assert result["var"] == "tas"
        assert result["aggregation"] == "annualavg"
        assert result["country_iso"] == "TWN"

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


class TestWorldBankClimateNormalize:
    def test_normalize_monthly_data(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert df["timestamp"].dtype .kind == "M"
        # 12 monthly values from historical + 1 annual from rcp45
        assert len(df) >= 12
        assert "country" in df.columns
        assert "variable" in df.columns
        assert df["country"].iloc[0] == "TWN"

    def test_normalize_annual_val(self, connector):
        raw_data = {
            "data": [
                {
                    "scenario": "rcp85",
                    "fromYear": 2040,
                    "toYear": 2059,
                    "annualVal": 26.3,
                },
            ],
            "var": "tas",
            "country_iso": "USA",
        }
        df = connector.normalize(raw_data)

        assert len(df) >= 1
        assert df["value"].iloc[0] == 26.3
        assert df["scenario"].iloc[0] == "rcp85"

    def test_normalize_not_dict(self, connector):
        with pytest.raises(ConnectorError, match="expected dict"):
            connector.normalize("not a dict")

    def test_normalize_empty_data(self, connector):
        with pytest.raises(ConnectorError, match="empty data"):
            connector.normalize({"data": [], "var": "tas", "country_iso": "TWN"})

    def test_normalize_missing_data_key(self, connector):
        with pytest.raises(ConnectorError, match="empty data"):
            connector.normalize({"var": "tas", "country_iso": "TWN"})
