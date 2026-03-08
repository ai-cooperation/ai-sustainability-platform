"""Tests for NOAACDOConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorError
from src.connectors.climate.noaa_cdo import NOAACDOConnector


@pytest.fixture
def connector():
    """Create connector with mocked settings including a token."""
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings = MagicMock()
        settings.noaa_cdo_token = "test-token-abc123"
        mock_settings.return_value = settings
        return NOAACDOConnector()


@pytest.fixture
def connector_no_token():
    """Create connector without API token."""
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings = MagicMock()
        settings.noaa_cdo_token = ""
        mock_settings.return_value = settings
        return NOAACDOConnector()


@pytest.fixture
def sample_response():
    """Sample NOAA CDO API response."""
    return {
        "metadata": {
            "resultset": {"offset": 1, "count": 3, "limit": 1000}
        },
        "results": [
            {
                "date": "2024-01-01T00:00:00",
                "datatype": "TMAX",
                "station": "GHCND:USW00013722",
                "value": 122,
            },
            {
                "date": "2024-01-01T00:00:00",
                "datatype": "TMIN",
                "station": "GHCND:USW00013722",
                "value": 44,
            },
            {
                "date": "2024-01-01T00:00:00",
                "datatype": "PRCP",
                "station": "GHCND:USW00013722",
                "value": 0,
            },
        ],
    }


class TestNOAACDOConnectorProperties:
    def test_name(self, connector):
        assert connector.name == "noaa_cdo"

    def test_domain(self, connector):
        assert connector.domain == "climate"


class TestNOAACDOFetch:
    @patch("src.connectors.climate.noaa_cdo.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = sample_response

        result = connector.fetch(
            startdate="2024-01-01",
            enddate="2024-01-02",
        )

        assert result == sample_response
        call_kwargs = mock_get.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert headers["token"] == "test-token-abc123"

    @patch("src.connectors.climate.noaa_cdo.requests.get")
    def test_fetch_with_optional_params(self, mock_get, connector, sample_response):
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.return_value = sample_response

        connector.fetch(
            startdate="2024-01-01",
            enddate="2024-01-31",
            locationid="FIPS:37",
            datatypeid="TMAX",
        )

        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["locationid"] == "FIPS:37"
        assert params["datatypeid"] == "TMAX"

    def test_fetch_missing_dates(self, connector):
        with pytest.raises(ConnectorError, match="startdate.*enddate.*required"):
            connector.fetch()

    def test_fetch_no_token(self, connector_no_token):
        with pytest.raises(ConnectorError, match="token not configured"):
            connector_no_token.fetch(startdate="2024-01-01", enddate="2024-01-02")

    @patch("src.connectors.climate.noaa_cdo.requests.get")
    def test_fetch_api_error(self, mock_get, connector):
        from requests.exceptions import HTTPError

        mock_get.return_value.raise_for_status.side_effect = HTTPError("401 Unauthorized")

        with pytest.raises(ConnectorError, match="API request failed"):
            connector.fetch(startdate="2024-01-01", enddate="2024-01-02")


class TestNOAACDONormalize:
    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert df["timestamp"].dtype .kind == "M"
        assert len(df) == 3
        assert list(df.columns) == ["timestamp", "station", "datatype", "value"]
        assert df["station"].iloc[0] == "GHCND:USW00013722"
        assert df["datatype"].iloc[0] == "TMAX"

    def test_normalize_not_dict(self, connector):
        with pytest.raises(ConnectorError, match="expected dict"):
            connector.normalize([1, 2, 3])

    def test_normalize_no_results(self, connector):
        with pytest.raises(ConnectorError, match="no results"):
            connector.normalize({"metadata": {}, "results": []})

    def test_normalize_missing_results_key(self, connector):
        with pytest.raises(ConnectorError, match="no results"):
            connector.normalize({"metadata": {}})
