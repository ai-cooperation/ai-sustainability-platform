"""Tests for OpenChargeMapConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.transport.open_charge_map import OpenChargeMapConnector

SAMPLE_RESPONSE = [
    {
        "ID": 12345,
        "AddressInfo": {
            "Title": "City Hall Charging Station",
            "Latitude": 34.0522,
            "Longitude": -118.2437,
            "Country": {"Title": "United States"},
        },
        "Connections": [
            {
                "PowerKW": 50.0,
                "ConnectionType": {"Title": "CCS (Type 1)"},
            }
        ],
        "OperatorInfo": {"Title": "ChargePoint"},
    },
    {
        "ID": 67890,
        "AddressInfo": {
            "Title": "Mall Parking EV Charger",
            "Latitude": 37.7749,
            "Longitude": -122.4194,
            "Country": {"Title": "United States"},
        },
        "Connections": [],
        "OperatorInfo": None,
    },
]


class TestOpenChargeMapConnector:
    def _make_connector(self) -> OpenChargeMapConnector:
        with patch("src.connectors.base.get_settings") as mock_settings:
            settings = MagicMock()
            settings.open_charge_map_api_key = ""
            settings.cache_dir = MagicMock()
            mock_settings.return_value = settings
            return OpenChargeMapConnector()

    def test_name(self):
        conn = self._make_connector()
        assert conn.name == "open_charge_map"

    def test_domain(self):
        conn = self._make_connector()
        assert conn.domain == "transport"

    @patch("src.connectors.transport.open_charge_map.requests.get")
    def test_fetch_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        conn = self._make_connector()
        result = conn.fetch(countrycode="US", maxresults=10)

        assert isinstance(result, list)
        assert len(result) == 2
        mock_get.assert_called_once()
        call_params = mock_get.call_args[1]["params"]
        assert call_params["countrycode"] == "US"
        assert call_params["maxresults"] == 10
        assert call_params["output"] == "json"

    @patch("src.connectors.transport.open_charge_map.requests.get")
    def test_fetch_with_api_key(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        conn = self._make_connector()
        conn._settings.open_charge_map_api_key = "test-key-123"
        conn.fetch()

        call_headers = mock_get.call_args[1]["headers"]
        assert call_headers["X-API-Key"] == "test-key-123"
        call_params = mock_get.call_args[1]["params"]
        assert "key" not in call_params

    @patch("src.connectors.transport.open_charge_map.requests.get")
    def test_fetch_without_api_key(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        conn = self._make_connector()
        conn._settings.open_charge_map_api_key = ""
        conn.fetch()

        call_headers = mock_get.call_args[1]["headers"]
        assert "X-API-Key" not in call_headers
        call_params = mock_get.call_args[1]["params"]
        assert "key" not in call_params

    @patch("src.connectors.transport.open_charge_map.requests.get")
    def test_fetch_http_error(self, mock_get):
        mock_get.side_effect = requests.RequestException("Connection refused")

        conn = self._make_connector()
        with pytest.raises(ConnectorError, match="OpenChargeMap API request failed"):
            conn.fetch()

    @patch("src.connectors.transport.open_charge_map.requests.get")
    def test_fetch_unexpected_format(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "bad request"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        conn = self._make_connector()
        with pytest.raises(ConnectorError, match="expected a list"):
            conn.fetch()

    def test_normalize_success(self):
        conn = self._make_connector()
        df = conn.normalize(SAMPLE_RESPONSE)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

        expected_cols = {
            "id", "title", "latitude", "longitude", "country",
            "power_kw", "connector_type", "operator", "timestamp",
        }
        assert set(df.columns) == expected_cols

        assert df.iloc[0]["id"] == 12345
        assert df.iloc[0]["title"] == "City Hall Charging Station"
        assert df.iloc[0]["latitude"] == 34.0522
        assert df.iloc[0]["power_kw"] == 50.0
        assert df.iloc[0]["connector_type"] == "CCS (Type 1)"
        assert df.iloc[0]["operator"] == "ChargePoint"
        assert df.iloc[0]["country"] == "United States"

    def test_normalize_missing_connections(self):
        conn = self._make_connector()
        df = conn.normalize(SAMPLE_RESPONSE)

        assert pd.isna(df.iloc[1]["power_kw"])
        assert pd.isna(df.iloc[1]["connector_type"]) or df.iloc[1]["connector_type"] is None
        assert df.iloc[1]["operator"] == ""

    def test_normalize_has_timestamp(self):
        conn = self._make_connector()
        df = conn.normalize(SAMPLE_RESPONSE)

        assert "timestamp" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_normalize_invalid_input(self):
        conn = self._make_connector()
        with pytest.raises(ConnectorError, match="Expected list"):
            conn.normalize({"not": "a list"})

    def test_normalize_empty_list(self):
        conn = self._make_connector()
        df = conn.normalize([])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_health_check_params(self):
        conn = self._make_connector()
        params = conn._health_check_params()
        assert params["maxresults"] == 1
