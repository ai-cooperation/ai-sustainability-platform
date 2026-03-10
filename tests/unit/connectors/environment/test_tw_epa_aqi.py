"""Tests for TwEpaAqiConnector（台灣環境部空氣品質連接器）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.environment.tw_epa_aqi import TwEpaAqiConnector, _safe_numeric


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings_instance = MagicMock()
        mock_settings.return_value = settings_instance
        return TwEpaAqiConnector()


@pytest.fixture
def sample_response():
    return {
        "records": [
            {
                "sitename": "松山",
                "county": "臺北市",
                "aqi": "45",
                "pm2.5": "12",
                "pm10": "25",
                "o3": "30",
                "status": "良好",
                "publishtime": "2026-03-10 14:00",
            },
            {
                "sitename": "板橋",
                "county": "新北市",
                "aqi": "68",
                "pm2.5": "22",
                "pm10": "40",
                "o3": "45",
                "status": "普通",
                "publishtime": "2026-03-10 14:00",
            },
            {
                "sitename": "左營",
                "county": "高雄市",
                "aqi": "",
                "pm2.5": "-",
                "pm10": None,
                "o3": "50",
                "status": "設備維護",
                "publishtime": "2026-03-10 14:00",
            },
        ],
    }


class TestTwEpaAqiConnector:
    def test_name(self, connector):
        assert connector.name == "tw_epa_aqi"

    def test_domain(self, connector):
        assert connector.domain == "environment"

    @patch("src.connectors.environment.tw_epa_aqi.requests.get")
    def test_fetch_success(self, mock_get, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch()

        assert "records" in result
        assert len(result["records"]) == 3
        mock_get.assert_called_once()

    @patch("src.connectors.environment.tw_epa_aqi.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Service Unavailable")

        with pytest.raises(ConnectorError, match="API 請求失敗"):
            connector.fetch()

    @patch("src.connectors.environment.tw_epa_aqi.requests.get")
    def test_fetch_missing_records_key(self, mock_get, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"total": 0}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        with pytest.raises(ConnectorError, match="缺少 'records' 欄位"):
            connector.fetch()

    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "timestamp" in df.columns
        assert "station" in df.columns
        assert "county" in df.columns
        assert "aqi" in df.columns
        assert "pm25" in df.columns
        assert "pm10" in df.columns
        assert "o3" in df.columns
        assert "status" in df.columns
        assert "country" in df.columns

    def test_normalize_values(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert df["station"].iloc[0] == "松山"
        assert df["county"].iloc[0] == "臺北市"
        assert df["aqi"].iloc[0] == 45.0
        assert df["pm25"].iloc[0] == 12.0
        assert df["country"].iloc[0] == "TW"

    def test_normalize_handles_missing_values(self, connector, sample_response):
        """驗證空值、破折號、None 等都正確處理為 None。"""
        df = connector.normalize(sample_response)

        # 第三筆（左營）的 aqi=""、pm2.5="-"、pm10=None
        assert pd.isna(df["aqi"].iloc[2])
        assert pd.isna(df["pm25"].iloc[2])
        assert pd.isna(df["pm10"].iloc[2])

    def test_normalize_empty_records(self, connector):
        with pytest.raises(ConnectorError, match="無監測資料"):
            connector.normalize({"records": []})

    def test_normalize_timestamp_parsing(self, connector, sample_response):
        df = connector.normalize(sample_response)
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_health_check_params(self, connector):
        params = connector._health_check_params()
        assert params == {"limit": 1}


class TestSafeNumeric:
    def test_valid_integer(self):
        assert _safe_numeric("42") == 42.0

    def test_valid_float(self):
        assert _safe_numeric("3.14") == 3.14

    def test_none(self):
        assert _safe_numeric(None) is None

    def test_empty_string(self):
        assert _safe_numeric("") is None

    def test_dash(self):
        assert _safe_numeric("-") is None

    def test_invalid_string(self):
        assert _safe_numeric("N/A") is None
