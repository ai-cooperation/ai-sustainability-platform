"""Tests for EPAEnvirofactsConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.environment.epa_envirofacts import EPAEnvirofactsConnector


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings"):
        return EPAEnvirofactsConnector()


@pytest.fixture
def sample_response():
    return [
        {
            "FACILITY_NAME": "Plant A",
            "SECTOR": "Power Plants",
            "GHG_QUANTITY": 50000.0,
            "REPORTING_YEAR": 2023,
        },
        {
            "FACILITY_NAME": "Plant B",
            "SECTOR": "Refineries",
            "GHG_QUANTITY": 30000.0,
            "REPORTING_YEAR": 2023,
        },
    ]


class TestEPAEnvirofactsConnector:
    def test_name(self, connector):
        assert connector.name == "epa_envirofacts"

    def test_domain(self, connector):
        assert connector.domain == "environment"

    @patch("src.connectors.environment.epa_envirofacts.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch(table="GHG_EMITTER_SECTOR")

        assert isinstance(result, list)
        assert len(result) == 2
        mock_get.assert_called_once()

    @patch("src.connectors.environment.epa_envirofacts.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Timeout")

        with pytest.raises(ConnectorError, match="API request failed"):
            connector.fetch()

    @patch("src.connectors.environment.epa_envirofacts.requests.get")
    def test_fetch_non_list_response(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": "not found"}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="expected list response"):
            connector.fetch()

    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        assert len(df) == 2

    def test_normalize_with_year_column(self, connector, sample_response):
        df = connector.normalize(sample_response)

        # REPORTING_YEAR should be detected and used for timestamp
        assert df["timestamp"].iloc[0].year == 2023

    def test_normalize_without_year_column(self, connector):
        data = [{"facility": "A", "value": 100}]
        df = connector.normalize(data)

        assert "timestamp" in df.columns
        assert len(df) == 1

    def test_normalize_empty_data(self, connector):
        with pytest.raises(ConnectorError, match="empty response"):
            connector.normalize([])
