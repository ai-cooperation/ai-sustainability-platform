"""Tests for EmissionsAPIConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.environment.emissions_api import EmissionsAPIConnector


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings"):
        return EmissionsAPIConnector()


@pytest.fixture
def sample_response():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [10.5, 52.3],
                },
                "properties": {
                    "time_start": "2026-01-15T00:00:00Z",
                    "product": "carbonmonoxide",
                    "value": 0.035,
                },
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [11.2, 53.1],
                },
                "properties": {
                    "time_start": "2026-01-15T01:00:00Z",
                    "product": "carbonmonoxide",
                    "value": 0.042,
                },
            },
        ],
    }


class TestEmissionsAPIConnector:
    def test_name(self, connector):
        assert connector.name == "emissions_api"

    def test_domain(self, connector):
        assert connector.domain == "environment"

    @patch("src.connectors.environment.emissions_api.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch(product="carbonmonoxide")

        assert "features" in result
        assert len(result["features"]) == 2

    @patch("src.connectors.environment.emissions_api.requests.get")
    def test_fetch_invalid_product(self, mock_get, connector):
        with pytest.raises(ConnectorError, match="invalid product"):
            connector.fetch(product="invalid_gas")

    @patch("src.connectors.environment.emissions_api.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Timeout")

        with pytest.raises(ConnectorError, match="API request failed"):
            connector.fetch(product="ozone")

    @patch("src.connectors.environment.emissions_api.requests.get")
    def test_fetch_missing_features(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"type": "FeatureCollection"}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="missing 'features' key"):
            connector.fetch(product="carbonmonoxide")

    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        assert len(df) == 2
        assert set(df.columns) == {
            "timestamp", "latitude", "longitude", "product", "value",
        }

    def test_normalize_coordinates(self, connector, sample_response):
        df = connector.normalize(sample_response)

        # GeoJSON uses [lon, lat] order
        assert df["longitude"].iloc[0] == 10.5
        assert df["latitude"].iloc[0] == 52.3

    def test_normalize_empty_features(self, connector):
        with pytest.raises(ConnectorError, match="no features"):
            connector.normalize({"features": []})
