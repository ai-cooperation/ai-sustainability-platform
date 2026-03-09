"""Tests for CopernicusCDSConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorError
from src.connectors.climate.copernicus_cds import CopernicusCDSConnector


@pytest.fixture
def connector():
    """Create connector with mocked settings including CDS key."""
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings = MagicMock()
        settings.copernicus_cds_key = "12345:abcdef-ghijkl"
        mock_settings.return_value = settings
        return CopernicusCDSConnector()


@pytest.fixture
def connector_no_key():
    """Create connector without CDS key."""
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings = MagicMock()
        settings.copernicus_cds_key = ""
        mock_settings.return_value = settings
        return CopernicusCDSConnector()


class TestCopernicusCDSConnectorProperties:
    def test_name(self, connector):
        assert connector.name == "copernicus_cds"

    def test_domain(self, connector):
        assert connector.domain == "climate"


class TestCopernicusCDSFetch:
    @patch("src.connectors.climate.copernicus_cds.CopernicusCDSConnector._get_client")
    def test_fetch_success(self, mock_get_client, connector):
        mock_client = MagicMock()
        mock_client.retrieve.return_value = "result-object"
        mock_get_client.return_value = mock_client

        result = connector.fetch(
            dataset="reanalysis-era5-single-levels-monthly-means",
            year=["2023"],
            month=["01"],
        )

        assert "result" in result
        assert result["dataset"] == "reanalysis-era5-single-levels-monthly-means"
        mock_client.retrieve.assert_called_once()

    @patch("src.connectors.climate.copernicus_cds.CopernicusCDSConnector._get_client")
    def test_fetch_default_params(self, mock_get_client, connector):
        mock_client = MagicMock()
        mock_client.retrieve.return_value = "result-object"
        mock_get_client.return_value = mock_client

        result = connector.fetch()

        assert result["dataset"] == "reanalysis-era5-single-levels-monthly-means"
        call_args = mock_client.retrieve.call_args
        request_body = call_args[0][1]
        assert request_body["variable"] == "2m_temperature"
        assert len(request_body["month"]) == 12

    @patch("src.connectors.climate.copernicus_cds.CopernicusCDSConnector._get_client")
    def test_fetch_retrieval_error(self, mock_get_client, connector):
        mock_client = MagicMock()
        mock_client.retrieve.side_effect = Exception("Queue timeout")
        mock_get_client.return_value = mock_client

        with pytest.raises(ConnectorError, match="CDS retrieval failed"):
            connector.fetch()

    def test_fetch_no_key(self, connector_no_key):
        with pytest.raises(ConnectorError):
            connector_no_key.fetch()

    def test_get_client_no_cdsapi(self, connector):
        """Test error when cdsapi is not installed."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "cdsapi":
                raise ImportError("No module named 'cdsapi'")
            return original_import(name, *args, **kwargs)

        with patch.object(builtins, "__import__", side_effect=mock_import):
            with pytest.raises(ConnectorError, match="cdsapi package is not installed"):
                connector._get_client()


class TestCopernicusCDSHealthCheck:
    @patch("src.connectors.climate.copernicus_cds.requests.get")
    def test_health_check_healthy(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        result = connector.health_check()

        assert result["status"] == "healthy"
        assert "latency_ms" in result
        assert "CDS API reachable" in result["message"]
        mock_get.assert_called_once_with(
            "https://cds.climate.copernicus.eu/api", timeout=15
        )

    @patch("src.connectors.climate.copernicus_cds.requests.get")
    def test_health_check_degraded(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_get.return_value = mock_resp

        result = connector.health_check()

        assert result["status"] == "degraded"
        assert "503" in result["message"]

    @patch("src.connectors.climate.copernicus_cds.requests.get")
    def test_health_check_down(self, mock_get, connector):
        import requests

        mock_get.side_effect = requests.ConnectionError("Connection refused")

        result = connector.health_check()

        assert result["status"] == "down"
        assert "Connection refused" in result["message"]

    @patch("src.connectors.climate.copernicus_cds.requests.get")
    def test_health_check_does_not_require_cdsapi(self, mock_get, connector):
        """Health check should work even without cdsapi installed."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        # Should NOT raise ImportError for cdsapi
        result = connector.health_check()
        assert result["status"] == "healthy"


class TestCopernicusCDSNormalize:
    def test_normalize_success(self, connector):
        raw_data = {
            "result": "result-object",
            "dataset": "reanalysis-era5-single-levels-monthly-means",
            "request": {
                "variable": "2m_temperature",
                "year": ["2023"],
                "month": ["01", "02", "03"],
                "time": "00:00",
                "format": "netcdf",
            },
        }

        df = connector.normalize(raw_data)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert df["timestamp"].dtype .kind == "M"
        assert len(df) == 3
        assert list(df.columns) == ["timestamp", "dataset", "variable", "status"]
        assert df["variable"].iloc[0] == "2m_temperature"
        assert df["status"].iloc[0] == "retrieved"

    def test_normalize_multiple_years(self, connector):
        raw_data = {
            "result": "result-object",
            "dataset": "era5",
            "request": {
                "variable": "precipitation",
                "year": ["2022", "2023"],
                "month": ["01", "06"],
            },
        }

        df = connector.normalize(raw_data)

        assert len(df) == 4  # 2 years * 2 months

    def test_normalize_single_string_year_month(self, connector):
        raw_data = {
            "result": "result-object",
            "dataset": "era5",
            "request": {
                "variable": "temperature",
                "year": "2023",
                "month": "06",
            },
        }

        df = connector.normalize(raw_data)
        assert len(df) == 1

    def test_normalize_not_dict(self, connector):
        with pytest.raises(ConnectorError, match="expected dict"):
            connector.normalize("not a dict")

    def test_normalize_empty_request(self, connector):
        raw_data = {
            "result": "result",
            "dataset": "era5",
            "request": {"variable": "temp", "year": [], "month": []},
        }
        with pytest.raises(ConnectorError, match="could not build records"):
            connector.normalize(raw_data)
