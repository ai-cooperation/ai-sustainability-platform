"""Tests for OpenMeteoSolarConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorError
from src.connectors.energy.open_meteo_solar import OpenMeteoSolarConnector


@pytest.fixture
def connector():
    with patch("src.utils.config.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return OpenMeteoSolarConnector()


@pytest.fixture
def sample_response():
    return {
        "latitude": 25.03,
        "longitude": 121.57,
        "hourly": {
            "time": [
                "2024-01-01T00:00",
                "2024-01-01T01:00",
                "2024-01-01T02:00",
            ],
            "shortwave_radiation": [0.0, 0.0, 10.5],
            "direct_radiation": [0.0, 0.0, 5.2],
            "diffuse_radiation": [0.0, 0.0, 5.3],
        },
    }


class TestOpenMeteoSolarConnector:
    def test_name(self, connector):
        assert connector.name == "open_meteo_solar"

    def test_domain(self, connector):
        assert connector.domain == "energy"

    @patch("src.connectors.energy.open_meteo_solar.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.fetch(latitude=25.03, longitude=121.57)

        assert result == sample_response
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert call_kwargs[1]["params"]["latitude"] == 25.03

    @patch("src.connectors.energy.open_meteo_solar.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        from requests.exceptions import HTTPError

        mock_get.side_effect = HTTPError("404 Not Found")

        with pytest.raises(ConnectorError, match="Open-Meteo Solar API request failed"):
            connector.fetch()

    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert "shortwave_radiation" in df.columns
        assert "direct_radiation" in df.columns
        assert "diffuse_radiation" in df.columns
        assert "latitude" in df.columns
        assert "longitude" in df.columns
        assert len(df) == 3
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_normalize_missing_hourly(self, connector):
        with pytest.raises(ConnectorError, match="Missing 'hourly' data"):
            connector.normalize({"latitude": 0})

    def test_normalize_invalid_type(self, connector):
        with pytest.raises(ConnectorError, match="Expected dict"):
            connector.normalize([1, 2, 3])

    @patch("src.connectors.energy.open_meteo_solar.requests.get")
    def test_run_pipeline(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.run(latitude=25.03, longitude=121.57)

        assert result.source == "open_meteo_solar"
        assert result.record_count == 3

    def test_health_check_params(self, connector):
        params = connector._health_check_params()
        assert "latitude" in params
        assert "longitude" in params


@pytest.mark.integration
class TestOpenMeteoSolarIntegration:
    def test_fetch_real_api(self):
        with patch("src.utils.config.get_settings") as mock_s:
            mock_s.return_value = MagicMock()
            conn = OpenMeteoSolarConnector()
            raw = conn.fetch(latitude=25.03, longitude=121.57)
            df = conn.normalize(raw)
            assert not df.empty
            assert "timestamp" in df.columns
