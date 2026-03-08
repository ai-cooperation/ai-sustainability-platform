"""Tests for ElectricityMapsConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorError
from src.connectors.energy.electricity_maps import ElectricityMapsConnector


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_s:
        mock_settings = MagicMock()
        mock_settings.electricity_maps_api_key = "test-api-key"
        mock_s.return_value = mock_settings
        yield ElectricityMapsConnector()


@pytest.fixture
def connector_no_key():
    with patch("src.connectors.base.get_settings") as mock_s:
        mock_settings = MagicMock()
        mock_settings.electricity_maps_api_key = ""
        mock_s.return_value = mock_settings
        yield ElectricityMapsConnector()


@pytest.fixture
def sample_response():
    return {
        "zone": "DE",
        "carbonIntensity": 350,
        "datetime": "2024-01-01T12:00:00.000Z",
        "updatedAt": "2024-01-01T12:05:00.000Z",
        "fossilFuelPercentage": 42.5,
    }


@pytest.fixture
def sample_history_response():
    return [
        {
            "zone": "DE",
            "carbonIntensity": 350,
            "datetime": "2024-01-01T00:00:00.000Z",
            "fossilFuelPercentage": 42.5,
        },
        {
            "zone": "DE",
            "carbonIntensity": 320,
            "datetime": "2024-01-01T01:00:00.000Z",
            "fossilFuelPercentage": 38.0,
        },
    ]


class TestElectricityMapsConnector:
    def test_name(self, connector):
        assert connector.name == "electricity_maps"

    def test_domain(self, connector):
        assert connector.domain == "energy"

    def test_fetch_no_api_key(self, connector_no_key):
        with pytest.raises(ConnectorError, match="Electricity Maps API key not configured"):
            connector_no_key.fetch()

    @patch("src.connectors.energy.electricity_maps.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.fetch(zone="DE")

        assert result == sample_response
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert call_kwargs[1]["headers"]["auth-token"] == "test-api-key"

    @patch("src.connectors.energy.electricity_maps.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        from requests.exceptions import HTTPError

        mock_get.side_effect = HTTPError("403 Forbidden")

        with pytest.raises(ConnectorError, match="Electricity Maps API request failed"):
            connector.fetch()

    def test_normalize_single_item(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "timestamp" in df.columns
        assert "zone" in df.columns
        assert "carbon_intensity" in df.columns
        assert "fossil_fuel_percentage" in df.columns
        assert df["carbon_intensity"].iloc[0] == 350
        assert df["zone"].iloc[0] == "DE"

    def test_normalize_list(self, connector, sample_history_response):
        df = connector.normalize(sample_history_response)

        assert len(df) == 2
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_normalize_invalid_type(self, connector):
        with pytest.raises(ConnectorError, match="Unexpected response format"):
            connector.normalize(42)

    @patch("src.connectors.energy.electricity_maps.requests.get")
    def test_run_pipeline(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.run(zone="DE")

        assert result.source == "electricity_maps"
        assert result.record_count == 1

    def test_health_check_params(self, connector):
        params = connector._health_check_params()
        assert params["zone"] == "DE"
        assert params["endpoint"] == "latest"


@pytest.mark.integration
class TestElectricityMapsIntegration:
    def test_fetch_real_api(self):
        """Requires ELECTRICITY_MAPS_API_KEY environment variable."""
        import os

        key = os.environ.get("ELECTRICITY_MAPS_API_KEY", "")
        if not key:
            pytest.skip("ELECTRICITY_MAPS_API_KEY not set")
        with patch("src.connectors.base.get_settings") as mock_s:
            settings = MagicMock()
            settings.electricity_maps_api_key = key
            mock_s.return_value = settings
            conn = ElectricityMapsConnector()
            raw = conn.fetch(zone="DE")
            df = conn.normalize(raw)
            assert not df.empty
