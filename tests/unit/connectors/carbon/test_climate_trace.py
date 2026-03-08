"""Tests for ClimateTRACEConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests as requests_lib

from src.connectors.base import ConnectorError
from src.connectors.carbon.climate_trace import ClimateTRACEConnector

SAMPLE_RESPONSE_LIST = [
    {
        "year": 2020,
        "country": "USA",
        "sector": "power",
        "subsector": "electricity-generation",
        "co2": 1500000000,
        "ch4": 50000000,
        "n2o": 10000000,
        "co2e": 1600000000,
    },
    {
        "year": 2021,
        "country": "USA",
        "sector": "power",
        "subsector": "electricity-generation",
        "co2": 1450000000,
        "ch4": 48000000,
        "n2o": 9500000,
        "co2e": 1550000000,
    },
]

SAMPLE_RESPONSE_DICT = {"data": SAMPLE_RESPONSE_LIST}


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return ClimateTRACEConnector()


class TestClimateTRACEConnector:
    def test_name(self, connector: ClimateTRACEConnector):
        assert connector.name == "climate_trace"

    def test_domain(self, connector: ClimateTRACEConnector):
        assert connector.domain == "carbon"

    @patch("src.connectors.carbon.climate_trace.requests.get")
    def test_fetch_success(self, mock_get, connector: ClimateTRACEConnector):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_RESPONSE_LIST
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = connector.fetch()

        assert isinstance(result, list)
        assert len(result) == 2

    @patch("src.connectors.carbon.climate_trace.requests.get")
    def test_fetch_with_params(self, mock_get, connector: ClimateTRACEConnector):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_RESPONSE_LIST
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        connector.fetch(since=2020, to=2021, countries="USA", sectors="power")

        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["since"] == 2020
        assert params["to"] == 2021
        assert params["countries"] == "USA"
        assert params["sectors"] == "power"

    @patch("src.connectors.carbon.climate_trace.requests.get")
    def test_fetch_http_error(self, mock_get, connector: ClimateTRACEConnector):
        mock_get.side_effect = requests_lib.RequestException("API unavailable")

        with pytest.raises(ConnectorError, match="request failed"):
            connector.fetch()

    def test_normalize_list_response(self, connector: ClimateTRACEConnector):
        df = connector.normalize(SAMPLE_RESPONSE_LIST)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert "country" in df.columns
        assert "co2e" in df.columns
        assert len(df) == 2
        assert df["timestamp"].dtype .kind == "M"

    def test_normalize_dict_response(self, connector: ClimateTRACEConnector):
        df = connector.normalize(SAMPLE_RESPONSE_DICT)

        assert len(df) == 2
        assert "timestamp" in df.columns

    def test_normalize_single_record_dict(self, connector: ClimateTRACEConnector):
        single = {
            "year": 2022,
            "country": "CHN",
            "sector": "industry",
            "subsector": "steel",
            "co2": 999,
            "ch4": 10,
            "n2o": 5,
            "co2e": 1020,
        }
        df = connector.normalize(single)

        assert len(df) == 1
        assert df["country"].iloc[0] == "CHN"

    def test_normalize_empty_list(self, connector: ClimateTRACEConnector):
        with pytest.raises(ConnectorError, match="No emission records"):
            connector.normalize([])

    def test_normalize_no_year_field(self, connector: ClimateTRACEConnector):
        data = [{"country": "USA", "co2": 100}]
        with pytest.raises(ConnectorError, match="No valid records"):
            connector.normalize(data)

    def test_normalize_timestamp_is_jan_1(self, connector: ClimateTRACEConnector):
        df = connector.normalize(SAMPLE_RESPONSE_LIST)

        for _, row in df.iterrows():
            ts = row["timestamp"]
            assert ts.month == 1
            assert ts.day == 1
            assert ts.year == row["year"]
