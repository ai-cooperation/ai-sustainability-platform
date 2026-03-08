"""Open-Meteo Climate API connector for historical climate projections."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class OpenMeteoClimateConnector(BaseConnector):
    """Fetch climate projection data from Open-Meteo Climate API.

    Endpoint: https://climate-api.open-meteo.com/v1/climate
    Auth: None (free)
    """

    BASE_URL = "https://climate-api.open-meteo.com/v1/climate"

    @property
    def name(self) -> str:
        return "open_meteo_climate"

    @property
    def domain(self) -> str:
        return "climate"

    def fetch(self, **params: Any) -> dict:
        """Fetch climate projection data.

        Args:
            latitude: Location latitude (default: 25.03).
            longitude: Location longitude (default: 121.57).
            start_date: Start date YYYY-MM-DD (default: 2020-01-01).
            end_date: End date YYYY-MM-DD (default: 2050-12-31).
            models: Climate model (default: EC_Earth3P_HR).
            daily: Daily variables to retrieve.

        Returns:
            Raw JSON response.

        Raises:
            ConnectorError: If the API request fails.
        """
        request_params = {
            "latitude": params.get("latitude", 25.03),
            "longitude": params.get("longitude", 121.57),
            "start_date": params.get("start_date", "2020-01-01"),
            "end_date": params.get("end_date", "2050-12-31"),
            "models": params.get("models", "EC_Earth3P_HR"),
            "daily": params.get(
                "daily",
                "temperature_2m_max,temperature_2m_min,precipitation_sum",
            ),
        }

        try:
            response = requests.get(self.BASE_URL, params=request_params, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectorError(f"{self.name}: API request failed - {e}") from e

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert climate projection response to standardized DataFrame.

        Args:
            raw_data: Raw API response with 'daily' key.

        Returns:
            DataFrame with columns: timestamp, lat, lon, temperature_max,
            temperature_min, precipitation.

        Raises:
            ConnectorError: If response structure is unexpected.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError(f"{self.name}: expected dict, got {type(raw_data).__name__}")

        daily = raw_data.get("daily")
        if not daily:
            raise ConnectorError(f"{self.name}: missing 'daily' key in response")

        time_values = daily.get("time", [])
        if not time_values:
            raise ConnectorError(f"{self.name}: no time values in daily data")

        lat = raw_data.get("latitude", 0.0)
        lon = raw_data.get("longitude", 0.0)

        df = pd.DataFrame({
            "timestamp": pd.to_datetime(time_values),
            "lat": lat,
            "lon": lon,
            "temperature_max": daily.get("temperature_2m_max", [None] * len(time_values)),
            "temperature_min": daily.get("temperature_2m_min", [None] * len(time_values)),
            "precipitation": daily.get("precipitation_sum", [None] * len(time_values)),
        })

        return df

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {
            "latitude": 0.0,
            "longitude": 0.0,
            "start_date": "2020-01-01",
            "end_date": "2020-01-02",
        }
