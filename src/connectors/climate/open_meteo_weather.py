"""Open-Meteo Weather API connector for current/forecast weather data."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class OpenMeteoWeatherConnector(BaseConnector):
    """Fetch weather forecast data from Open-Meteo API.

    Endpoint: https://api.open-meteo.com/v1/forecast
    Auth: None (free, 10,000 requests/day)
    """

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    @property
    def name(self) -> str:
        return "open_meteo_weather"

    @property
    def domain(self) -> str:
        return "climate"

    def fetch(self, **params: Any) -> dict:
        """Fetch weather forecast data.

        Args:
            latitude: Location latitude (default: 25.03 for Taipei).
            longitude: Location longitude (default: 121.57 for Taipei).
            hourly: Comma-separated hourly variables.

        Returns:
            Raw JSON response from Open-Meteo.

        Raises:
            ConnectorError: If the API request fails.
        """
        request_params = {
            "latitude": params.get("latitude", 25.03),
            "longitude": params.get("longitude", 121.57),
            "hourly": params.get(
                "hourly",
                "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            ),
        }

        if "forecast_days" in params:
            request_params["forecast_days"] = params["forecast_days"]

        try:
            response = requests.get(self.BASE_URL, params=request_params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectorError(f"{self.name}: API request failed - {e}") from e

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert Open-Meteo weather response to standardized DataFrame.

        Args:
            raw_data: Raw API response with 'hourly' key.

        Returns:
            DataFrame with columns: timestamp, lat, lon, temperature,
            humidity, precipitation, wind_speed.

        Raises:
            ConnectorError: If response structure is unexpected.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError(f"{self.name}: expected dict, got {type(raw_data).__name__}")

        hourly = raw_data.get("hourly")
        if not hourly:
            raise ConnectorError(f"{self.name}: missing 'hourly' key in response")

        time_values = hourly.get("time", [])
        if not time_values:
            raise ConnectorError(f"{self.name}: no time values in hourly data")

        lat = raw_data.get("latitude", 0.0)
        lon = raw_data.get("longitude", 0.0)

        df = pd.DataFrame({
            "timestamp": pd.to_datetime(time_values),
            "lat": lat,
            "lon": lon,
            "temperature": hourly.get("temperature_2m", [None] * len(time_values)),
            "humidity": hourly.get("relative_humidity_2m", [None] * len(time_values)),
            "precipitation": hourly.get("precipitation", [None] * len(time_values)),
            "wind_speed": hourly.get("wind_speed_10m", [None] * len(time_values)),
        })

        return df

    def _health_check_params(self) -> dict:
        """Minimal params for health check.

        Request only 1 day of a single variable to minimize response size
        and avoid timeouts on the free Open-Meteo API.
        """
        return {
            "latitude": 0.0,
            "longitude": 0.0,
            "hourly": "temperature_2m",
            "forecast_days": 1,
        }
