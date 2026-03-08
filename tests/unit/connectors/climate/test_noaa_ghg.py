"""Tests for NOAAGHGConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorError
from src.connectors.climate.noaa_ghg import NOAAGHGConnector


@pytest.fixture
def connector():
    """Create connector with mocked settings."""
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return NOAAGHGConnector()


@pytest.fixture
def sample_csv_text():
    """Sample NOAA GHG CSV with comment headers."""
    return (
        "# CO2 data from Mauna Loa Observatory\n"
        "# Source: NOAA GML\n"
        "# Units: ppm\n"
        "#\n"
        "# Header line explaining columns\n"
        "year,month,decimal_date,average,deseasonalized,ndays,sdev,unc\n"
        "2023,1,2023.042,418.19,419.52,31,0.73,0.12\n"
        "2023,2,2023.125,419.28,419.69,28,0.52,0.10\n"
        "2023,3,2023.208,420.98,419.94,31,0.61,0.11\n"
    )


class TestNOAAGHGConnectorProperties:
    def test_name(self, connector):
        assert connector.name == "noaa_ghg"

    def test_domain(self, connector):
        assert connector.domain == "climate"


class TestNOAAGHGFetch:
    @patch("src.connectors.climate.noaa_ghg.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_csv_text):
        mock_get.return_value = MagicMock(
            status_code=200,
            text=sample_csv_text,
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = connector.fetch(dataset="mlo_co2")

        assert result["csv_text"] == sample_csv_text
        assert result["dataset"] == "mlo_co2"

    @patch("src.connectors.climate.noaa_ghg.requests.get")
    def test_fetch_default_dataset(self, mock_get, connector, sample_csv_text):
        mock_get.return_value = MagicMock(
            status_code=200,
            text=sample_csv_text,
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = connector.fetch()
        assert result["dataset"] == "mlo_co2"

    def test_fetch_unknown_dataset(self, connector):
        with pytest.raises(ConnectorError, match="unknown dataset"):
            connector.fetch(dataset="invalid_dataset")

    @patch("src.connectors.climate.noaa_ghg.requests.get")
    def test_fetch_api_error(self, mock_get, connector):
        from requests.exceptions import HTTPError

        mock_get.return_value.raise_for_status.side_effect = HTTPError("404")

        with pytest.raises(ConnectorError, match="API request failed"):
            connector.fetch()


class TestNOAAGHGNormalize:
    def test_normalize_success(self, connector, sample_csv_text):
        raw_data = {"csv_text": sample_csv_text, "dataset": "mlo_co2"}
        df = connector.normalize(raw_data)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert "co2_ppm" in df.columns
        assert "trend" in df.columns
        assert "location" in df.columns
        assert df["timestamp"].dtype .kind == "M"
        assert len(df) == 3
        assert df["location"].iloc[0] == "Mauna Loa"
        assert df["co2_ppm"].iloc[0] == 418.19

    def test_normalize_global_dataset(self, connector, sample_csv_text):
        raw_data = {"csv_text": sample_csv_text, "dataset": "gl_co2"}
        df = connector.normalize(raw_data)

        assert df["location"].iloc[0] == "Global"

    def test_normalize_skips_comment_lines(self, connector):
        csv_with_comments = (
            "# Comment 1\n"
            "# Comment 2\n"
            "year,month,decimal_date,average,deseasonalized,ndays\n"
            "2023,6,2023.458,423.78,421.50,30\n"
        )
        raw_data = {"csv_text": csv_with_comments, "dataset": "mlo_co2"}
        df = connector.normalize(raw_data)

        assert len(df) == 1
        assert df["co2_ppm"].iloc[0] == 423.78

    def test_normalize_filters_missing_values(self, connector):
        csv_text = (
            "year,month,decimal_date,average,deseasonalized,ndays\n"
            "2023,1,2023.042,418.19,419.52,31\n"
            "2023,2,2023.125,-99.99,-99.99,0\n"
        )
        raw_data = {"csv_text": csv_text, "dataset": "mlo_co2"}
        df = connector.normalize(raw_data)

        # -99.99 should be filtered out (value <= 0)
        assert len(df) == 1

    def test_normalize_not_dict(self, connector):
        with pytest.raises(ConnectorError, match="expected dict"):
            connector.normalize([1, 2, 3])

    def test_normalize_empty_csv(self, connector):
        with pytest.raises(ConnectorError, match="empty CSV"):
            connector.normalize({"csv_text": "", "dataset": "mlo_co2"})

    def test_normalize_only_comments(self, connector):
        csv_text = "# Only comments\n# No data\n"
        with pytest.raises(ConnectorError, match="no data lines"):
            connector.normalize({"csv_text": csv_text, "dataset": "mlo_co2"})
