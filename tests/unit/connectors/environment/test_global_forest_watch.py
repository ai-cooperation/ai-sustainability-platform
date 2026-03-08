"""Tests for GlobalForestWatchConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.environment.global_forest_watch import (
    GlobalForestWatchConnector,
)


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings_instance = MagicMock()
        settings_instance.global_forest_watch_api_key = "test-gfw-key"
        mock_settings.return_value = settings_instance
        return GlobalForestWatchConnector()


@pytest.fixture
def sample_response():
    return {
        "data": [
            {
                "year": 2020,
                "iso": "BRA",
                "tree_cover_loss_ha": 1500000.0,
                "co2_emissions": 750000000.0,
            },
            {
                "year": 2021,
                "iso": "BRA",
                "tree_cover_loss_ha": 1400000.0,
                "co2_emissions": 700000000.0,
            },
            {
                "year": 2022,
                "iso": "BRA",
                "tree_cover_loss_ha": 1300000.0,
                "co2_emissions": 650000000.0,
            },
        ],
    }


class TestGlobalForestWatchConnector:
    def test_name(self, connector):
        assert connector.name == "global_forest_watch"

    def test_domain(self, connector):
        assert connector.domain == "environment"

    def test_missing_api_key(self):
        with patch("src.connectors.base.get_settings") as mock_settings:
            settings_instance = MagicMock()
            settings_instance.global_forest_watch_api_key = ""
            mock_settings.return_value = settings_instance
            conn = GlobalForestWatchConnector()

            with pytest.raises(
                ConnectorError, match="GLOBAL_FOREST_WATCH_API_KEY not configured"
            ):
                conn.fetch()

    @patch("src.connectors.environment.global_forest_watch.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch(dataset="umd_tree_cover_loss")

        assert "data" in result
        # Verify API key header
        call_kwargs = mock_get.call_args
        assert call_kwargs[1]["headers"]["x-api-key"] == "test-gfw-key"

    @patch("src.connectors.environment.global_forest_watch.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Server error")

        with pytest.raises(ConnectorError, match="API request failed"):
            connector.fetch()

    @patch("src.connectors.environment.global_forest_watch.requests.get")
    def test_fetch_non_dict_response(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = "not a dict"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="unexpected response format"):
            connector.fetch()

    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        assert len(df) == 3
        assert "year" in df.columns
        assert "country" in df.columns
        assert "tree_cover_loss_ha" in df.columns

    def test_normalize_values(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert df["year"].iloc[0] == 2020
        assert df["country"].iloc[0] == "BRA"
        assert df["tree_cover_loss_ha"].iloc[0] == 1500000.0
        assert df["timestamp"].iloc[0].year == 2020

    def test_normalize_empty_data(self, connector):
        with pytest.raises(ConnectorError, match="no data"):
            connector.normalize({"data": []})

    def test_normalize_single_record(self, connector):
        raw = {
            "data": {
                "year": 2023,
                "iso": "IDN",
                "area_ha": 500000.0,
                "emissions": 200000000.0,
            },
        }
        df = connector.normalize(raw)

        assert len(df) == 1
        assert df["country"].iloc[0] == "IDN"
