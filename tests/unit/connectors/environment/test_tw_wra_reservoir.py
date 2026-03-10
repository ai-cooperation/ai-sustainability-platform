"""Tests for TwWraReservoirConnector（台灣水利署水庫水情連接器）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.environment.tw_wra_reservoir import (
    TwWraReservoirConnector,
    _extract_records,
    _safe_numeric,
)


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings_instance = MagicMock()
        mock_settings.return_value = settings_instance
        return TwWraReservoirConnector()


@pytest.fixture
def sample_response_dict():
    """水利署 API 回傳 dict 格式。"""
    return {
        "records": [
            {
                "ReservoirName": "翡翠水庫",
                "WaterLevel": "165.32",
                "PercentageOfStorage": "85.2",
                "InflowDischarge": "12.5",
                "OutflowDischarge": "8.3",
                "ObservationTime": "2026-03-10 14:00:00",
            },
            {
                "ReservoirName": "石門水庫",
                "WaterLevel": "230.15",
                "PercentageOfStorage": "72.1",
                "InflowDischarge": "5.0",
                "OutflowDischarge": "10.2",
                "ObservationTime": "2026-03-10 14:00:00",
            },
        ],
    }


@pytest.fixture
def sample_response_list():
    """水利署 API 回傳 list 格式。"""
    return [
        {
            "ReservoirName": "曾文水庫",
            "WaterLevel": "210.50",
            "PercentageOfStorage": "60.0",
            "InflowDischarge": "3.2",
            "OutflowDischarge": "7.1",
            "ObservationTime": "2026-03-10 14:00:00",
        },
    ]


class TestTwWraReservoirConnector:
    def test_name(self, connector):
        assert connector.name == "tw_wra_reservoir"

    def test_domain(self, connector):
        assert connector.domain == "environment"

    @patch("src.connectors.environment.tw_wra_reservoir.requests.get")
    def test_fetch_dict_response(self, mock_get, connector, sample_response_dict):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response_dict
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch()
        assert "records" in result

    @patch("src.connectors.environment.tw_wra_reservoir.requests.get")
    def test_fetch_list_response(self, mock_get, connector, sample_response_list):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response_list
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch()
        assert "records" in result
        assert len(result["records"]) == 1

    @patch("src.connectors.environment.tw_wra_reservoir.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Timeout")

        with pytest.raises(ConnectorError, match="API 請求失敗"):
            connector.fetch()

    def test_normalize_success(self, connector, sample_response_dict):
        df = connector.normalize(sample_response_dict)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "timestamp" in df.columns
        assert "reservoir_name" in df.columns
        assert "water_level" in df.columns
        assert "storage_percentage" in df.columns
        assert "inflow_cms" in df.columns
        assert "outflow_cms" in df.columns
        assert "country" in df.columns

    def test_normalize_values(self, connector, sample_response_dict):
        df = connector.normalize(sample_response_dict)

        assert df["reservoir_name"].iloc[0] == "翡翠水庫"
        assert df["water_level"].iloc[0] == 165.32
        assert df["storage_percentage"].iloc[0] == 85.2
        assert df["inflow_cms"].iloc[0] == 12.5
        assert df["outflow_cms"].iloc[0] == 8.3
        assert df["country"].iloc[0] == "TW"

    def test_normalize_list_input(self, connector):
        """list 格式的回應也應正確處理。"""
        raw = {"records": [
            {
                "ReservoirName": "曾文水庫",
                "WaterLevel": "210.50",
                "PercentageOfStorage": "60.0",
                "ObservationTime": "2026-03-10 14:00:00",
            },
        ]}
        df = connector.normalize(raw)
        assert len(df) == 1
        assert df["reservoir_name"].iloc[0] == "曾文水庫"

    def test_normalize_empty_records(self, connector):
        with pytest.raises(ConnectorError, match="無水庫資料"):
            connector.normalize({"records": []})

    def test_normalize_timestamp_parsing(self, connector, sample_response_dict):
        df = connector.normalize(sample_response_dict)
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_normalize_handles_missing_values(self, connector):
        raw = {"records": [
            {
                "ReservoirName": "日月潭水庫",
                "WaterLevel": "--",
                "PercentageOfStorage": "",
                "InflowDischarge": None,
                "OutflowDischarge": "-",
                "ObservationTime": "2026-03-10 14:00:00",
            },
        ]}
        df = connector.normalize(raw)
        assert pd.isna(df["water_level"].iloc[0])
        assert pd.isna(df["storage_percentage"].iloc[0])
        assert pd.isna(df["inflow_cms"].iloc[0])
        assert pd.isna(df["outflow_cms"].iloc[0])

    def test_health_check_params(self, connector):
        params = connector._health_check_params()
        assert params == {}


class TestExtractRecords:
    def test_list_input(self):
        assert _extract_records([{"a": 1}]) == [{"a": 1}]

    def test_dict_with_records(self):
        assert _extract_records({"records": [{"a": 1}]}) == [{"a": 1}]

    def test_dict_with_data(self):
        assert _extract_records({"data": [{"a": 1}]}) == [{"a": 1}]

    def test_empty_dict(self):
        assert _extract_records({}) == []

    def test_nested_dict(self):
        result = _extract_records({"Data": {"records": [{"a": 1}]}})
        assert result == [{"a": 1}]


class TestSafeNumeric:
    def test_double_dash(self):
        assert _safe_numeric("--") is None

    def test_valid_number(self):
        assert _safe_numeric("42.5") == 42.5
