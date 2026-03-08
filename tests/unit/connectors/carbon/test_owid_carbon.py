"""Tests for OWIDCarbonConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests as requests_lib

from src.connectors.base import ConnectorError
from src.connectors.carbon.owid_carbon import OWIDCarbonConnector

SAMPLE_CSV = (
    "country,year,co2,co2_per_capita,population,gdp,energy_per_capita\n"
    "World,2020,34.81,4.47,7794798739,84.71,74.46\n"
    "World,2021,36.29,4.63,7874965825,90.81,76.12\n"
    "Taiwan,2020,0.27,11.56,23816775,0.67,187.3\n"
    "Taiwan,2021,0.28,11.83,23855010,0.73,192.1\n"
)


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return OWIDCarbonConnector()


class TestOWIDCarbonConnector:
    def test_name(self, connector: OWIDCarbonConnector):
        assert connector.name == "owid_carbon"

    def test_domain(self, connector: OWIDCarbonConnector):
        assert connector.domain == "carbon"

    @patch("src.connectors.carbon.owid_carbon.requests.get")
    def test_fetch_success(self, mock_get, connector: OWIDCarbonConnector):
        mock_response = MagicMock()
        mock_response.text = SAMPLE_CSV
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = connector.fetch()

        assert "csv_text" in result
        assert result["csv_text"] == SAMPLE_CSV
        mock_get.assert_called_once()

    @patch("src.connectors.carbon.owid_carbon.requests.get")
    def test_fetch_http_error(self, mock_get, connector: OWIDCarbonConnector):
        mock_get.side_effect = requests_lib.RequestException("Connection refused")

        with pytest.raises(ConnectorError, match="download failed"):
            connector.fetch()

    def test_normalize_success(self, connector: OWIDCarbonConnector):
        raw_data = {"csv_text": SAMPLE_CSV, "params": {}}
        df = connector.normalize(raw_data)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert "country" in df.columns
        assert "co2" in df.columns
        assert len(df) == 4
        assert df["timestamp"].dtype .kind == "M"

    def test_normalize_with_country_filter(self, connector: OWIDCarbonConnector):
        raw_data = {"csv_text": SAMPLE_CSV, "params": {"country": "Taiwan"}}
        df = connector.normalize(raw_data)

        assert len(df) == 2
        assert all(df["country"] == "Taiwan")

    def test_normalize_with_year_filter(self, connector: OWIDCarbonConnector):
        raw_data = {
            "csv_text": SAMPLE_CSV,
            "params": {"start_year": 2021, "end_year": 2021},
        }
        df = connector.normalize(raw_data)

        assert len(df) == 2
        assert all(df["year"] == 2021)

    def test_normalize_timestamp_is_jan_1(self, connector: OWIDCarbonConnector):
        raw_data = {"csv_text": SAMPLE_CSV, "params": {}}
        df = connector.normalize(raw_data)

        for _, row in df.iterrows():
            ts = row["timestamp"]
            assert ts.month == 1
            assert ts.day == 1
            assert ts.year == row["year"]

    def test_normalize_invalid_input(self, connector: OWIDCarbonConnector):
        with pytest.raises(ConnectorError, match="Expected dict"):
            connector.normalize("not a dict")

    def test_normalize_no_columns(self, connector: OWIDCarbonConnector):
        raw_data = {"csv_text": "foo,bar\n1,2\n", "params": {}}
        with pytest.raises(ConnectorError, match="No expected columns"):
            connector.normalize(raw_data)

    def test_normalize_missing_year_column(self, connector: OWIDCarbonConnector):
        raw_data = {"csv_text": "country,co2\nWorld,34.81\n", "params": {}}
        with pytest.raises(ConnectorError, match="Missing 'year' column"):
            connector.normalize(raw_data)
