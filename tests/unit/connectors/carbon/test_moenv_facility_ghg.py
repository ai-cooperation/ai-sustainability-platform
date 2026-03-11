"""Tests for MoenvFacilityGhgConnector（環境部事業溫室氣體設施層級連接器）。"""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.carbon.moenv_facility_ghg import (
    MoenvFacilityGhgConnector,
    _safe_int,
    _safe_numeric,
)


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        settings_instance = MagicMock()
        settings_instance.moenv_api_key = ""
        mock_settings.return_value = settings_instance
        return MoenvFacilityGhgConnector()


def _make_record(
    year: str = "111",
    name: str = "台積電股份有限公司",
    reg_no: str = "F12345678",
    industry_code: str = "2610",
    industry_name: str = "積體電路製造業",
    county: str = "新竹市",
    scope1: str = "123456.78",
    scope2: str = "654321.12",
    total: str = "777777.90",
) -> dict:
    """建立一筆模擬的 MOENV 設施排放 record。"""
    return {
        "盤查年度": year,
        "事業名稱": name,
        "登記編號": reg_no,
        "行業代碼": industry_code,
        "行業名稱": industry_name,
        "縣市": county,
        "直接排放(公噸CO2e)": scope1,
        "能源間接排放(公噸CO2e)": scope2,
        "排放總量(公噸CO2e)": total,
    }


@pytest.fixture
def sample_records():
    return [
        _make_record(
            year="111",
            name="台積電股份有限公司",
            reg_no="F12345678",
            scope1="123456.78",
            scope2="654321.12",
            total="777777.90",
        ),
        _make_record(
            year="111",
            name="中華鋼鐵股份有限公司",
            reg_no="G87654321",
            industry_code="2410",
            industry_name="鋼鐵冶煉業",
            county="高雄市",
            scope1="987654.32",
            scope2="123456.78",
            total="1111111.10",
        ),
        _make_record(
            year="110",
            name="台灣塑膠工業股份有限公司",
            reg_no="H11223344",
            industry_code="2011",
            industry_name="石油化工原料製造業",
            county="雲林縣",
            scope1="500000.00",
            scope2="200000.00",
            total="700000.00",
        ),
    ]


def _mock_api_response(records: list[dict]) -> dict:
    """包裝成 MOENV API 回傳格式。"""
    return {"records": records}


class TestMoenvFacilityGhgConnector:
    def test_name(self, connector):
        assert connector.name == "moenv_facility_ghg"

    def test_domain(self, connector):
        assert connector.domain == "carbon"

    @patch("src.connectors.carbon.moenv_facility_ghg.requests.get")
    def test_fetch_single_page(self, mock_get, connector, sample_records):
        """單頁回應（筆數 < limit）應直接回傳。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = _mock_api_response(sample_records)
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch(limit=1000)

        assert len(result) == 3
        assert result[0]["事業名稱"] == "台積電股份有限公司"
        mock_get.assert_called_once()

    @patch("src.connectors.carbon.moenv_facility_ghg.requests.get")
    def test_fetch_pagination(self, mock_get, connector):
        """多頁回應應自動分頁合併。"""
        page1 = [_make_record(name=f"公司{i}") for i in range(3)]
        page2 = [_make_record(name="最後公司")]

        mock_resp1 = MagicMock()
        mock_resp1.json.return_value = _mock_api_response(page1)
        mock_resp1.raise_for_status = MagicMock()

        mock_resp2 = MagicMock()
        mock_resp2.json.return_value = _mock_api_response(page2)
        mock_resp2.raise_for_status = MagicMock()

        mock_get.side_effect = [mock_resp1, mock_resp2]

        result = connector.fetch(limit=3)

        assert len(result) == 4
        assert mock_get.call_count == 2
        # 驗證第二頁 offset = 3
        second_call_params = mock_get.call_args_list[1][1]["params"]
        assert second_call_params["offset"] == 3

    @patch("src.connectors.carbon.moenv_facility_ghg.requests.get")
    def test_fetch_http_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Connection timeout")

        with pytest.raises(ConnectorError, match="API 請求失敗"):
            connector.fetch()

    @patch("src.connectors.carbon.moenv_facility_ghg.requests.get")
    def test_fetch_empty_response(self, mock_get, connector):
        """空 API 回應應回傳空列表。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"records": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = connector.fetch()
        assert result == []

    @patch("src.connectors.carbon.moenv_facility_ghg.requests.get")
    def test_fetch_uses_settings_api_key(self, mock_get, connector):
        """若 settings 有 moenv_api_key 則優先使用。"""
        connector._settings.moenv_api_key = "custom-key-123"

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"records": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        connector.fetch()

        call_params = mock_get.call_args[1]["params"]
        assert call_params["api_key"] == "custom-key-123"

    @patch("src.connectors.carbon.moenv_facility_ghg.requests.get")
    def test_fetch_uses_default_api_key(self, mock_get, connector):
        """settings 無 key 時使用預設。"""
        connector._settings.moenv_api_key = ""

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"records": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        connector.fetch()

        call_params = mock_get.call_args[1]["params"]
        assert call_params["api_key"] == MoenvFacilityGhgConnector.DEFAULT_API_KEY


