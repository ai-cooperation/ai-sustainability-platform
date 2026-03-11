"""TWSE/TPEx ESG 廢棄物管理連接器（t187ap46 主題 4）。

資料來源：證交所＋櫃買中心結構化 ESG 資料
端點：TWSE _L_4 / TPEx _O_4
更新頻率：每年中旬（非申報季回傳空陣列為正常）
"""

from __future__ import annotations

from src.connectors.corporate._esg_base import TWSEEsgBaseConnector


class TWSEEsgWasteConnector(TWSEEsgBaseConnector):
    """廢棄物管理（Waste Management）連接器。

    涵蓋總廢棄物產生量、有害廢棄物、回收量及回收比率，
    對應 GRI 306。
    """

    @property
    def name(self) -> str:
        return "twse_esg_waste"

    @property
    def topic_id(self) -> str:
        return "4"

    @property
    def column_map(self) -> dict[str, str]:
        return {
            "廢棄物總量(公噸)": "total_waste",
            "有害廢棄物(公噸)": "hazardous_waste",
            "回收廢棄物(公噸)": "recycled_waste",
            "回收率(%)": "recycled_pct",
        }
