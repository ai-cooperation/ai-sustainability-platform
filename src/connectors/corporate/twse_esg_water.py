"""TWSE/TPEx ESG 水資源管理連接器（t187ap46 主題 3）。

資料來源：證交所＋櫃買中心結構化 ESG 資料
端點：TWSE _L_3 / TPEx _O_3
更新頻率：每年中旬（非申報季回傳空陣列為正常）
"""

from __future__ import annotations

from src.connectors.corporate._esg_base import TWSEEsgBaseConnector


class TWSEEsgWaterConnector(TWSEEsgBaseConnector):
    """水資源管理（Water Resource Management）連接器。

    涵蓋總取水量、回收水量及回收比率等資訊，對應 GRI 303。
    """

    @property
    def name(self) -> str:
        return "twse_esg_water"

    @property
    def topic_id(self) -> str:
        return "3"

    @property
    def column_map(self) -> dict[str, str]:
        return {
            "總取水量(公秉)": "total_water_withdrawal",
            "回收水量(公秉)": "water_recycled",
            "回收水率(%)": "water_recycled_pct",
        }
