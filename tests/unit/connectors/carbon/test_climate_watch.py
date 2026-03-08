"""Tests for ClimateWatchConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests as requests_lib

from src.connectors.base import ConnectorError
from src.connectors.carbon.climate_watch import ClimateWatchConnector

SAMPLE_RESPONSE = {
    "data": [
        {
            "country": "USA",
            "sector": "Total including LUCF",
            "gas": "All GHG",
            "emissions": [
                {"year": 2019, "value": 5769.23},
                {"year": 2020, "value": 5222.41},
            ],
        },
        {
            "country": "CHN",
            "sector": "Total including LUCF",
            "gas": "All GHG",
            "emissions": [
                {"year": 2019, "value": 12705.67},
                {"year": 2020, "value": 13013.89},
            ],
        },
    ]
}


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return ClimateWatchConnector()


class TestClimateWatchConnector:
    def test_name(self, connector: ClimateWatchConnector):
        assert connector.name == "climate_watch"

    def test_domain(self, connector: ClimateWatchConnector):
        assert connector.domain == "carbon"

    @patch("src.connectors.carbon.climate_watch.requests.get")
    def test_fetch_success(self, mock_get, connector: ClimateWatchConnector):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = connector.fetch()

        assert isinstance(result, dict)
        assert "data" in result
        mock_get.assert_called_once()

    @patch("src.connectors.carbon.climate_watch.requests.get")
    def test_fetch_with_params(self, mock_get, connector: ClimateWatchConnector):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        connector.fetch(source="CAIT", gas="CO2", regions="USA")

        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["source"] == "CAIT"
        assert params["gas"] == "CO2"
        assert params["regions"] == "USA"

    @patch("src.connectors.carbon.climate_watch.requests.get")
    def test_fetch_http_error(self, mock_get, connector: ClimateWatchConnector):
        mock_get.side_effect = requests_lib.RequestException("Timeout")

        with pytest.raises(ConnectorError, match="request failed"):
            connector.fetch()

    def test_normalize_success(self, connector: ClimateWatchConnector):
        df = connector.normalize(SAMPLE_RESPONSE)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert "country" in df.columns
        assert "value" in df.columns
        assert len(df) == 4
        assert df["timestamp"].dtype .kind == "M"

    def test_normalize_countries(self, connector: ClimateWatchConnector):
        df = connector.normalize(SAMPLE_RESPONSE)

        countries = df["country"].unique()
        assert "USA" in countries
        assert "CHN" in countries

    def test_normalize_invalid_input(self, connector: ClimateWatchConnector):
        with pytest.raises(ConnectorError, match="Expected dict"):
            connector.normalize([1, 2, 3])

    def test_normalize_empty_data(self, connector: ClimateWatchConnector):
        with pytest.raises(ConnectorError, match="No 'data' entries"):
            connector.normalize({"data": []})

    def test_normalize_no_emissions(self, connector: ClimateWatchConnector):
        data = {
            "data": [
                {
                    "country": "USA",
                    "sector": "Total",
                    "gas": "All GHG",
                    "emissions": [],
                }
            ]
        }
        with pytest.raises(ConnectorError, match="No emission records"):
            connector.normalize(data)

    def test_normalize_timestamp_is_jan_1(self, connector: ClimateWatchConnector):
        df = connector.normalize(SAMPLE_RESPONSE)

        for _, row in df.iterrows():
            ts = row["timestamp"]
            assert ts.month == 1
            assert ts.day == 1
