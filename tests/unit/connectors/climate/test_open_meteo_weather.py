"""Tests for OpenMeteoWeatherConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorError
from src.connectors.climate.open_meteo_weather import OpenMeteoWeatherConnector


@pytest.fixture
def connector():
    """Create connector with mocked settings."""
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return OpenMeteoWeatherConnector()


@pytest.fixture
def sample_response():
    """Sample Open-Meteo weather API response."""
    return {
        "latitude": 25.0,
        "longitude": 121.5,
        "hourly": {
            "time": [
                "2026-03-01T00:00",
                "2026-03-01T01:00",
                "2026-03-01T02:00",
            ],
            "temperature_2m": [18.5, 17.8, 17.2],
            "relative_humidity_2m": [72, 75, 78],
            "precipitation": [0.0, 0.1, 0.0],
            "wind_speed_10m": [5.2, 4.8, 4.5],
        },
    }


class TestOpenMeteoWeatherConnectorProperties:
    def test_name(self, connector):
        assert connector.name == "open_meteo_weather"

    def test_domain(self, connector):
        assert connector.domain == "climate"


class TestOpenMeteoWeatherFetch:
    @patch("src.connectors.climate.open_meteo_weather.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value=sample_response),
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = connector.fetch(latitude=25.03, longitude=121.57)

        assert result == sample_response
        mock_get.assert_called_once()

    @patch("src.connectors.climate.open_meteo_weather.requests.get")
    def test_fetch_uses_default_params(self, mock_get, connector, sample_response):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value=sample_response),
        )
        mock_get.return_value.raise_for_status = MagicMock()

        connector.fetch()

        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["latitude"] == 25.03
        assert params["longitude"] == 121.57

    @patch("src.connectors.climate.open_meteo_weather.requests.get")
    def test_fetch_api_error(self, mock_get, connector):
        from requests.exceptions import HTTPError

        mock_get.return_value.raise_for_status.side_effect = HTTPError("500 Server Error")

        with pytest.raises(ConnectorError, match="API request failed"):
            connector.fetch()

    @patch("src.connectors.climate.open_meteo_weather.requests.get")
    def test_fetch_connection_error(self, mock_get, connector):
        from requests.exceptions import ConnectionError

        mock_get.side_effect = ConnectionError("Connection refused")

        with pytest.raises(ConnectorError, match="API request failed"):
            connector.fetch()


class TestOpenMeteoWeatherNormalize:
    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert df["timestamp"].dtype .kind == "M"
        assert len(df) == 3
        assert list(df.columns) == [
            "timestamp", "lat", "lon", "temperature",
            "humidity", "precipitation", "wind_speed",
        ]
        assert df["temperature"].iloc[0] == 18.5
        assert df["lat"].iloc[0] == 25.0

    def test_normalize_not_dict(self, connector):
        with pytest.raises(ConnectorError, match="expected dict"):
            connector.normalize([1, 2, 3])

    def test_normalize_missing_hourly(self, connector):
        with pytest.raises(ConnectorError, match="missing 'hourly'"):
            connector.normalize({"latitude": 25.0})

    def test_normalize_empty_time(self, connector):
        raw = {"hourly": {"time": []}, "latitude": 25.0, "longitude": 121.5}
        with pytest.raises(ConnectorError, match="no time values"):
            connector.normalize(raw)
