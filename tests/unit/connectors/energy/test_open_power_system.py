"""Tests for OpenPowerSystemConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorError
from src.connectors.energy.open_power_system import OpenPowerSystemConnector


@pytest.fixture
def connector():
    with patch("src.utils.config.get_settings") as mock_s:
        mock_s.return_value = MagicMock()
        return OpenPowerSystemConnector()


@pytest.fixture
def sample_csv_text():
    header = "utc_timestamp,DE_load_actual_entsoe_transparency,DE_solar_generation_actual,DE_wind_onshore_generation_actual"
    row1 = "2024-01-01T00:00:00Z,45000,0,12000"
    row2 = "2024-01-01T01:00:00Z,44000,0,11500"
    row3 = "2024-01-01T02:00:00Z,43500,0,11800"
    return "\n".join([header, row1, row2, row3])


@pytest.fixture
def sample_raw_data(sample_csv_text):
    return {"csv_text": sample_csv_text, "country": None}


class TestOpenPowerSystemConnector:
    def test_name(self, connector):
        assert connector.name == "open_power_system"

    def test_domain(self, connector):
        assert connector.domain == "energy"

    @patch("src.connectors.energy.open_power_system.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_csv_text):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.iter_lines.return_value = iter(sample_csv_text.split("\n"))
        mock_get.return_value = mock_resp

        result = connector.fetch(nrows=10)

        assert "csv_text" in result
        assert len(result["csv_text"]) > 0

    @patch("src.connectors.energy.open_power_system.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        from requests.exceptions import ConnectionError

        mock_get.side_effect = ConnectionError("Connection refused")

        with pytest.raises(ConnectorError, match="Open Power System Data download failed"):
            connector.fetch()

    @patch("src.connectors.energy.open_power_system.requests.get")
    def test_fetch_insufficient_data(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.iter_lines.return_value = iter(["header_only"])
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="insufficient data"):
            connector.fetch()

    def test_normalize_success(self, connector, sample_raw_data):
        df = connector.normalize(sample_raw_data)

        assert isinstance(df, pd.DataFrame)
        assert "timestamp" in df.columns
        assert len(df) == 3
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_normalize_with_country_filter(self, connector, sample_csv_text):
        raw = {"csv_text": sample_csv_text, "country": "DE"}
        df = connector.normalize(raw)

        assert "timestamp" in df.columns
        assert "country" in df.columns
        assert all(df["country"] == "DE")

    def test_normalize_missing_csv_text(self, connector):
        with pytest.raises(ConnectorError, match="Expected dict with 'csv_text'"):
            connector.normalize({"no_csv": True})

    def test_normalize_invalid_type(self, connector):
        with pytest.raises(ConnectorError, match="Expected dict with 'csv_text'"):
            connector.normalize("not a dict")

    @patch("src.connectors.energy.open_power_system.requests.get")
    def test_run_pipeline(self, mock_get, connector, sample_csv_text):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.iter_lines.return_value = iter(sample_csv_text.split("\n"))
        mock_get.return_value = mock_resp

        result = connector.run(nrows=10)

        assert result.source == "open_power_system"
        assert result.record_count == 3

    def test_health_check_params(self, connector):
        params = connector._health_check_params()
        assert params["nrows"] == 5


@pytest.mark.integration
class TestOpenPowerSystemIntegration:
    def test_fetch_real_api(self):
        with patch("src.utils.config.get_settings") as mock_s:
            mock_s.return_value = MagicMock()
            conn = OpenPowerSystemConnector()
            raw = conn.fetch(nrows=10)
            df = conn.normalize(raw)
            assert not df.empty
            assert "timestamp" in df.columns
