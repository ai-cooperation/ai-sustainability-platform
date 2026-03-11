"""Tests for TWSEEsgWaterConnector（水資源管理連接器）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.corporate.twse_esg_water import TWSEEsgWaterConnector


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return TWSEEsgWaterConnector()


@pytest.fixture
def sample_data():
    return [
        {
            "報告年度": "113",
            "公司代號": "2303",
            "公司名稱": "聯電",
            "總取水量(公秉)": "35000000",
            "回收水量(公秉)": "28000000",
            "回收水率(%)": "80.0%",
            "_market": "TWSE",
        },
        {
            "報告年度": "113",
            "公司代號": "6488",
            "公司名稱": "環球晶",
            "總取水量(公秉)": "5000000",
            "回收水量(公秉)": "2500000",
            "回收水率(%)": "50.0%",
            "_market": "TPEx",
        },
    ]


class TestTWSEEsgWaterConnector:
    def test_name(self, connector):
        assert connector.name == "twse_esg_water"

    def test_domain(self, connector):
        assert connector.domain == "corporate"

    def test_topic_id(self, connector):
        assert connector.topic_id == "3"

    def test_normalize_with_data(self, connector, sample_data):
        df = connector.normalize(sample_data)

        assert len(df) == 2
        assert df["stock_id"].iloc[0] == "2303"
        assert df["total_water_withdrawal"].iloc[0] == 35000000.0
        assert df["water_recycled"].iloc[0] == 28000000.0
        assert df["water_recycled_pct"].iloc[0] == 80.0
        # 驗證 TPEx 資料
        assert df["market"].iloc[1] == "TPEx"
        assert df["stock_id"].iloc[1] == "6488"

    def test_normalize_empty(self, connector):
        df = connector.normalize([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "total_water_withdrawal" in df.columns
        assert "water_recycled_pct" in df.columns

    def test_normalize_expected_columns(self, connector, sample_data):
        df = connector.normalize(sample_data)
        expected = [
            "stock_id", "company_name", "market", "report_year",
            "total_water_withdrawal", "water_recycled", "water_recycled_pct",
        ]
        assert list(df.columns) == expected
