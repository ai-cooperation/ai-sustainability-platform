"""Tests for MoenvUvConnector（台灣環境部紫外線指數連接器）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorError
from src.connectors.environment.moenv_uv import (
    MoenvUvConnector,
    _parse_coordinate,
    _safe_float,
)


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings_instance = MagicMock()
        settings_instance.moenv_api_key = None
        mock_settings.return_value = settings_instance
        return MoenvUvConnector()


@pytest.fixture
def sample_response():
    return {
        "include_total": True,
        "resource_id": "UV_S_01",
        "records": [
            {
                "sitename": "鹿林山",
                "uvi": "6.2",
                "unit": "環境部",
                "county": "嘉義縣",
                "wgs84_lon": "120.85985238",
                "wgs84_lat": "23.4720725",
                "datacreationdate": "2026-03-11 14:00:00",
            },
            {
                "sitename": "臺北",
                "uvi": "3.1",
                "unit": "環境部",
                "county": "臺北市",
                "wgs84_lon": "121.5083",
                "wgs84_lat": "25.0375",
                "datacreationdate": "2026-03-11 14:00:00",
            },
            {
                "sitename": "高雄",
                "uvi": "",
                "unit": "環境部",
                "county": "高雄市",
                "wgs84_lon": "120.3113",
                "wgs84_lat": "22.6273",
                "datacreationdate": "2026-03-11 14:00:00",
            },
        ],
        "total": "3",
    }


@pytest.fixture
def dms_response():
    """DMS 格式座標的測試資料。"""
    return {
        "records": [
            {
                "sitename": "測試站",
                "uvi": "5.0",
                "unit": "環境部",
                "county": "測試縣",
                "wgs84_lon": "121,45,24",
                "wgs84_lat": "25,2,0",
                "datacreationdate": "2026-03-11 12:00:00",
            },
        ],
    }


class TestMoenvUvConnector:
    def test_name(self, connector):
        assert connector.name == "moenv_uv"

    def test_domain(self, connector):
        assert connector.domain == "environment"

    @patch("src.connectors.environment.moenv_uv.create_tw_gov_session")
    def test_fetch_success(self, mock_session_fn, connector, sample_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_response
        mock_resp.raise_for_status = MagicMock()
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_session_fn.return_value = mock_session

        result = connector.fetch()

        assert "records" in result
        assert len(result["records"]) == 3
        mock_session.get.assert_called_once()

    @patch("src.connectors.environment.moenv_uv.create_tw_gov_session")
    def test_fetch_http_error(self, mock_session_fn, connector):
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("Service Unavailable")
        mock_session_fn.return_value = mock_session

        with pytest.raises(ConnectorError, match="API 請求失敗"):
            connector.fetch()

    @patch("src.connectors.environment.moenv_uv.create_tw_gov_session")
    def test_fetch_missing_records_key(self, mock_session_fn, connector):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"total": 0}
        mock_resp.raise_for_status = MagicMock()
        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_session_fn.return_value = mock_session

        with pytest.raises(ConnectorError, match="缺少 'records' 欄位"):
            connector.fetch()

    def test_normalize_success(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        expected_columns = {
            "timestamp", "station_name", "county", "uv_index",
            "latitude", "longitude", "source_agency",
        }
        assert set(df.columns) == expected_columns

    def test_normalize_values(self, connector, sample_response):
        df = connector.normalize(sample_response)

        assert df["station_name"].iloc[0] == "鹿林山"
        assert df["county"].iloc[0] == "嘉義縣"
        assert df["uv_index"].iloc[0] == 6.2
        assert df["latitude"].iloc[0] == pytest.approx(23.4720725)
        assert df["longitude"].iloc[0] == pytest.approx(120.85985238)
        assert df["source_agency"].iloc[0] == "環境部"

    def test_normalize_handles_missing_uvi(self, connector, sample_response):
        """驗證空值的 UVI 正確處理為 None。"""
        df = connector.normalize(sample_response)
        assert pd.isna(df["uv_index"].iloc[2])

    def test_normalize_empty_records(self, connector):
        with pytest.raises(ConnectorError, match="無監測資料"):
            connector.normalize({"records": []})

    def test_normalize_timestamp_parsing(self, connector, sample_response):
        df = connector.normalize(sample_response)
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        assert df["timestamp"].iloc[0] == pd.Timestamp("2026-03-11 14:00:00")

    def test_normalize_dms_coordinates(self, connector, dms_response):
        """驗證度分秒 (DMS) 格式座標正確轉換為十進位。"""
        df = connector.normalize(dms_response)

        # 121,45,24 → 121 + 45/60 + 24/3600 = 121.75667
        assert df["longitude"].iloc[0] == pytest.approx(121.75667, abs=1e-4)
        # 25,2,0 → 25 + 2/60 + 0/3600 = 25.03333
        assert df["latitude"].iloc[0] == pytest.approx(25.03333, abs=1e-4)

    def test_health_check_params(self, connector):
        params = connector._health_check_params()
        assert params == {"limit": 1}


class TestParseCoordinate:
    def test_decimal_degrees(self):
        assert _parse_coordinate("120.85985238") == pytest.approx(120.85985238)

    def test_dms_format(self):
        # 121°45'24" = 121 + 45/60 + 24/3600
        assert _parse_coordinate("121,45,24") == pytest.approx(121.75667, abs=1e-4)

    def test_dms_with_zero_seconds(self):
        assert _parse_coordinate("25,2,0") == pytest.approx(25.03333, abs=1e-4)

    def test_none(self):
        assert _parse_coordinate(None) is None

    def test_empty_string(self):
        assert _parse_coordinate("") is None

    def test_invalid_dms(self):
        assert _parse_coordinate("121,45") is None

    def test_non_numeric(self):
        assert _parse_coordinate("abc") is None


class TestSafeFloat:
    def test_valid_float(self):
        assert _safe_float("6.2") == 6.2

    def test_valid_integer(self):
        assert _safe_float("10") == 10.0

    def test_none(self):
        assert _safe_float(None) is None

    def test_empty_string(self):
        assert _safe_float("") is None

    def test_dash(self):
        assert _safe_float("-") is None

    def test_invalid_string(self):
        assert _safe_float("N/A") is None
