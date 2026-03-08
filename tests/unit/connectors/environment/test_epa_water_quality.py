"""Tests for EPAWaterQualityConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.environment.epa_water_quality import (
    EPAWaterQualityConnector,
)


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings"):
        return EPAWaterQualityConnector()


@pytest.fixture
def sample_csv():
    return (
        "ActivityStartDate,MonitoringLocationIdentifier,"
        "CharacteristicName,ResultMeasureValue,"
        "ResultMeasure/MeasureUnitCode\n"
        "2026-01-15,USGS-01234,Dissolved oxygen,8.5,mg/l\n"
        "2026-01-16,USGS-01234,Dissolved oxygen,7.9,mg/l\n"
        "2026-01-17,USGS-05678,Dissolved oxygen,9.1,mg/l\n"
    )


class TestEPAWaterQualityConnector:
    def test_name(self, connector):
        assert connector.name == "epa_water_quality"

    def test_domain(self, connector):
        assert connector.domain == "environment"

    @patch("src.connectors.environment.epa_water_quality.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_csv):
        mock_resp = MagicMock()
        mock_resp.text = sample_csv
        mock_resp.headers = {"Content-Type": "text/csv"}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch(statecode="US:06")

        assert "csv_text" in result
        assert "Dissolved oxygen" in result["csv_text"]

    @patch("src.connectors.environment.epa_water_quality.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Server error")

        with pytest.raises(ConnectorError, match="API request failed"):
            connector.fetch()

    @patch("src.connectors.environment.epa_water_quality.requests.get")
    def test_fetch_wrong_content_type(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.text = "<html>Error</html>"
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="expected CSV response"):
            connector.fetch()

    def test_normalize_success(self, connector, sample_csv):
        raw = {"csv_text": sample_csv}
        df = connector.normalize(raw)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert "station" in df.columns
        assert "parameter" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns
        assert len(df) == 3
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_normalize_empty_csv(self, connector):
        with pytest.raises(ConnectorError, match="empty CSV"):
            connector.normalize({"csv_text": ""})

    def test_normalize_values(self, connector, sample_csv):
        raw = {"csv_text": sample_csv}
        df = connector.normalize(raw)

        assert df["station"].iloc[0] == "USGS-01234"
        assert df["parameter"].iloc[0] == "Dissolved oxygen"
        assert df["unit"].iloc[0] == "mg/l"
