"""Environment domain connectors."""

from __future__ import annotations

from src.connectors.environment.aqicn import AQICNConnector
from src.connectors.environment.emissions_api import EmissionsAPIConnector
from src.connectors.environment.epa_envirofacts import EPAEnvirofactsConnector
from src.connectors.environment.epa_water_quality import EPAWaterQualityConnector
from src.connectors.environment.global_forest_watch import GlobalForestWatchConnector
from src.connectors.environment.open_meteo_air_quality import OpenMeteoAirQualityConnector
from src.connectors.environment.openaq import OpenAQConnector
from src.connectors.environment.tw_epa_aqi import TwEpaAqiConnector
from src.connectors.environment.tw_wra_reservoir import TwWraReservoirConnector

__all__ = [
    "AQICNConnector",
    "EmissionsAPIConnector",
    "EPAEnvirofactsConnector",
    "EPAWaterQualityConnector",
    "GlobalForestWatchConnector",
    "OpenMeteoAirQualityConnector",
    "OpenAQConnector",
    "TwEpaAqiConnector",
    "TwWraReservoirConnector",
]
