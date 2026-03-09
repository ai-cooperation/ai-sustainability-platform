"""Tests for NASAPowerConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorError
from src.connectors.energy.nasa_power import NASAPowerConnector


@pytest.fixture
def connector():
    with patch("src.utils.config.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return NASAPowerConnector()


@pytest.fixture
def sample_response():
    return {
        "geometry": {"type": "Point", "coordinates": [121.57, 25.03]},
        "properties": {
            "parameter": {
                "ALLSKY_SFC_SW_DWN": {
                    "20240101": 1.23,
                    "20240102": 2.34,
                    "20240103": 3.45,
                },
                "T2M": {
                    "20240101": 5.0,
                    "20240102": 6.1,
                    "20240103": 4.8,
                },
            }
        },
    }


class TestNASAPowerConnector:
    def test_name(self, connector):
        assert connector.name == "nasa_power"

    def test_domain(self, connector):
        assert connector.domain == "energy"

    @patch("src.connectors.energy.nasa_power.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.fetch(
            latitude=25.03, longitude=121.57, start="20240101", end="20240103"
        )

        assert result == sample_response
        mock_get.assert_called_once()

    @patch("src.connectors.energy.nasa_power.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        from requests.exceptions import ConnectionError

        mock_get.side_effect = ConnectionError("Connection refused")

        with pytest.raises(ConnectorError, match="NASA POWER API request failed"):
            connector.fetch()

    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert "solar_radiation" in df.columns
        assert "temperature" in df.columns
        assert "latitude" in df.columns
        assert "longitude" in df.columns
        assert len(df) == 3
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        assert df["solar_radiation"].iloc[0] == 1.23

    def test_normalize_missing_data(self, connector):
        raw = {"properties": {"parameter": {}}, "geometry": {"coordinates": [0, 0]}}
        with pytest.raises(ConnectorError, match="No parameter data"):
            connector.normalize(raw)

    def test_normalize_invalid_type(self, connector):
        with pytest.raises(ConnectorError, match="Expected dict"):
            connector.normalize("not a dict")

    @patch("src.connectors.energy.nasa_power.requests.get")
    def test_run_pipeline(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.run(
            latitude=25.03, longitude=121.57, start="20240101", end="20240103"
        )

        assert result.source == "nasa_power"
        assert result.record_count == 3

    def test_health_check_params(self, connector):
        params = connector._health_check_params()
        assert params["start"] == "20240101"
        assert params["end"] == "20240101"


@pytest.mark.integration
class TestNASAPowerIntegration:
    def test_fetch_real_api(self):
        with patch("src.utils.config.get_settings") as mock_s:
            mock_s.return_value = MagicMock()
            conn = NASAPowerConnector()
            raw = conn.fetch(
                latitude=25.03, longitude=121.57, start="20240101", end="20240103"
            )
            df = conn.normalize(raw)
            assert not df.empty
            assert "timestamp" in df.columns
