"""Tests for TWSECompanyConnector（台灣上市櫃公司基本資料連接器）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.corporate.twse_company import TWSECompanyConnector, _safe_numeric


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return TWSECompanyConnector()


@pytest.fixture
def twse_records():
    return [
        {
            "出表日期": "1150309",
            "公司代號": "1101",
            "公司名稱": "臺灣水泥股份有限公司",
            "公司簡稱": "台泥",
            "產業別": "01",
            "董事長": "張安平",
            "上市日期": "19620209",
            "實收資本額": "77231817420",
            "住址": "台北市中山北路2段113號",
            "網址": "https://www.tccgroupholdings.com/tw/",
        },
        {
            "出表日期": "1150309",
            "公司代號": "1102",
            "公司名稱": "亞洲水泥股份有限公司",
            "公司簡稱": "亞泥",
            "產業別": "01",
            "董事長": "徐旭東",
            "上市日期": "19620608",
            "實收資本額": "35465628810",
            "住址": "台北市大安區敦化南路2段207號30、31樓",
            "網址": "www.acc.com.tw",
        },
    ]


@pytest.fixture
def tpex_records():
    return [
        {
            "Date": "1150310",
            "SecuritiesCompanyCode": "1240",
            "CompanyName": "茂生農經股份有限公司",
            "CompanyAbbreviation": "茂生農經",
            "SecuritiesIndustryCode": "33",
            "Chairman": "吳清德",
            "DateOfListing": "20180808",
            "Paidin.Capital.NTDollars": "442323730",
            "Address": "2F.,No.30,Sec. 1,Heping W.Rd.",
            "WebAddress": "https://www.morn-sun.com.tw/",
        },
    ]


class TestTWSECompanyConnector:
    def test_name(self, connector):
        assert connector.name == "twse_company"

    def test_domain(self, connector):
        assert connector.domain == "corporate"

    @patch("src.connectors.corporate.twse_company.requests.get")
    def test_fetch_success(self, mock_get, connector, twse_records, tpex_records):
        twse_resp = MagicMock()
        twse_resp.json.return_value = twse_records
        twse_resp.raise_for_status = MagicMock()

        tpex_resp = MagicMock()
        tpex_resp.json.return_value = tpex_records
        tpex_resp.raise_for_status = MagicMock()

        mock_get.side_effect = [twse_resp, tpex_resp]

        result = connector.fetch()

        assert len(result) == 3
        assert result[0]["_market"] == "twse"
        assert result[2]["_market"] == "tpex"
        assert mock_get.call_count == 2

    @patch("src.connectors.corporate.twse_company.requests.get")
    def test_fetch_twse_error(self, mock_get, connector):
        mock_get.side_effect = requests.RequestException("Connection refused")

        with pytest.raises(ConnectorError, match="twse API 請求失敗"):
            connector.fetch()

    @patch("src.connectors.corporate.twse_company.requests.get")
    def test_fetch_tpex_error(self, mock_get, connector, twse_records):
        twse_resp = MagicMock()
        twse_resp.json.return_value = twse_records
        twse_resp.raise_for_status = MagicMock()

        mock_get.side_effect = [
            twse_resp,
            requests.RequestException("TPEx down"),
        ]

        with pytest.raises(ConnectorError, match="tpex API 請求失敗"):
            connector.fetch()

    def test_normalize_twse_records(self, connector, twse_records):
        for r in twse_records:
            r["_market"] = "twse"
        df = connector.normalize(twse_records)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert df["stock_id"].iloc[0] == "1101"
        assert df["company_name"].iloc[0] == "臺灣水泥股份有限公司"
        assert df["company_abbr"].iloc[0] == "台泥"
        assert df["chairman"].iloc[0] == "張安平"
        assert df["market"].iloc[0] == "twse"
        assert df["paid_in_capital"].iloc[0] == 77231817420.0

    def test_normalize_tpex_records(self, connector, tpex_records):
        for r in tpex_records:
            r["_market"] = "tpex"
        df = connector.normalize(tpex_records)

        assert len(df) == 1
        assert df["stock_id"].iloc[0] == "1240"
        assert df["company_name"].iloc[0] == "茂生農經股份有限公司"
        assert df["market"].iloc[0] == "tpex"
        assert df["paid_in_capital"].iloc[0] == 442323730.0

    def test_normalize_combined(self, connector, twse_records, tpex_records):
        for r in twse_records:
            r["_market"] = "twse"
        for r in tpex_records:
            r["_market"] = "tpex"
        combined = twse_records + tpex_records
        df = connector.normalize(combined)

        assert len(df) == 3
        assert set(df["market"]) == {"twse", "tpex"}

    def test_normalize_empty(self, connector):
        with pytest.raises(ConnectorError, match="無公司資料"):
            connector.normalize([])

    def test_normalize_has_timestamp(self, connector, twse_records):
        for r in twse_records:
            r["_market"] = "twse"
        df = connector.normalize(twse_records)
        assert "timestamp" in df.columns
        assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])

    def test_normalize_columns(self, connector, twse_records):
        for r in twse_records:
            r["_market"] = "twse"
        df = connector.normalize(twse_records)
        expected = {
            "stock_id", "company_name", "company_abbr", "industry",
            "chairman", "listing_date", "paid_in_capital", "address",
            "website", "market", "timestamp",
        }
        assert set(df.columns) == expected

    def test_health_check_params(self, connector):
        params = connector._health_check_params()
        assert params == {"timeout": 10}


class TestSafeNumeric:
    def test_valid_integer(self):
        assert _safe_numeric("42") == 42.0

    def test_with_commas(self):
        assert _safe_numeric("1,234,567") == 1234567.0

    def test_none(self):
        assert _safe_numeric(None) is None

    def test_empty(self):
        assert _safe_numeric("") is None

    def test_dash(self):
        assert _safe_numeric("-") is None

    def test_fullwidth_dash(self):
        assert _safe_numeric("－") is None

    def test_invalid(self):
        assert _safe_numeric("N/A") is None
