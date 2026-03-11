"""Tests for TWSEIncomeConnector（台灣上市櫃公司綜合損益連接器）。"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.corporate.twse_income import (
    TWSEIncomeConnector,
    _quarter_to_timestamp,
    _safe_numeric,
)


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return TWSEIncomeConnector()


@pytest.fixture
def twse_records():
    return [
        {
            "出表日期": "1150310",
            "年度": "114",
            "季別": "4",
            "公司代號": "1215",
            "公司名稱": "台灣卜蜂企業股份有限公司",
            "產業別": "食品工業",
            "基本每股盈餘(元)": "10.39",
            "普通股每股面額": "新台幣                 10.0000元",
            "營業收入": "28431622.00",
            "營業利益": "3752534.00",
            "營業外收入及支出": "109301.00",
            "稅後淨利": "3076657.00",
        },
    ]


@pytest.fixture
def tpex_records():
    return [
        {
            "Date": "1150310",
            "Year": "114",
            "季別": "4",
            "SecuritiesCompanyCode": "1259",
            "CompanyName": "安心食品服務股份有限公司",
            "產業別": "觀光餐旅",
            "基本每股盈餘": "2.45",
            "普通股每股面額": "新台幣                 10.0000元",
            "營業收入": "6062167.00",
            "營業利益": "-13589.00",
            "營業外收入及支出": "54527.00",
            "稅後淨利": "82378.00",
        },
    ]


class TestTWSEIncomeConnector:
    def test_name(self, connector):
        assert connector.name == "twse_income"

    def test_domain(self, connector):
        assert connector.domain == "corporate"

    @patch("src.connectors.corporate.twse_income.requests.get")
    def test_fetch_success(self, mock_get, connector, twse_records, tpex_records):
        twse_resp = MagicMock()
        twse_resp.json.return_value = twse_records
        twse_resp.raise_for_status = MagicMock()

        tpex_resp = MagicMock()
        tpex_resp.json.return_value = tpex_records
        tpex_resp.raise_for_status = MagicMock()

        mock_get.side_effect = [twse_resp, tpex_resp]
        result = connector.fetch()

        assert len(result) == 2
        assert result[0]["_market"] == "twse"
        assert result[1]["_market"] == "tpex"

    @patch("src.connectors.corporate.twse_income.requests.get")
    def test_fetch_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("500")

        with pytest.raises(ConnectorError, match="twse API 請求失敗"):
            connector.fetch()

    def test_normalize_twse(self, connector, twse_records):
        for r in twse_records:
            r["_market"] = "twse"
        df = connector.normalize(twse_records)

        assert len(df) == 1
        assert df["stock_id"].iloc[0] == "1215"
        assert df["company_name"].iloc[0] == "台灣卜蜂企業股份有限公司"
        assert df["eps"].iloc[0] == 10.39
        assert df["revenue"].iloc[0] == 28431622.0
        assert df["operating_profit"].iloc[0] == 3752534.0
        assert df["non_operating_income"].iloc[0] == 109301.0
        assert df["net_income"].iloc[0] == 3076657.0
        assert df["year"].iloc[0] == 2025  # 114 + 1911
        assert df["quarter"].iloc[0] == 4.0
        assert df["market"].iloc[0] == "twse"

    def test_normalize_tpex(self, connector, tpex_records):
        for r in tpex_records:
            r["_market"] = "tpex"
        df = connector.normalize(tpex_records)

        assert len(df) == 1
        assert df["stock_id"].iloc[0] == "1259"
        assert df["eps"].iloc[0] == 2.45
        assert df["operating_profit"].iloc[0] == -13589.0
        assert df["market"].iloc[0] == "tpex"

    def test_normalize_timestamp_from_year_quarter(self, connector, twse_records):
        for r in twse_records:
            r["_market"] = "twse"
        df = connector.normalize(twse_records)

        # 年度 114 Q4 → 2025-12-01 UTC
        ts = df["timestamp"].iloc[0]
        assert ts.year == 2025
        assert ts.month == 12

    def test_normalize_empty(self, connector):
        with pytest.raises(ConnectorError, match="無損益資料"):
            connector.normalize([])

    def test_normalize_columns(self, connector, twse_records):
        for r in twse_records:
            r["_market"] = "twse"
        df = connector.normalize(twse_records)

        expected = {
            "stock_id", "company_name", "industry", "year", "quarter",
            "eps", "revenue", "operating_profit", "non_operating_income",
            "net_income", "market", "timestamp",
        }
        assert set(df.columns) == expected

    def test_normalize_negative_values(self, connector):
        records = [
            {
                "年度": "113",
                "季別": "2",
                "公司代號": "9999",
                "公司名稱": "虧損公司",
                "產業別": "其他",
                "基本每股盈餘(元)": "-1.23",
                "營業收入": "100000.00",
                "營業利益": "-50000.00",
                "營業外收入及支出": "-10000.00",
                "稅後淨利": "-60000.00",
                "_market": "twse",
            },
        ]
        df = connector.normalize(records)

        assert df["eps"].iloc[0] == -1.23
        assert df["operating_profit"].iloc[0] == -50000.0
        assert df["net_income"].iloc[0] == -60000.0

    def test_health_check_params(self, connector):
        assert connector._health_check_params() == {"timeout": 10}


class TestQuarterToTimestamp:
    def test_q1(self):
        result = _quarter_to_timestamp("113", "1")
        assert result == datetime(2024, 3, 1, tzinfo=UTC)

    def test_q2(self):
        result = _quarter_to_timestamp("113", "2")
        assert result == datetime(2024, 6, 1, tzinfo=UTC)

    def test_q3(self):
        result = _quarter_to_timestamp("114", "3")
        assert result == datetime(2025, 9, 1, tzinfo=UTC)

    def test_q4(self):
        result = _quarter_to_timestamp("114", "4")
        assert result == datetime(2025, 12, 1, tzinfo=UTC)

    def test_invalid_year(self):
        assert _quarter_to_timestamp("abc", "1") is None

    def test_invalid_quarter(self):
        assert _quarter_to_timestamp("113", "abc") is None


class TestSafeNumeric:
    def test_valid_float(self):
        assert _safe_numeric("28431622.00") == 28431622.0

    def test_negative(self):
        assert _safe_numeric("-13589.00") == -13589.0

    def test_none(self):
        assert _safe_numeric(None) is None

    def test_dash(self):
        assert _safe_numeric("-") is None

    def test_empty(self):
        assert _safe_numeric("") is None
