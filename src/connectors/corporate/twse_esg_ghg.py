"""TWSE/TPEx ESG 溫室氣體排放連接器（t187ap46 主題 1）。

資料來源：證交所＋櫃買中心結構化 ESG 資料
端點：TWSE _L_1 / TPEx _O_1
更新頻率：每年中旬（非申報季回傳空陣列為正常）
"""

from __future__ import annotations

from src.connectors.corporate._esg_base import TWSEEsgBaseConnector


class TWSEEsgGhgConnector(TWSEEsgBaseConnector):
    """溫室氣體排放（Greenhouse Gas Emissions）連接器。

    涵蓋範疇一（直接排放）、範疇二（間接排放）及排放密集度等資訊，
    對應 GRI 305 / TCFD 指標。
    """

    @property
    def name(self) -> str:
        return "twse_esg_ghg"

    @property
    def topic_id(self) -> str:
        return "1"

    @property
    def column_map(self) -> dict[str, str]:
        return {
            "範疇一排放量(公噸CO2e)": "scope1_emissions",
            "範疇二排放量(公噸CO2e)": "scope2_emissions",
            "排放總量(公噸CO2e)": "total_emissions",
            "排放密集度(公噸CO2e/百萬元營收)": "intensity",
            "基準年": "base_year",
            "確信/查證情形": "verification_status",
        }
