"""Unit tests for EUAgriFoodConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.agriculture.eu_agri_food import EUAgriFoodConnector
from src.connectors.base import ConnectorError


@pytest.fixture
def connector():
    """Create an EUAgriFoodConnector with mocked settings."""
    with patch("src.connectors.base.get_settings") as mock_settings, \
         patch("src.connectors.base.get_logger") as mock_logger:
        mock_settings.return_value = MagicMock()
        mock_logger.return_value = MagicMock()
        return EUAgriFoodConnector()


@pytest.fixture
def sample_eurostat_raw():
    """Sample Eurostat JSON-stat API response."""
    return {
        "value": {"0": 280000.0, "1": 275000.0, "2": 290000.0},
        "dimension": {
            "time": {
                "category": {
                    "index": {"2020": 0, "2021": 1, "2022": 2},
                }
            }
        },
        "extension": {
            "annotation": [{"title": "1000 t"}],
        },
    }


@pytest.fixture
def sample_converted_eurostat():
    """Eurostat response after _convert_eurostat_response."""
    return {
        "data": [
            {
                "year": 2020, "product": "C0000",
                "country": "EU27_2020",
                "value": 280000.0, "unit": "1000 t",
            },
            {
                "year": 2021, "product": "C0000",
                "country": "EU27_2020",
                "value": 275000.0, "unit": "1000 t",
            },
            {
                "year": 2022, "product": "C0000",
                "country": "EU27_2020",
                "value": 290000.0, "unit": "1000 t",
            },
        ],
        "source": "eurostat",
    }


@pytest.fixture
def sample_usda_fas_response():
    """Sample USDA FAS API response."""
    return [
        {
            "dataYear": 2023,
            "commodityDescription": "Wheat",
            "countryDescription": "United States",
            "quantity": 1500000.0,
            "unitDescription": "Metric Tons",
        },
    ]


@pytest.fixture
def sample_response_with_date():
    """Legacy-style response with date field (for normalize backward compat)."""
    return {
        "data": [
            {
                "date": "2024-03-15",
                "product": "Common wheat",
                "memberState": "FR",
                "price": 215.50,
                "unit": "EUR/t",
            },
            {
                "date": "2024-03-15",
                "product": "Barley",
                "memberState": "DE",
                "price": 198.75,
                "unit": "EUR/t",
            },
        ]
    }


class TestEUAgriFoodProperties:
    def test_name(self, connector):
        assert connector.name == "eu_agri_food"

    def test_domain(self, connector):
        assert connector.domain == "agriculture"


class TestEUAgriFoodFetch:
    @patch("src.connectors.agriculture.eu_agri_food.requests.get")
    def test_fetch_eurostat_success(self, mock_get, connector, sample_eurostat_raw):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_eurostat_raw
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.fetch()

        assert result["source"] == "eurostat"
        assert len(result["data"]) == 3
        assert result["data"][0]["year"] == 2020
        mock_get.assert_called_once()

    @patch("src.connectors.agriculture.eu_agri_food.requests.get")
    def test_fetch_falls_back_to_usda(self, mock_get, connector, sample_usda_fas_response):
        # First call (Eurostat) fails, second call (USDA) succeeds
        eurostat_exc = requests.RequestException("503 Service Unavailable")
        usda_resp = MagicMock()
        usda_resp.json.return_value = sample_usda_fas_response
        usda_resp.raise_for_status.return_value = None

        mock_get.side_effect = [eurostat_exc, usda_resp]

        result = connector.fetch()

        assert result["source"] == "usda_fas"
        assert len(result["data"]) == 1
        assert result["data"][0]["product"] == "Wheat"

    @patch("src.connectors.agriculture.eu_agri_food.requests.get")
    def test_fetch_both_fail(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Network error")

        with pytest.raises(ConnectorError, match="USDA FAS API request failed"):
            connector.fetch()

    @patch("src.connectors.agriculture.eu_agri_food.requests.get")
    def test_fetch_passes_eurostat_params(self, mock_get, connector, sample_eurostat_raw):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_eurostat_raw
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        connector.fetch(dataset="apro_cpsh1", geo="DE", crops="C1100")

        call_args = mock_get.call_args
        assert "apro_cpsh1" in call_args[0][0]
        params = call_args[1]["params"]
        assert params["geo"] == "DE"
        assert params["crops"] == "C1100"


class TestEUAgriFoodNormalize:
    def test_normalize_with_year_field(self, connector, sample_converted_eurostat):
        df = connector.normalize(sample_converted_eurostat)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "timestamp" in df.columns
        assert df["timestamp"].dtype.kind == "M"
        assert df["timestamp"].iloc[0] == pd.Timestamp("2020-01-01")

    def test_normalize_with_date_field(self, connector, sample_response_with_date):
        df = connector.normalize(sample_response_with_date)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "product" in df.columns
        assert "country" in df.columns
        assert "price" in df.columns
        assert "unit" in df.columns
        assert df["timestamp"].iloc[0] == pd.Timestamp("2024-03-15")

    def test_normalize_list_format(self, connector):
        raw = [
            {
                "date": "2024-01-10",
                "product": "Skim milk powder",
                "memberState": "IE",
                "price": 2450.0,
                "unit": "EUR/t",
            },
        ]
        df = connector.normalize(raw)
        assert len(df) == 1
        assert df["product"].iloc[0] == "Skim milk powder"

    def test_normalize_empty_records(self, connector):
        with pytest.raises(ConnectorError, match="no records"):
            connector.normalize({"data": []})

    def test_normalize_unexpected_type(self, connector):
        with pytest.raises(ConnectorError, match="unexpected format"):
            connector.normalize(42)

    def test_normalize_skips_records_without_date_or_year(self, connector):
        raw = {
            "data": [
                {"product": "Wheat", "memberState": "FR", "price": 200.0},
                {
                    "date": "2024-01-01",
                    "product": "Barley",
                    "memberState": "DE",
                    "price": 190.0,
                    "unit": "EUR/t",
                },
            ]
        }
        df = connector.normalize(raw)
        assert len(df) == 1

    def test_normalize_all_records_invalid(self, connector):
        raw = {
            "data": [
                {"product": "Wheat", "memberState": "FR"},
            ]
        }
        with pytest.raises(ConnectorError, match="No valid records"):
            connector.normalize(raw)
