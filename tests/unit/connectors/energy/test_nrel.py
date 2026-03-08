"""Tests for NRELConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorError
from src.connectors.energy.nrel import NRELConnector


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_s:
        mock_settings = MagicMock()
        mock_settings.nrel_api_key = "test-api-key"
        mock_s.return_value = mock_settings
        yield NRELConnector()


@pytest.fixture
def connector_no_key():
    with patch("src.connectors.base.get_settings") as mock_s:
        mock_settings = MagicMock()
        mock_settings.nrel_api_key = ""
        mock_s.return_value = mock_settings
        yield NRELConnector()


@pytest.fixture
def sample_response():
    return {
        "inputs": {"lat": 40.0, "lon": -105.0},
        "outputs": {
            "avg_ghi": {
                "jan": 2.5, "feb": 3.2, "mar": 4.1, "apr": 5.0,
                "may": 6.0, "jun": 6.5, "jul": 6.8, "aug": 6.2,
                "sep": 5.3, "oct": 4.0, "nov": 2.8, "dec": 2.3,
                "annual": 4.56,
            },
            "avg_dni": {
                "jan": 3.0, "feb": 3.8, "mar": 4.5, "apr": 5.2,
                "may": 5.8, "jun": 6.1, "jul": 6.5, "aug": 6.0,
                "sep": 5.5, "oct": 4.5, "nov": 3.3, "dec": 2.8,
                "annual": 4.75,
            },
        },
    }


class TestNRELConnector:
    def test_name(self, connector):
        assert connector.name == "nrel"

    def test_domain(self, connector):
        assert connector.domain == "energy"

    def test_fetch_no_api_key(self, connector_no_key):
        with pytest.raises(ConnectorError, match="NREL API key not configured"):
            connector_no_key.fetch()

    @patch("src.connectors.energy.nrel.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.fetch(latitude=40.0, longitude=-105.0)

        assert result == sample_response
        mock_get.assert_called_once()

    @patch("src.connectors.energy.nrel.requests.get")
    def test_fetch_api_error_in_body(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"errors": ["Invalid API key"]}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="NREL API error"):
            connector.fetch()

    @patch("src.connectors.energy.nrel.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        from requests.exceptions import Timeout

        mock_get.side_effect = Timeout("Request timed out")

        with pytest.raises(ConnectorError, match="NREL API request failed"):
            connector.fetch()

    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert "latitude" in df.columns
        assert "longitude" in df.columns
        assert "ghi" in df.columns
        assert "dni" in df.columns
        assert "wind_speed" in df.columns
        assert len(df) == 12  # 12 months
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        assert df["latitude"].iloc[0] == 40.0
        assert df["ghi"].iloc[0] == 2.5  # January

    def test_normalize_no_outputs(self, connector):
        with pytest.raises(ConnectorError, match="No outputs found"):
            connector.normalize({"inputs": {}, "outputs": {}})

    def test_normalize_invalid_type(self, connector):
        with pytest.raises(ConnectorError, match="Expected dict"):
            connector.normalize([1, 2])

    @patch("src.connectors.energy.nrel.requests.get")
    def test_run_pipeline(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.run(latitude=40.0, longitude=-105.0)

        assert result.source == "nrel"
        assert result.record_count == 12

    def test_health_check_params(self, connector):
        params = connector._health_check_params()
        assert params["latitude"] == 40.0
        assert params["longitude"] == -105.0


@pytest.mark.integration
class TestNRELIntegration:
    def test_fetch_real_api(self):
        """Requires NREL_API_KEY environment variable."""
        import os

        key = os.environ.get("NREL_API_KEY", "")
        if not key:
            pytest.skip("NREL_API_KEY not set")
        with patch("src.connectors.base.get_settings") as mock_s:
            settings = MagicMock()
            settings.nrel_api_key = key
            mock_s.return_value = settings
            conn = NRELConnector()
            raw = conn.fetch(latitude=40.0, longitude=-105.0)
            df = conn.normalize(raw)
            assert not df.empty
