"""Tests for NRELAltFuelConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.transport.nrel_alt_fuel import NRELAltFuelConnector

SAMPLE_RESPONSE = {
    "alt_fuel_stations": [
        {
            "id": 1001,
            "station_name": "Downtown EV Station",
            "latitude": 34.0522,
            "longitude": -118.2437,
            "fuel_type_code": "ELEC",
            "city": "Los Angeles",
            "state": "CA",
            "access_code": "public",
        },
        {
            "id": 1002,
            "station_name": "Airport Hydrogen Hub",
            "latitude": 33.9425,
            "longitude": -118.4081,
            "fuel_type_code": "HY",
            "city": "El Segundo",
            "state": "CA",
            "access_code": "public",
        },
    ],
    "total_results": 2,
    "station_locator_url": "https://afdc.energy.gov/stations",
}


class TestNRELAltFuelConnector:
    def _make_connector(self) -> NRELAltFuelConnector:
        with patch("src.connectors.base.get_settings") as mock_settings:
            settings = MagicMock()
            settings.nrel_api_key = "test-nrel-key"
            settings.cache_dir = MagicMock()
            mock_settings.return_value = settings
            return NRELAltFuelConnector()

    def test_name(self):
        conn = self._make_connector()
        assert conn.name == "nrel_alt_fuel"

    def test_domain(self):
        conn = self._make_connector()
        assert conn.domain == "transport"

    @patch("src.connectors.transport.nrel_alt_fuel.requests.get")
    def test_fetch_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        conn = self._make_connector()
        result = conn.fetch(fuel_type="ELEC", state="CA", limit=10)

        assert isinstance(result, dict)
        assert "alt_fuel_stations" in result
        mock_get.assert_called_once()
        call_params = mock_get.call_args[1]["params"]
        assert call_params["api_key"] == "test-nrel-key"
        assert call_params["fuel_type"] == "ELEC"
        assert call_params["state"] == "CA"
        assert call_params["limit"] == 10

    @patch("src.connectors.transport.nrel_alt_fuel.requests.get")
    def test_fetch_missing_api_key(self, mock_get):
        conn = self._make_connector()
        conn._settings.nrel_api_key = ""

        with pytest.raises(ConnectorError, match="NREL API key is required"):
            conn.fetch()

    @patch("src.connectors.transport.nrel_alt_fuel.requests.get")
    def test_fetch_http_error(self, mock_get):
        mock_get.side_effect = requests.RequestException("Timeout")

        conn = self._make_connector()
        with pytest.raises(ConnectorError, match="NREL Alt Fuel API request failed"):
            conn.fetch()

    @patch("src.connectors.transport.nrel_alt_fuel.requests.get")
    def test_fetch_unexpected_format(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [1, 2, 3]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        conn = self._make_connector()
        with pytest.raises(ConnectorError, match="expected a dict"):
            conn.fetch()

    @patch("src.connectors.transport.nrel_alt_fuel.requests.get")
    def test_fetch_default_params(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = SAMPLE_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        conn = self._make_connector()
        conn.fetch()

        call_params = mock_get.call_args[1]["params"]
        assert call_params["fuel_type"] == "ELEC"
        assert call_params["state"] == "CA"
        assert call_params["limit"] == 200

    def test_normalize_success(self):
        conn = self._make_connector()
        df = conn.normalize(SAMPLE_RESPONSE)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

        expected_cols = {
            "id", "station_name", "latitude", "longitude",
            "fuel_type", "city", "state", "access_code", "timestamp",
        }
        assert set(df.columns) == expected_cols

        assert df.iloc[0]["id"] == 1001
        assert df.iloc[0]["station_name"] == "Downtown EV Station"
        assert df.iloc[0]["latitude"] == 34.0522
        assert df.iloc[0]["fuel_type"] == "ELEC"
        assert df.iloc[0]["city"] == "Los Angeles"
        assert df.iloc[0]["state"] == "CA"
        assert df.iloc[0]["access_code"] == "public"

    def test_normalize_has_timestamp(self):
        conn = self._make_connector()
        df = conn.normalize(SAMPLE_RESPONSE)

        assert "timestamp" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_normalize_invalid_input(self):
        conn = self._make_connector()
        with pytest.raises(ConnectorError, match="Expected dict"):
            conn.normalize([1, 2, 3])

    def test_normalize_missing_stations_key(self):
        conn = self._make_connector()
        with pytest.raises(ConnectorError, match="Missing 'alt_fuel_stations'"):
            conn.normalize({"total_results": 0})

    def test_normalize_empty_stations(self):
        conn = self._make_connector()
        df = conn.normalize({"alt_fuel_stations": []})
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_health_check_params(self):
        conn = self._make_connector()
        params = conn._health_check_params()
        assert params["limit"] == 1
        assert params["fuel_type"] == "ELEC"
