"""Tests for EIAConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorError
from src.connectors.energy.eia import EIAConnector


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_s = MagicMock()
        mock_s.eia_api_key = "test-api-key"
        mock_settings.return_value = mock_s
        yield EIAConnector()


@pytest.fixture
def connector_no_key():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_s = MagicMock()
        mock_s.eia_api_key = ""
        mock_settings.return_value = mock_s
        yield EIAConnector()


@pytest.fixture
def sample_response():
    return {
        "response": {
            "total": 3,
            "data": [
                {
                    "period": "2024-01-01T00",
                    "respondent": "US48",
                    "fueltype": "SUN",
                    "value": 1234,
                },
                {
                    "period": "2024-01-01T01",
                    "respondent": "US48",
                    "fueltype": "SUN",
                    "value": 2345,
                },
                {
                    "period": "2024-01-01T02",
                    "respondent": "US48",
                    "fueltype": "SUN",
                    "value": 3456,
                },
            ],
        }
    }


class TestEIAConnector:
    def test_name(self, connector):
        assert connector.name == "eia"

    def test_domain(self, connector):
        assert connector.domain == "energy"

    def test_fetch_no_api_key(self, connector_no_key):
        with pytest.raises(ConnectorError, match="EIA API key not configured"):
            connector_no_key.fetch()

    @patch("src.connectors.energy.eia.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.fetch()

        assert result == sample_response
        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert "api_key" in call_kwargs[1]["params"]

    @patch("src.connectors.energy.eia.requests.get")
    def test_fetch_api_error_in_body(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "response": {"error": "Invalid API key"}
        }
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="EIA API error"):
            connector.fetch()

    @patch("src.connectors.energy.eia.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        from requests.exceptions import HTTPError

        mock_get.side_effect = HTTPError("500 Server Error")

        with pytest.raises(ConnectorError, match="EIA API request failed"):
            connector.fetch()

    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert "period" in df.columns
        assert len(df) == 3
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_normalize_no_data(self, connector):
        with pytest.raises(ConnectorError, match="No data records"):
            connector.normalize({"response": {"data": []}})

    def test_normalize_missing_period(self, connector):
        raw = {"response": {"data": [{"value": 1}]}}
        with pytest.raises(ConnectorError, match="Missing 'period' column"):
            connector.normalize(raw)

    def test_normalize_invalid_type(self, connector):
        with pytest.raises(ConnectorError, match="Expected dict"):
            connector.normalize("string")

    @patch("src.connectors.energy.eia.requests.get")
    def test_run_pipeline(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.run()

        assert result.source == "eia"
        assert result.record_count == 3

    def test_health_check_params(self, connector):
        params = connector._health_check_params()
        assert params["length"] == 1


@pytest.mark.integration
class TestEIAIntegration:
    def test_fetch_real_api(self):
        """Requires EIA_API_KEY environment variable."""
        with patch("src.connectors.base.get_settings") as mock_s:
            import os

            key = os.environ.get("EIA_API_KEY", "")
            if not key:
                pytest.skip("EIA_API_KEY not set")
            settings = MagicMock()
            settings.eia_api_key = key
            mock_s.return_value = settings
            conn = EIAConnector()
            raw = conn.fetch(length=5)
            df = conn.normalize(raw)
            assert not df.empty
