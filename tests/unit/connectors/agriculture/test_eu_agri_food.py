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
def sample_response_with_date():
    """Sample EU Agri-Food response with date field."""
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


@pytest.fixture
def sample_response_with_year():
    """Sample EU Agri-Food response with year-only field."""
    return {
        "data": [
            {
                "year": 2023,
                "productName": "Butter",
                "country": "NL",
                "value": 5100.0,
                "priceUnit": "EUR/100kg",
            },
        ]
    }


@pytest.fixture
def sample_response_as_list():
    """Sample EU Agri-Food response as a plain list."""
    return [
        {
            "date": "2024-01-10",
            "product": "Skim milk powder",
            "memberState": "IE",
            "price": 2450.0,
            "unit": "EUR/t",
        },
    ]


class TestEUAgriFoodProperties:
    def test_name(self, connector):
        assert connector.name == "eu_agri_food"

    def test_domain(self, connector):
        assert connector.domain == "agriculture"


class TestEUAgriFoodFetch:
    @patch("src.connectors.agriculture.eu_agri_food.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response_with_date):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response_with_date
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.fetch(dataset="cereals-prices")

        assert result == sample_response_with_date
        mock_get.assert_called_once()

    @patch("src.connectors.agriculture.eu_agri_food.requests.get")
    def test_fetch_with_filters(self, mock_get, connector, sample_response_with_date):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response_with_date
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        connector.fetch(
            dataset="dairy-prices",
            member_state="FR",
            product="Butter",
            year="2024",
        )

        params = mock_get.call_args[1]["params"]
        assert params["memberState"] == "FR"
        assert params["product"] == "Butter"
        assert params["year"] == "2024"

    @patch("src.connectors.agriculture.eu_agri_food.requests.get")
    def test_fetch_default_dataset(self, mock_get, connector, sample_response_with_date):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response_with_date
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        connector.fetch()

        url = mock_get.call_args[0][0]
        assert url.endswith("/cereals-prices")

    @patch("src.connectors.agriculture.eu_agri_food.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Timeout")

        with pytest.raises(ConnectorError, match="EU Agri-Food API request failed"):
            connector.fetch()


class TestEUAgriFoodNormalize:
    def test_normalize_with_date_field(self, connector, sample_response_with_date):
        df = connector.normalize(sample_response_with_date)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "timestamp" in df.columns
        assert "product" in df.columns
        assert "country" in df.columns
        assert "price" in df.columns
        assert "unit" in df.columns
        assert df["timestamp"].dtype .kind == "M"
        assert df["timestamp"].iloc[0] == pd.Timestamp("2024-03-15")

    def test_normalize_with_year_field(self, connector, sample_response_with_year):
        df = connector.normalize(sample_response_with_year)

        assert len(df) == 1
        assert df["timestamp"].iloc[0] == pd.Timestamp("2023-01-01")
        assert df["product"].iloc[0] == "Butter"

    def test_normalize_list_format(self, connector, sample_response_as_list):
        df = connector.normalize(sample_response_as_list)

        assert len(df) == 1
        assert df["product"].iloc[0] == "Skim milk powder"

    def test_normalize_empty_records(self, connector):
        with pytest.raises(ConnectorError, match="no records"):
            connector.normalize({"data": []})

    def test_normalize_unexpected_type(self, connector):
        with pytest.raises(ConnectorError, match="unexpected format"):
            connector.normalize(42)

    def test_normalize_uses_begin_date_fallback(self, connector):
        raw = {
            "data": [
                {
                    "beginDate": "2024-06-01",
                    "product": "Maize",
                    "memberState": "IT",
                    "price": 180.0,
                    "unit": "EUR/t",
                },
            ]
        }
        df = connector.normalize(raw)
        assert df["timestamp"].iloc[0] == pd.Timestamp("2024-06-01")

    def test_normalize_skips_records_without_date_or_year(self, connector):
        raw = {
            "data": [
                {"product": "Wheat", "memberState": "FR", "price": 200.0},
                {"date": "2024-01-01", "product": "Barley", "memberState": "DE", "price": 190.0, "unit": "EUR/t"},
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