class TestNormalize:
    def test_normalize_success(self, connector, sample_records):
        df = connector.normalize(sample_records)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3

        expected_cols = {
            "facility_name", "company_name", "registration_no",
            "industry_code", "industry_name", "county",
            "scope1_emissions", "scope2_emissions", "total_emissions",
            "report_year", "timestamp",
        }
        assert expected_cols.issubset(set(df.columns))

    def test_normalize_values(self, connector, sample_records):
        df = connector.normalize(sample_records)

        row = df.iloc[0]
        assert row["facility_name"] == "台積電股份有限公司"
        assert row["company_name"] == "台積電股份有限公司"
        assert row["registration_no"] == "F12345678"
        assert row["industry_code"] == "2610"
        assert row["county"] == "新竹市"
        assert row["scope1_emissions"] == 123456.78
        assert row["scope2_emissions"] == 654321.12
        assert row["total_emissions"] == 777777.90
        assert row["report_year"] == 2022

    def test_normalize_timestamp(self, connector, sample_records):
        df = connector.normalize(sample_records)

        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
        # 盤查年度 111 → 西元 2022
        assert df["timestamp"].iloc[0].year == 2022
        assert df["timestamp"].iloc[0].month == 1
        assert df["timestamp"].iloc[0].day == 1

    def test_normalize_empty(self, connector):
        with pytest.raises(ConnectorError, match="無設施排放資料"):
            connector.normalize([])

    def test_normalize_missing_fields(self, connector):
        """缺少欄位時應填入預設空值。"""
        records = [{"盤查年度": "111", "事業名稱": "測試公司"}]
        df = connector.normalize(records)

        assert len(df) == 1
        assert df["facility_name"].iloc[0] == "測試公司"
        assert df["scope1_emissions"].iloc[0] is None
        assert df["scope2_emissions"].iloc[0] is None

    def test_normalize_comma_in_numbers(self, connector):
        """數值中含千分位逗號應正確解析。"""
        records = [
            _make_record(scope1="1,234,567.89", scope2="987,654.32", total="2,222,222.21")
        ]
        df = connector.normalize(records)

        assert df["scope1_emissions"].iloc[0] == 1234567.89
        assert df["scope2_emissions"].iloc[0] == 987654.32
        assert df["total_emissions"].iloc[0] == 2222222.21


class TestHealthCheckParams:
    def test_health_check_params(self, connector):
        params = connector._health_check_params()
        assert params == {"limit": 1}


class TestSafeNumeric:
    def test_valid_float(self):
        assert _safe_numeric("42000.5") == 42000.5

    def test_valid_int_string(self):
        assert _safe_numeric("100") == 100.0

    def test_with_commas(self):
        assert _safe_numeric("1,234,567.89") == 1234567.89

    def test_none(self):
        assert _safe_numeric(None) is None

    def test_empty(self):
        assert _safe_numeric("") is None

    def test_dash(self):
        assert _safe_numeric("-") is None

    def test_invalid(self):
        assert _safe_numeric("N/A") is None


class TestSafeInt:
    def test_valid(self):
        assert _safe_int("111") == 111

    def test_with_spaces(self):
        assert _safe_int(" 110 ") == 110

    def test_none(self):
        assert _safe_int(None) is None

    def test_empty(self):
        assert _safe_int("") is None

    def test_invalid(self):
        assert _safe_int("abc") is None
