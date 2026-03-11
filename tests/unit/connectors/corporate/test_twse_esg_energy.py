"""Tests for TWSEEsgEnergyConnector（能源管理連接器）。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.corporate.twse_esg_energy import TWSEEsgEnergyConnector


@pytest.fixture
def connector():
    with patch("src.connectors.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        return TWSEEsgEnergyConnector()


@pytest.fixture
def sample_data():
    return [
        {
            "報告年度": "113",
            "公司代號": "2330",
            "公司名稱": "台積電",
            "總能源消耗量(GJ)": "52000000",
            "再生能源使用量(GJ)": "5200000",
            "再生能源使用比率(%)": "10.0%",
            "用電量(度)": "18000000000",
            "燃料消耗量(GJ)": "2000000",
            "_market": "TWSE",
        },
    ]


class TestTWSEEsgEnergyConnector:
    def test_name(self, connector):
        assert connector.name == "twse_esg_energy"

    def test_domain(self, connector):
        assert connector.domain == "corporate"

    def test_topic_id(self, connector):
        assert connector.topic_id == "2"

    def test_normalize_with_data(self, connector, sample_data):
        df = connector.normalize(sample_data)

        assert len(df) == 1
        assert df["stock_id"].iloc[0] == "2330"
        assert df["total_energy_consumption"].iloc[0] == 52000000.0
        assert df["renewable_energy"].iloc[0] == 5200000.0
        assert df["renewable_pct"].iloc[0] == 10.0
        assert df["electricity_consumption"].iloc[0] == 18000000000.0
        assert df["fuel_consumption"].iloc[0] == 2000000.0

    def test_normalize_empty(self, connector):
        df = connector.normalize([])

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "total_energy_consumption" in df.columns
        assert "renewable_pct" in df.columns

    def test_normalize_expected_columns(self, connector, sample_data):
        df = connector.normalize(sample_data)
        expected = [
            "stock_id", "company_name", "market", "report_year",
            "total_energy_consumption", "renewable_energy",
            "renewable_pct", "electricity_consumption", "fuel_consumption",
        ]
        assert list(df.columns) == expected
