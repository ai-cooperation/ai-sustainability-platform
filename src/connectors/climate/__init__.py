"""Climate domain connectors."""

from __future__ import annotations

from src.connectors.climate.copernicus_cds import CopernicusCDSConnector
from src.connectors.climate.noaa_cdo import NOAACDOConnector
from src.connectors.climate.noaa_ghg import NOAAGHGConnector
from src.connectors.climate.open_meteo_climate import OpenMeteoClimateConnector
from src.connectors.climate.open_meteo_weather import OpenMeteoWeatherConnector
from src.connectors.climate.world_bank_climate import WorldBankClimateConnector

__all__ = [
    "CopernicusCDSConnector",
    "NOAACDOConnector",
    "NOAAGHGConnector",
    "OpenMeteoClimateConnector",
    "OpenMeteoWeatherConnector",
    "WorldBankClimateConnector",
]
