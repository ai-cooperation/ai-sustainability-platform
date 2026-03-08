"""Energy domain connectors."""

from __future__ import annotations

from src.connectors.energy.carbon_intensity_uk import CarbonIntensityUKConnector
from src.connectors.energy.eia import EIAConnector
from src.connectors.energy.electricity_maps import ElectricityMapsConnector
from src.connectors.energy.nasa_power import NASAPowerConnector
from src.connectors.energy.nrel import NRELConnector
from src.connectors.energy.open_meteo_solar import OpenMeteoSolarConnector
from src.connectors.energy.open_power_system import OpenPowerSystemConnector

__all__ = [
    "CarbonIntensityUKConnector",
    "EIAConnector",
    "ElectricityMapsConnector",
    "NASAPowerConnector",
    "NRELConnector",
    "OpenMeteoSolarConnector",
    "OpenPowerSystemConnector",
]
