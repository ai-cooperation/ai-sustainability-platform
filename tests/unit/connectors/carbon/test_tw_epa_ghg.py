"""Tests for TwEpaGhgConnector（台灣環境部溫室氣體排放連接器）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.carbon.tw_epa_ghg import TwEpaGhgConnector, _safe_numeric


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings_instance = MagicMock()
        mock_settings.return_value = settings_instance
        return TwEpaGhgConnector()


@pytest.fixture
def sample_response():
    return {
        "records": [
            {
                "Year": "2022",
                "Sector": "能源部門",
                "GasType": "CO2",
                "Emissions": "150000",
            },
            {
                "Year": "2022",
                "Sector": "工業製程",
                "GasType": "CO2e",
                "Emissions": "45000",
            },
            {
                "Year": "2021",
                "Sector": "農業部門",
                "GasType": "CH4",
                "Emissions": "3200",
            },
        ],
    }


@pytest.fixture
def sample_response_chinese_keys():
    """環境部資料可能使用中文欄位名。"""
    return {
        "records": [
            {
                "統計年": "2022",
                "部門": "能源部門",
                "氣體別": "CO2",
                "排放量": "150000",
            },
        ],
    }


class TestTwEpaGhgConnector:
    def test_name(self, connector):
        assert connector.name == "tw_epa_ghg"

    def test_domain(self, connector):
        assert connector.domain == "carbon"

    @patch("src.connectors.carbon.tw_epa_ghg.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch()

        assert "records" in result
        assert len(result["records"]) == 3

    @patch("src.connectors.carbon.tw_epa_ghg.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Bad Gateway")

        with pytest.raises(ConnectorError, match="API 請求失敗"):
            connector.fetch()

    @patch("src.connectors.carbon.tw_epa_ghg.requests.get")
    def test_fetch_empty_result(self, mock_get, connector):
        """total=0 的空結果應回傳空 records。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"total": 0}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch()
        assert result == {"records": []}

    @patch("src.connectors.carbon.tw_epa_ghg.requests.get")
    def test_fetch_data_key_response(self, mock_get, connector):
        """某些 API 用 'data' key 而非 'records'。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"Year": "2022"}]}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch()
        assert "records" in result
        assert len(result["records"]) == 1

    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "timestamp" in df.columns
        assert "sector" in df.columns
        assert "gas_type" in df.columns
        assert "emissions_kt" in df.columns
        assert "unit" in df.columns
        assert "country" in df.columns

    def test_normalize_values(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert df["sector"].iloc[0] == "能源部門"
        assert df["gas_type"].iloc[0] == "CO2"
        assert df["emissions_kt"].iloc[0] == 150000.0
        assert df["country"].iloc[0] == "TW"
        assert df["unit"].iloc[0] == "kt CO2e"

    def test_normalize_chinese_keys(self, connector, sample_response_chinese_keys):
        """驗證中文欄位名也能正確解析。"""
        df = connector.normalize(sample_response_chinese_keys)

        assert len(df) == 1
        assert df["sector"].iloc[0] == "能源部門"
        assert df["gas_type"].iloc[0] == "CO2"
        assert df["emissions_kt"].iloc[0] == 150000.0

    def test_normalize_timestamp(self, connector, sample_response):
        df = connector.normalize(sample_response)
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        # 2022 年資料的 timestamp 應為 2022-01-01
        assert df["timestamp"].iloc[0].year == 2022

    def test_normalize_empty_records(self, connector):
        with pytest.raises(ConnectorError, match="無排放資料"):
            connector.normalize({"records": []})

    def test_health_check_params(self, connector):
        params = connector._health_check_params()
        assert params == {"limit": 1}


class TestSafeNumeric:
    def test_valid(self):
        assert _safe_numeric("42000") == 42000.0

    def test_none(self):
        assert _safe_numeric(None) is None

    def test_empty(self):
        assert _safe_numeric("") is None

    def test_dash(self):
        assert _safe_numeric("-") is None
