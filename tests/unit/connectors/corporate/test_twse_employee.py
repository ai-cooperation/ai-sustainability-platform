"""Tests for TWSEEmployeeConnector（台灣上市櫃公司員工薪資連接器）。"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.corporate.twse_employee import (
    TWSEEmployeeConnector,
    _find_field,
    _safe_numeric,
)


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return TWSEEmployeeConnector()


@pytest.fixture
def twse_records():
    return [
        {
            "出表日期": "1141230",
            "報告年度": "113",
            "公司代號": "1101",
            "公司名稱": "台泥",
            "員工福利平均數(仟元/人)": "1185",
            "員工薪資平均數(仟元/人) ": "1045",
            "非擔任主管職務之全時員工薪資平均數(仟元/人) ": "1003",
            "非擔任主管之全時員工薪資中位數(仟元/人) ": "877",
            "管理職女性主管佔比": "19.00%",
        },
        {
            "出表日期": "1141230",
            "報告年度": "113",
            "公司代號": "1102",
            "公司名稱": "亞泥",
            "員工福利平均數(仟元/人)": "1349",
            "員工薪資平均數(仟元/人) ": "1248",
            "非擔任主管職務之全時員工薪資平均數(仟元/人) ": "1132",
            "非擔任主管之全時員工薪資中位數(仟元/人) ": "988",
            "管理職女性主管佔比": "22.00%",
        },
    ]


@pytest.fixture
def tpex_records():
    return [
        {
            "出表日期": "1141230",
            "報告年度": "113",
            "公司代號": "1240",
            "公司名稱": "茂生農經",
            "員工福利平均數(仟元/人)(每年6/2起公開)": "982",
            "員工薪資平均數(仟元/人)(每年6/2起公開)": "841",
            "非擔任主管職務之全時員工薪資平均數(仟元/人)(每年7/1起公開)": "740",
            "非擔任主管之全時員工薪資中位數(仟元/人)(每年7/1起公開)": "649",
            "管理職女性主管佔比": "6.00%",
        },
    ]


class TestTWSEEmployeeConnector:
    def test_name(self, connector):
        assert connector.name == "twse_employee"

    def test_domain(self, connector):
        assert connector.domain == "corporate"

    @patch("src.connectors.corporate.twse_employee.create_tw_gov_session")
    def test_fetch_success(self, mock_get, connector, twse_records, tpex_records):
        twse_resp = MagicMock()
        twse_resp.json.return_value = twse_records
        twse_resp.raise_for_status = MagicMock()

        tpex_resp = MagicMock()
        tpex_resp.json.return_value = tpex_records
        tpex_resp.raise_for_status = MagicMock()

        mock_get.return_value.get.side_effect = [twse_resp, tpex_resp]
        result = connector.fetch()

        assert len(result) == 3
        assert result[0]["_market"] == "twse"
        assert result[2]["_market"] == "tpex"

    @patch("src.connectors.corporate.twse_employee.create_tw_gov_session")
    def test_fetch_error(self, mock_get, connector):
        mock_get.return_value.get.side_effect = requests.RequestException("down")

        with pytest.raises(ConnectorError, match="twse API 請求失敗"):
            connector.fetch()

    def test_normalize_twse(self, connector, twse_records):
        for r in twse_records:
            r["_market"] = "twse"
        df = connector.normalize(twse_records)

        assert len(df) == 2
        assert df["stock_id"].iloc[0] == "1101"
        assert df["company_name"].iloc[0] == "台泥"
        assert df["avg_employee_benefit"].iloc[0] == 1185.0
        assert df["avg_salary"].iloc[0] == 1045.0
        assert df["avg_salary_non_mgr"].iloc[0] == 1003.0
        assert df["median_salary_non_mgr"].iloc[0] == 877.0
        assert df["female_mgr_ratio"].iloc[0] == 19.0
        assert df["year"].iloc[0] == 2024  # 113 + 1911
        assert df["market"].iloc[0] == "twse"

    def test_normalize_tpex(self, connector, tpex_records):
        """TPEx 欄位名稱帶括號說明，驗證模糊比對能正確擷取。"""
        for r in tpex_records:
            r["_market"] = "tpex"
        df = connector.normalize(tpex_records)

        assert len(df) == 1
        assert df["stock_id"].iloc[0] == "1240"
        assert df["avg_employee_benefit"].iloc[0] == 982.0
        assert df["avg_salary"].iloc[0] == 841.0
        assert df["avg_salary_non_mgr"].iloc[0] == 740.0
        assert df["median_salary_non_mgr"].iloc[0] == 649.0
        assert df["female_mgr_ratio"].iloc[0] == 6.0
        assert df["market"].iloc[0] == "tpex"

    def test_normalize_timestamp(self, connector, twse_records):
        for r in twse_records:
            r["_market"] = "twse"
        df = connector.normalize(twse_records)

        # 報告年度 113 → 2024-12-31
        ts = df["timestamp"].iloc[0]
        assert ts.year == 2024
        assert ts.month == 12
        assert ts.day == 31

    def test_normalize_empty(self, connector):
        with pytest.raises(ConnectorError, match="無員工資料"):
            connector.normalize([])

    def test_normalize_columns(self, connector, twse_records):
        for r in twse_records:
            r["_market"] = "twse"
        df = connector.normalize(twse_records)

        expected = {
            "stock_id", "company_name", "year",
            "avg_employee_benefit", "avg_salary",
            "avg_salary_non_mgr", "median_salary_non_mgr",
            "female_mgr_ratio", "market", "timestamp",
        }
        assert set(df.columns) == expected

    def test_normalize_combined(self, connector, twse_records, tpex_records):
        for r in twse_records:
            r["_market"] = "twse"
        for r in tpex_records:
            r["_market"] = "tpex"
        combined = twse_records + tpex_records
        df = connector.normalize(combined)

        assert len(df) == 3
        assert set(df["market"]) == {"twse", "tpex"}

    def test_health_check_params(self, connector):
        assert connector._health_check_params() == {"timeout": 10}


class TestFindField:
    def test_exact_match(self):
        record = {"員工福利平均數(仟元/人)": "1185"}
        assert _find_field(record, ["員工福利平均數"]) == "1185"

    def test_with_extra_suffix(self):
        record = {"員工薪資平均數(仟元/人)(每年6/2起公開)": "841"}
        assert _find_field(record, ["員工薪資平均數"]) == "841"

    def test_trailing_space(self):
        record = {"員工薪資平均數(仟元/人) ": "1045"}
        assert _find_field(record, ["員工薪資平均數"]) == "1045"

    def test_not_found(self):
        record = {"公司名稱": "台泥"}
        assert _find_field(record, ["不存在的欄位"]) is None


class TestSafeNumeric:
    def test_valid(self):
        assert _safe_numeric("1185") == 1185.0

    def test_percentage(self):
        assert _safe_numeric("19.00%") == 19.0

    def test_with_commas(self):
        assert _safe_numeric("1,234") == 1234.0

    def test_none(self):
        assert _safe_numeric(None) is None

    def test_dash(self):
        assert _safe_numeric("-") is None

    def test_empty(self):
        assert _safe_numeric("") is None
