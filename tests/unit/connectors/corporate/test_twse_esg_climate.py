"""Tests for TWSEEsgClimateConnector（氣候相關議題連接器）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.corporate.twse_esg_climate import TWSEEsgClimateConnector


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return TWSEEsgClimateConnector()


@pytest.fixture
def sample_data():
    return [
        {
            "報告年度": "113",
            "公司代號": "2330",
            "公司名稱": "台積電",
            "氣候風險評估": "已完成情境分析",
            "TCFD揭露情形": "完整揭露四大支柱",
            "碳減量目標": "2030年減量30%（基準年2020）",
            "_market": "TWSE",
        },
        {
            "報告年度": "113",
            "公司代號": "3711",
            "公司名稱": "日月光投控",
            "氣候風險評估": "已辨識實體與轉型風險",
            "TCFD揭露情形": "部分揭露",
            "碳減量目標": "2050年淨零排放",
            "_market": "TWSE",
        },
    ]


class TestTWSEEsgClimateConnector:
    def test_name(self, connector):
        assert connector.name == "twse_esg_climate"

    def test_domain(self, connector):
        assert connector.domain == "corporate"

    def test_topic_id(self, connector):
        assert connector.topic_id == "8"

    def test_normalize_with_data(self, connector, sample_data):
        df = connector.normalize(sample_data)

        assert len(df) == 2
        assert df["stock_id"].iloc[0] == "2330"
        assert df["company_name"].iloc[0] == "台積電"
        assert df["report_year"].iloc[0] == 2024
        assert df["climate_risk_assessment"].iloc[0] == "已完成情境分析"
        assert df["tcfd_disclosure"].iloc[0] == "完整揭露四大支柱"
        assert df["carbon_reduction_target"].iloc[0] == "2030年減量30%（基準年2020）"

    def test_normalize_empty(self, connector):
        df = connector.normalize([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "climate_risk_assessment" in df.columns
        assert "tcfd_disclosure" in df.columns
        assert "carbon_reduction_target" in df.columns

    def test_normalize_expected_columns(self, connector, sample_data):
        df = connector.normalize(sample_data)
        expected = [
            "stock_id", "company_name", "market", "report_year",
            "climate_risk_assessment", "tcfd_disclosure",
            "carbon_reduction_target",
        ]
        assert list(df.columns) == expected

    def test_normalize_text_fields_preserved(self, connector, sample_data):
        """氣候連接器的欄位多為文字描述，應原樣保留。"""
        df = connector.normalize(sample_data)
        assert df["carbon_reduction_target"].iloc[1] == "2050年淨零排放"
