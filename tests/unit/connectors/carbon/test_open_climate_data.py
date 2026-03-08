"""Tests for OpenClimateDataConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests as requests_lib

from src.connectors.base import ConnectorError
from src.connectors.carbon.open_climate_data import OpenClimateDataConnector


SAMPLE_CSV = (
    "Year,Country,Emissions,Category\n"
    "2018,USA,5100.5,Fossil\n"
    "2019,USA,5000.3,Fossil\n"
    "2020,CHN,12700.1,Fossil\n"
)

SAMPLE_CSV_NO_YEAR = (
    "Country,Emissions,Category\n"
    "USA,5100.5,Fossil\n"
)


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return OpenClimateDataConnector()


class TestOpenClimateDataConnector:
    def test_name(self, connector: OpenClimateDataConnector):
        assert connector.name == "open_climate_data"

    def test_domain(self, connector: OpenClimateDataConnector):
        assert connector.domain == "carbon"

    @patch("src.connectors.carbon.open_climate_data.requests.get")
    def test_fetch_default_dataset(
        self, mock_get, connector: OpenClimateDataConnector
    ):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_CSV
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = connector.fetch()

        assert "csv_text" in result
        assert result["dataset"] == "global-carbon-budget"

    @patch("src.connectors.carbon.open_climate_data.requests.get")
    def test_fetch_specific_dataset(
        self, mock_get, connector: OpenClimateDataConnector
    ):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_CSV
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = connector.fetch(dataset="national-climate-plans")

        assert result["dataset"] == "national-climate-plans"

    def test_fetch_unknown_dataset(self, connector: OpenClimateDataConnector):
        with pytest.raises(ConnectorError, match="Unknown dataset"):
            connector.fetch(dataset="nonexistent")

    @patch("src.connectors.carbon.open_climate_data.requests.get")
    def test_fetch_custom_url(
        self, mock_get, connector: OpenClimateDataConnector
    ):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_CSV
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = connector.fetch(url="https://example.com/data.csv")

        assert "csv_text" in result
        mock_get.assert_called_once_with(
            "https://example.com/data.csv", timeout=60
        )

    @patch("src.connectors.carbon.open_climate_data.requests.get")
    def test_fetch_http_error(
        self, mock_get, connector: OpenClimateDataConnector
    ):
        mock_get.side_effect = requests_lib.RequestException("Network error")

        with pytest.raises(ConnectorError, match="download failed"):
            connector.fetch()

    def test_normalize_success(self, connector: OpenClimateDataConnector):
        raw_data = {
            "csv_text": SAMPLE_CSV,
            "dataset": "global-carbon-budget",
            "url": "https://example.com",
        }
        df = connector.normalize(raw_data)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert len(df) == 3
        assert df["timestamp"].dtype .kind == "M"

    def test_normalize_year_column_case_insensitive(
        self, connector: OpenClimateDataConnector
    ):
        csv_lower = "year,country,emissions\n2020,USA,5000\n"
        raw_data = {"csv_text": csv_lower, "dataset": "test", "url": ""}
        df = connector.normalize(raw_data)

        assert df["timestamp"].iloc[0].year == 2020

    def test_normalize_no_year_column(self, connector: OpenClimateDataConnector):
        raw_data = {
            "csv_text": SAMPLE_CSV_NO_YEAR,
            "dataset": "test",
            "url": "",
        }
        df = connector.normalize(raw_data)

        # Should fallback to 1970-01-01
        assert "timestamp" in df.columns
        assert len(df) == 1

    def test_normalize_invalid_input(self, connector: OpenClimateDataConnector):
        with pytest.raises(ConnectorError, match="Expected dict"):
            connector.normalize("not a dict")

    def test_normalize_empty_csv(self, connector: OpenClimateDataConnector):
        raw_data = {"csv_text": "Year,Country\n", "dataset": "test", "url": ""}
        with pytest.raises(ConnectorError, match="no data rows"):
            connector.normalize(raw_data)
