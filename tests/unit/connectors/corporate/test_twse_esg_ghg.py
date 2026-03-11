"""Tests for TWSEEsgGhgConnector（溫室氣體排放連接器）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from src.connectors.base import ConnectorError
from src.connectors.corporate._esg_base import _parse_roc_year, _safe_numeric, _safe_pct
from src.connectors.corporate.twse_esg_ghg import TWSEEsgGhgConnector


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return TWSEEsgGhgConnector()


@pytest.fixture
def sample_twse_data():
    return [
        {
            "出表日期": "1141230",
            "報告年度": "113",
            "公司代號": "2330",
            "公司名稱": "台積電",
            "範疇一排放量(公噸CO2e)": "1500000",
            "範疇二排放量(公噸CO2e)": "8500000",
            "排放總量(公噸CO2e)": "10000000",
            "排放密集度(公噸CO2e/百萬元營收)": "4.5",
            "基準年": "2020",
            "確信/查證情形": "已取得第三方查證",
            "_market": "TWSE",
        },
        {
            "出表日期": "1141230",
            "報告年度": "113",
            "公司代號": "1101",
            "公司名稱": "台泥",
            "範疇一排放量(公噸CO2e)": "9200000",
            "範疇二排放量(公噸CO2e)": "300000",
            "排放總量(公噸CO2e)": "9500000",
            "排放密集度(公噸CO2e/百萬元營收)": "85.2",
            "基準年": "2019",
            "確信/查證情形": "已取得第三方查證",
            "_market": "TWSE",
        },
    ]


class TestTWSEEsgGhgConnector:
    def test_name(self, connector):
        assert connector.name == "twse_esg_ghg"

    def test_domain(self, connector):
        assert connector.domain == "corporate"

    def test_topic_id(self, connector):
        assert connector.topic_id == "1"

    @patch("src.connectors.corporate._esg_base.create_tw_gov_session")
    def test_fetch_combines_twse_and_tpex(self, mock_get, connector):
        """兩個端點都有資料時應合併。"""
        twse_resp = MagicMock()
        twse_resp.json.return_value = [{"公司代號": "2330", "公司名稱": "台積電"}]
        twse_resp.raise_for_status = MagicMock()

        tpex_resp = MagicMock()
        tpex_resp.json.return_value = [{"公司代號": "6488", "公司名稱": "環球晶"}]
        tpex_resp.raise_for_status = MagicMock()

        mock_get.return_value.get.side_effect = [twse_resp, tpex_resp]
        result = connector.fetch()

        assert len(result) == 2
        assert result[0]["_market"] == "TWSE"
        assert result[1]["_market"] == "TPEx"

    @patch("src.connectors.corporate._esg_base.create_tw_gov_session")
    def test_fetch_empty_arrays(self, mock_get, connector):
        """非申報季兩端點都回傳空陣列，不應拋錯。"""
        for _ in range(2):
            resp = MagicMock()
            resp.json.return_value = []
            resp.raise_for_status = MagicMock()
        mock_get.return_value.get.return_value = resp

        result = connector.fetch()
        assert result == []

    @patch("src.connectors.corporate._esg_base.create_tw_gov_session")
    def test_fetch_one_fails_one_succeeds(self, mock_get, connector):
        """一個端點失敗、一個成功，應回傳成功的資料。"""
        twse_resp = MagicMock()
        twse_resp.json.return_value = [{"公司代號": "2330"}]
        twse_resp.raise_for_status = MagicMock()

        mock_get.return_value.get.side_effect = [
            twse_resp,
            requests.RequestException("TPEx timeout"),
        ]
        result = connector.fetch()
        assert len(result) == 1

    @patch("src.connectors.corporate._esg_base.create_tw_gov_session")
    def test_fetch_both_fail(self, mock_get, connector):
        """兩個端點都失敗時應拋出 ConnectorError。"""
        mock_get.return_value.get.side_effect = requests.RequestException("Network error")

        with pytest.raises(ConnectorError, match="皆請求失敗"):
            connector.fetch()

    def test_normalize_with_data(self, connector, sample_twse_data):
        df = connector.normalize(sample_twse_data)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert df["stock_id"].iloc[0] == "2330"
        assert df["company_name"].iloc[0] == "台積電"
        assert df["market"].iloc[0] == "TWSE"
        assert df["report_year"].iloc[0] == 2024  # 民國 113 → 西元 2024
        assert df["scope1_emissions"].iloc[0] == 1500000.0
        assert df["scope2_emissions"].iloc[0] == 8500000.0
        assert df["total_emissions"].iloc[0] == 10000000.0
        assert df["intensity"].iloc[0] == 4.5
        assert df["base_year"].iloc[0] == "2020"
        assert df["verification_status"].iloc[0] == "已取得第三方查證"

    def test_normalize_empty_returns_empty_df(self, connector):
        """空陣列應回傳具有正確欄位的空 DataFrame。"""
        df = connector.normalize([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "stock_id" in df.columns
        assert "scope1_emissions" in df.columns
        assert "verification_status" in df.columns

    def test_normalize_expected_columns(self, connector, sample_twse_data):
        df = connector.normalize(sample_twse_data)
        expected = [
            "stock_id", "company_name", "market", "report_year",
            "scope1_emissions", "scope2_emissions", "total_emissions",
            "intensity", "base_year", "verification_status",
        ]
        assert list(df.columns) == expected

    def test_health_check_params(self, connector):
        assert connector._health_check_params() == {}


class TestHelpers:
    def test_safe_numeric_valid(self):
        assert _safe_numeric("42000") == 42000.0

    def test_safe_numeric_with_commas(self):
        assert _safe_numeric("1,500,000") == 1500000.0

    def test_safe_numeric_none(self):
        assert _safe_numeric(None) is None

    def test_safe_numeric_empty(self):
        assert _safe_numeric("") is None

    def test_safe_numeric_dash(self):
        assert _safe_numeric("-") is None

    def test_safe_pct_with_percent_sign(self):
        assert _safe_pct("19.00%") == 19.0

    def test_safe_pct_without_sign(self):
        assert _safe_pct("85.2") == 85.2

    def test_safe_pct_none(self):
        assert _safe_pct(None) is None

    def test_parse_roc_year(self):
        assert _parse_roc_year("113") == 2024

    def test_parse_roc_year_western(self):
        assert _parse_roc_year("2024") == 2024

    def test_parse_roc_year_empty(self):
        assert _parse_roc_year("") is None

    def test_parse_roc_year_none(self):
        assert _parse_roc_year(None) is None
