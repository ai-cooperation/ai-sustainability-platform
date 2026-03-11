"""Tests for TWSEEsgWasteConnector（廢棄物管理連接器）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.corporate.twse_esg_waste import TWSEEsgWasteConnector


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return TWSEEsgWasteConnector()


@pytest.fixture
def sample_data():
    return [
        {
            "報告年度": "113",
            "公司代號": "1301",
            "公司名稱": "台塑",
            "廢棄物總量(公噸)": "850000",
            "有害廢棄物(公噸)": "12000",
            "回收廢棄物(公噸)": "680000",
            "回收率(%)": "80.0%",
            "_market": "TWSE",
        },
    ]


class TestTWSEEsgWasteConnector:
    def test_name(self, connector):
        assert connector.name == "twse_esg_waste"

    def test_domain(self, connector):
        assert connector.domain == "corporate"

    def test_topic_id(self, connector):
        assert connector.topic_id == "4"

    def test_normalize_with_data(self, connector, sample_data):
        df = connector.normalize(sample_data)

        assert len(df) == 1
        assert df["stock_id"].iloc[0] == "1301"
        assert df["total_waste"].iloc[0] == 850000.0
        assert df["hazardous_waste"].iloc[0] == 12000.0
        assert df["recycled_waste"].iloc[0] == 680000.0
        assert df["recycled_pct"].iloc[0] == 80.0

    def test_normalize_empty(self, connector):
        df = connector.normalize([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "total_waste" in df.columns
        assert "hazardous_waste" in df.columns

    def test_normalize_expected_columns(self, connector, sample_data):
        df = connector.normalize(sample_data)
        expected = [
            "stock_id", "company_name", "market", "report_year",
            "total_waste", "hazardous_waste", "recycled_waste", "recycled_pct",
        ]
        assert list(df.columns) == expected

    def test_normalize_missing_fields(self, connector):
        """部分欄位缺失時應填入 None。"""
        data = [
            {
                "報告年度": "113",
                "公司代號": "1301",
                "公司名稱": "台塑",
                "廢棄物總量(公噸)": "850000",
                "_market": "TWSE",
            },
        ]
        df = connector.normalize(data)

        assert len(df) == 1
        assert df["total_waste"].iloc[0] == 850000.0
        assert df["hazardous_waste"].iloc[0] is None
        assert df["recycled_waste"].iloc[0] is None
        assert df["recycled_pct"].iloc[0] is None
