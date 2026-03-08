"""Unit tests for GBIFConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.agriculture.gbif import GBIFConnector
from src.connectors.base import ConnectorError


@pytest.fixture
def connector():
    """Create a GBIFConnector with mocked settings."""
    with patch("src.connectors.base.get_settings") as mock_settings, \
         patch("src.connectors.base.get_logger") as mock_logger:
        mock_settings.return_value = MagicMock()
        mock_logger.return_value = MagicMock()
        return GBIFConnector()


@pytest.fixture
def sample_response():
    """Sample GBIF occurrence search response."""
    return {
        "offset": 0,
        "limit": 300,
        "count": 2,
        "results": [
            {
                "eventDate": "2024-03-15T10:30:00",
                "species": "Oryza sativa",
                "scientificName": "Oryza sativa L.",
                "country": "TW",
                "decimalLatitude": 24.1477,
                "decimalLongitude": 120.6736,
                "datasetName": "Taiwan Biodiversity Dataset",
            },
            {
                "year": 2023,
                "species": "Zea mays",
                "scientificName": "Zea mays L.",
                "country": "US",
                "decimalLatitude": 41.8781,
                "decimalLongitude": -87.6298,
                "datasetName": "iNaturalist observations",
            },
        ],
    }


class TestGBIFProperties:
    def test_name(self, connector):
        assert connector.name == "gbif"

    def test_domain(self, connector):
        assert connector.domain == "agriculture"


class TestGBIFFetch:
    @patch("src.connectors.agriculture.gbif.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = connector.fetch(country="TW")

        assert result == sample_response
        mock_get.assert_called_once()

    @patch("src.connectors.agriculture.gbif.requests.get")
    def test_fetch_params(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        connector.fetch(country="US", limit=100, offset=50, taxon_key=12345, year="2023")

        params = mock_get.call_args[1]["params"]
        assert params["country"] == "US"
        assert params["limit"] == 100
        assert params["offset"] == 50
        assert params["taxonKey"] == 12345
        assert params["year"] == "2023"
        assert params["hasCoordinate"] is True

    @patch("src.connectors.agriculture.gbif.requests.get")
    def test_fetch_limit_cap(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        connector.fetch(limit=999)

        params = mock_get.call_args[1]["params"]
        assert params["limit"] == 300

    @patch("src.connectors.agriculture.gbif.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Connection reset")

        with pytest.raises(ConnectorError, match="GBIF API request failed"):
            connector.fetch()

    @patch("src.connectors.agriculture.gbif.requests.get")
    def test_fetch_non_dict_response(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = "not a dict"
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="unexpected format"):
            connector.fetch()


class TestGBIFNormalize:
    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "timestamp" in df.columns
        assert "species" in df.columns
        assert "country" in df.columns
        assert "latitude" in df.columns
        assert "longitude" in df.columns
        assert "dataset" in df.columns
        assert df["timestamp"].dtype .kind == "M"

    def test_normalize_event_date_parsed(self, connector, sample_response):
        df = connector.normalize(sample_response)
        assert df["timestamp"].iloc[0] == pd.Timestamp("2024-03-15T10:30:00")

    def test_normalize_year_only_becomes_jan_first(self, connector, sample_response):
        df = connector.normalize(sample_response)
        assert df["timestamp"].iloc[1] == pd.Timestamp("2023-01-01")

    def test_normalize_falls_back_to_scientific_name(self, connector):
        raw = {
            "results": [
                {
                    "year": 2024,
                    "scientificName": "Triticum aestivum L.",
                    "country": "FR",
                    "decimalLatitude": 48.8566,
                    "decimalLongitude": 2.3522,
                    "datasetName": "French Flora",
                },
            ]
        }
        df = connector.normalize(raw)
        assert df["species"].iloc[0] == "Triticum aestivum L."

    def test_normalize_non_dict(self, connector):
        with pytest.raises(ConnectorError, match="Expected dict"):
            connector.normalize([1, 2])

    def test_normalize_missing_results_key(self, connector):
        with pytest.raises(ConnectorError, match="Missing 'results' key"):
            connector.normalize({"count": 0})

    def test_normalize_empty_results(self, connector):
        with pytest.raises(ConnectorError, match="no occurrence records"):
            connector.normalize({"results": []})

    def test_normalize_skips_records_without_date(self, connector):
        raw = {
            "results": [
                {"species": "Oryza sativa", "country": "TW"},
                {
                    "year": 2024, "species": "Zea mays",
                    "country": "US",
                    "decimalLatitude": 40.0,
                    "decimalLongitude": -90.0,
                    "datasetName": "Test",
                },
            ]
        }
        df = connector.normalize(raw)
        assert len(df) == 1

    def test_normalize_all_records_without_date(self, connector):
        raw = {
            "results": [
                {"species": "Oryza sativa", "country": "TW"},
            ]
        }
        with pytest.raises(ConnectorError, match="No valid occurrence records"):
            connector.normalize(raw)

    def test_normalize_invalid_event_date_falls_back_to_year(self, connector):
        raw = {
            "results": [
                {
                    "eventDate": "not-a-date",
                    "year": 2022,
                    "species": "Glycine max",
                    "country": "BR",
                    "decimalLatitude": -15.0,
                    "decimalLongitude": -47.0,
                    "datasetName": "Brazil Dataset",
                },
            ]
        }
        df = connector.normalize(raw)
        assert df["timestamp"].iloc[0] == pd.Timestamp("2022-01-01")
