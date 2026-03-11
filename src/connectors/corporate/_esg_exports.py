"""ESG 連接器匯出清單 — 供 __init__.py 合併用。"""

from __future__ import annotations

from src.connectors.corporate.twse_esg_climate import TWSEEsgClimateConnector
from src.connectors.corporate.twse_esg_energy import TWSEEsgEnergyConnector
from src.connectors.corporate.twse_esg_ghg import TWSEEsgGhgConnector
from src.connectors.corporate.twse_esg_waste import TWSEEsgWasteConnector
from src.connectors.corporate.twse_esg_water import TWSEEsgWaterConnector

ESG_CONNECTORS = [
    TWSEEsgGhgConnector,
    TWSEEsgEnergyConnector,
    TWSEEsgWaterConnector,
    TWSEEsgWasteConnector,
    TWSEEsgClimateConnector,
]

__all__ = [
    "TWSEEsgGhgConnector",
    "TWSEEsgEnergyConnector",
    "TWSEEsgWaterConnector",
    "TWSEEsgWasteConnector",
    "TWSEEsgClimateConnector",
    "ESG_CONNECTORS",
]
