"""TWSE/TPEx ESG 氣候相關議題連接器（t187ap46 主題 8）。

資料來源：證交所＋櫃買中心結構化 ESG 資料
端點：TWSE _L_8 / TPEx _O_8
更新頻率：每年中旬（非申報季回傳空陣列為正常）
"""

from __future__ import annotations

from src.connectors.corporate._esg_base import TWSEEsgBaseConnector


class TWSEEsgClimateConnector(TWSEEsgBaseConnector):
    """氣候相關議題（Climate-related Issues）連接器。

    涵蓋氣候風險評估、TCFD 揭露情形及碳減量目標，
    對應 TCFD 建議框架。
    """

    @property
    def name(self) -> str:
        return "twse_esg_climate"

    @property
    def topic_id(self) -> str:
        return "8"

    @property
    def column_map(self) -> dict[str, str]:
        return {
            "氣候風險評估": "climate_risk_assessment",
            "TCFD揭露情形": "tcfd_disclosure",
            "碳減量目標": "carbon_reduction_target",
        }
