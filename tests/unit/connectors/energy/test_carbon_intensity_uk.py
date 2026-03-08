"""Tests for CarbonIntensityUKConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorError
from src.connectors.energy.carbon_intensity_uk import CarbonIntensityUKConnector


@pytest.fixture
def connector():
    with patch("src.utils.config.get_settings") as mock_s:
        mock_s.return_value = MagicMock()
        return CarbonIntensityUKConnector()


@pytest.fixture
def sample_current_response():
    return {
        "data": [
            {
                "from": "2024-01-01T00:00Z",
                "to": "2024-01-01T00:30Z",
                "intensity": {
                    "forecast": 180,
                    "actual": 175,
                    "index": "moderate",
                },
            }
        ]
    }


@pytest.fixture
def sample_regional_response():
    return {
        "data": [
            {
                "from": "2024-01-01T00:00Z",
                "to": "2024-01-01T00:30Z",
                "regions": [
                    {
                        "shortname": "North Scotland",
                        "intensity": {
                            "forecast": 45,
                            "actual": 40,
                            "index": "low",
                        },
                    },
                    {
                        "shortname": "South Wales",
                        "intensity": {
                            "forecast": 210,
                            "actual": 205,
                            "index": "high",
                        },
                    },
                ],
            }
        ]
    }


class TestCarbonIntensityUKConnector:
    def test_name(self, connector):
        assert connector.name == "carbon_intensity_uk"

    def test_domain(self, connector):
        assert connector.domain == "energy"

    @patch("src.connectors.energy.carbon_intensity_uk.requests.get")
    def test_fetch_current(self, mock_get, connector, sample_current_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_current_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.fetch(endpoint="current")

        assert result == sample_current_response
        call_args = mock_get.call_args
        assert "/intensity" in call_args[0][0]

    @patch("src.connectors.energy.carbon_intensity_uk.requests.get")
    def test_fetch_by_date(self, mock_get, connector, sample_current_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_current_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        connector.fetch(endpoint="date", date="2024-01-01")

        call_args = mock_get.call_args
        assert "2024-01-01" in call_args[0][0]

    def test_fetch_date_without_date_param(self, connector):
        with pytest.raises(ConnectorError, match="'date' is required"):
            connector.fetch(endpoint="date")

    @patch("src.connectors.energy.carbon_intensity_uk.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        from requests.exceptions import Timeout

        mock_get.side_effect = Timeout("Request timed out")

        with pytest.raises(ConnectorError, match="Carbon Intensity UK API request failed"):
            connector.fetch()

    def test_normalize_current(self, connector, sample_current_response):
        df = connector.normalize(sample_current_response)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "timestamp" in df.columns
        assert "intensity_forecast" in df.columns
        assert "intensity_actual" in df.columns
        assert "index" in df.columns
        assert "region" in df.columns
        assert df["intensity_forecast"].iloc[0] == 180
        assert df["region"].iloc[0] == "national"

    def test_normalize_regional(self, connector, sample_regional_response):
        df = connector.normalize(sample_regional_response)

        assert len(df) == 2
        assert "North Scotland" in df["region"].values
        assert "South Wales" in df["region"].values

    def test_normalize_empty_data(self, connector):
        with pytest.raises(ConnectorError, match="No data found"):
            connector.normalize({"data": []})

    def test_normalize_invalid_type(self, connector):
        with pytest.raises(ConnectorError, match="Expected dict"):
            connector.normalize([1, 2])

    @patch("src.connectors.energy.carbon_intensity_uk.requests.get")
    def test_run_pipeline(self, mock_get, connector, sample_current_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_current_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.run(endpoint="current")

        assert result.source == "carbon_intensity_uk"
        assert result.record_count == 1

    def test_health_check_params(self, connector):
        params = connector._health_check_params()
        assert params["endpoint"] == "current"


@pytest.mark.integration
class TestCarbonIntensityUKIntegration:
    def test_fetch_real_api(self):
        with patch("src.utils.config.get_settings") as mock_s:
            mock_s.return_value = MagicMock()
            conn = CarbonIntensityUKConnector()
            raw = conn.fetch(endpoint="current")
            df = conn.normalize(raw)
            assert not df.empty
            assert "timestamp" in df.columns
