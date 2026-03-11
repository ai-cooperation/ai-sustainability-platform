"""Tests for TWSERevenueConnector（台灣上市櫃公司月營收連接器）。"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.corporate.twse_revenue import (
    TWSERevenueConnector,
    _parse_roc_year_month,
    _safe_numeric,
)


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return TWSERevenueConnector()


@pytest.fixture
def twse_records():
    return [
        {
            "出表日期": "1150217",
            "資料年月": "11501",
            "公司代號": "1101",
            "公司名稱": "台泥",
            "產業別": "水泥工業",
            "營業收入-當月營收": "12252892",
            "營業收入-上月營收": "14219975",
            "營業收入-去年當月營收": "12213350",
            "營業收入-上月比較增減(%)": "-13.83",
            "營業收入-去年同月增減(%)": "0.32",
            "累計營業收入-當月累計營收": "12252892",
            "累計營業收入-去年累計營收": "12213350",
            "累計營業收入-前期比較增減(%)": "0.32",
            "備註": "-",
        },
    ]


@pytest.fixture
def tpex_records():
    return [
        {
            "出表日期": "1150217",
            "資料年月": "11501",
            "公司代號": "1240",
            "公司名稱": "茂生農經",
            "產業別": "農業科技",
            "營業收入-當月營收": "216068",
            "營業收入-上月營收": "240962",
            "營業收入-去年當月營收": "231435",
            "營業收入-上月比較增減(%)": "-10.33",
            "營業收入-去年同月增減(%)": "-6.64",
            "累計營業收入-當月累計營收": "216068",
            "累計營業收入-去年累計營收": "231435",
            "累計營業收入-前期比較增減(%)": "-6.64",
            "備註": "-",
        },
    ]


class TestTWSERevenueConnector:
    def test_name(self, connector):
        assert connector.name == "twse_revenue"

    def test_domain(self, connector):
        assert connector.domain == "corporate"

    @patch("src.connectors.corporate.twse_revenue.requests.get")
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

    @patch("src.connectors.corporate.twse_revenue.requests.get")
    def test_fetch_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("timeout")

        with pytest.raises(ConnectorError, match="twse API 請求失敗"):
            connector.fetch()

    def test_normalize_twse(self, connector, twse_records):
        for r in twse_records:
            r["_market"] = "twse"
        df = connector.normalize(twse_records)

        assert len(df) == 1
        assert df["stock_id"].iloc[0] == "1101"
        assert df["company_name"].iloc[0] == "台泥"
        assert df["revenue_current_month"].iloc[0] == 12252892.0
        assert df["revenue_prev_month"].iloc[0] == 14219975.0
        assert df["mom_change_pct"].iloc[0] == -13.83
        assert df["yoy_change_pct"].iloc[0] == 0.32
        assert df["market"].iloc[0] == "twse"

    def test_normalize_tpex(self, connector, tpex_records):
        for r in tpex_records:
            r["_market"] = "tpex"
        df = connector.normalize(tpex_records)

        assert len(df) == 1
        assert df["stock_id"].iloc[0] == "1240"
        assert df["market"].iloc[0] == "tpex"

    def test_normalize_timestamp_from_roc(self, connector, twse_records):
        for r in twse_records:
            r["_market"] = "twse"
        df = connector.normalize(twse_records)

        # 11501 → 2026-01-01 UTC
        ts = df["timestamp"].iloc[0]
        assert ts.year == 2026
        assert ts.month == 1

    def test_normalize_empty(self, connector):
        with pytest.raises(ConnectorError, match="無營收資料"):
            connector.normalize([])

    def test_normalize_columns(self, connector, twse_records):
        for r in twse_records:
            r["_market"] = "twse"
        df = connector.normalize(twse_records)

        expected = {
            "stock_id", "company_name", "industry",
            "revenue_current_month", "revenue_prev_month",
            "revenue_yoy_same_month", "mom_change_pct", "yoy_change_pct",
            "ytd_revenue", "ytd_yoy_change_pct", "market", "timestamp",
        }
        assert set(df.columns) == expected

    def test_normalize_with_missing_values(self, connector):
        records = [
            {
                "資料年月": "11501",
                "公司代號": "9999",
                "公司名稱": "測試公司",
                "產業別": "",
                "營業收入-當月營收": "",
                "營業收入-上月營收": "-",
                "營業收入-去年當月營收": None,
                "營業收入-上月比較增減(%)": "",
                "營業收入-去年同月增減(%)": "",
                "累計營業收入-當月累計營收": "",
                "累計營業收入-前期比較增減(%)": "",
                "_market": "twse",
            },
        ]
        df = connector.normalize(records)

        assert pd.isna(df["revenue_current_month"].iloc[0])
        assert pd.isna(df["revenue_prev_month"].iloc[0])
        assert pd.isna(df["mom_change_pct"].iloc[0])

    def test_health_check_params(self, connector):
        assert connector._health_check_params() == {"timeout": 10}


class TestParseRocYearMonth:
    def test_normal(self):
        result = _parse_roc_year_month("11501")
        assert result == datetime(2026, 1, 1, tzinfo=UTC)

    def test_month_12(self):
        result = _parse_roc_year_month("11412")
        assert result == datetime(2025, 12, 1, tzinfo=UTC)

    def test_empty(self):
        assert _parse_roc_year_month("") is None

    def test_none(self):
        assert _parse_roc_year_month(None) is None

    def test_too_short(self):
        assert _parse_roc_year_month("12") is None


class TestSafeNumeric:
    def test_valid(self):
        assert _safe_numeric("12252892") == 12252892.0

    def test_negative(self):
        assert _safe_numeric("-13.83") == -13.83

    def test_with_commas(self):
        assert _safe_numeric("1,234,567") == 1234567.0

    def test_none(self):
        assert _safe_numeric(None) is None

    def test_dash(self):
        assert _safe_numeric("-") is None

    def test_empty(self):
        assert _safe_numeric("") is None
