"""TWSE/TPEx ESG 能源管理連接器（t187ap46 主題 2）。

資料來源：證交所＋櫃買中心結構化 ESG 資料
端點：TWSE _L_2 / TPEx _O_2
更新頻率：每年中旬（非申報季回傳空陣列為正常）
"""

from __future__ import annotations

from src.connectors.corporate._esg_base import TWSEEsgBaseConnector


class TWSEEsgEnergyConnector(TWSEEsgBaseConnector):
    """能源管理（Energy Management）連接器。

    涵蓋總能源消耗量、再生能源使用量及佔比、
    電力與燃料消耗等資訊，對應 GRI 302。
    """

    @property
    def name(self) -> str:
        return "twse_esg_energy"

    @property
    def topic_id(self) -> str:
        return "2"

    @property
    def column_map(self) -> dict[str, str]:
        return {
            "總能源消耗量(GJ)": "total_energy_consumption",
            "再生能源使用量(GJ)": "renewable_energy",
            "再生能源使用比率(%)": "renewable_pct",
            "用電量(度)": "electricity_consumption",
            "燃料消耗量(GJ)": "fuel_consumption",
        }
