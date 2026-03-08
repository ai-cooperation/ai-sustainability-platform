"""Tests for OpenMeteoClimateConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorError
from src.connectors.climate.open_meteo_climate import OpenMeteoClimateConnector


@pytest.fixture
def connector():
    """Create connector with mocked settings."""
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return OpenMeteoClimateConnector()


@pytest.fixture
def sample_response():
    """Sample Open-Meteo climate API response."""
    return {
        "latitude": 25.0,
        "longitude": 121.5,
        "daily": {
            "time": ["2030-01-01", "2030-01-02", "2030-01-03"],
            "temperature_2m_max": [22.5, 23.1, 21.8],
            "temperature_2m_min": [14.2, 15.0, 13.9],
            "precipitation_sum": [0.0, 2.5, 0.1],
        },
    }


class TestOpenMeteoClimateConnectorProperties:
    def test_name(self, connector):
        assert connector.name == "open_meteo_climate"

    def test_domain(self, connector):
        assert connector.domain == "climate"


class TestOpenMeteoClimateFetch:
    @patch("src.connectors.climate.open_meteo_climate.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value=sample_response),
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = connector.fetch(latitude=25.03, longitude=121.57)
        assert result == sample_response

    @patch("src.connectors.climate.open_meteo_climate.requests.get")
    def test_fetch_custom_params(self, mock_get, connector, sample_response):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value=sample_response),
        )
        mock_get.return_value.raise_for_status = MagicMock()

        connector.fetch(
            latitude=40.0,
            longitude=-74.0,
            start_date="2030-01-01",
            end_date="2030-12-31",
            models="MPI_ESM1_2_HR",
        )

        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["models"] == "MPI_ESM1_2_HR"
        assert params["start_date"] == "2030-01-01"

    @patch("src.connectors.climate.open_meteo_climate.requests.get")
    def test_fetch_api_error(self, mock_get, connector):
        from requests.exceptions import HTTPError

        mock_get.return_value.raise_for_status.side_effect = HTTPError("500")

        with pytest.raises(ConnectorError, match="API request failed"):
            connector.fetch()

    @patch("src.connectors.climate.open_meteo_climate.requests.get")
    def test_fetch_timeout(self, mock_get, connector):
        from requests.exceptions import Timeout

        mock_get.side_effect = Timeout("Request timed out")

        with pytest.raises(ConnectorError, match="API request failed"):
            connector.fetch()


class TestOpenMeteoClimateNormalize:
    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert df["timestamp"].dtype .kind == "M"
        assert len(df) == 3
        assert list(df.columns) == [
            "timestamp", "lat", "lon",
            "temperature_max", "temperature_min", "precipitation",
        ]
        assert df["temperature_max"].iloc[0] == 22.5
        assert df["temperature_min"].iloc[1] == 15.0

    def test_normalize_not_dict(self, connector):
        with pytest.raises(ConnectorError, match="expected dict"):
            connector.normalize("not a dict")

    def test_normalize_missing_daily(self, connector):
        with pytest.raises(ConnectorError, match="missing 'daily'"):
            connector.normalize({"latitude": 25.0})

    def test_normalize_empty_time(self, connector):
        raw = {"daily": {"time": []}, "latitude": 25.0, "longitude": 121.5}
        with pytest.raises(ConnectorError, match="no time values"):
            connector.normalize(raw)
