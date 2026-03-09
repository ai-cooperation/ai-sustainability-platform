"""Open-Meteo Air Quality API connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class OpenMeteoAirQualityConnector(BaseConnector):
    """Connector for Open-Meteo Air Quality API.

    Endpoint: https://air-quality-api.open-meteo.com/v1/air-quality
    Auth: None
    Rate limit: 10,000/day
    """

    BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

    DEFAULT_HOURLY = (
        "pm2_5,pm10,carbon_monoxide,nitrogen_dioxide,ozone,european_aqi"
    )

    @property
    def name(self) -> str:
        return "open_meteo_air_quality"

    @property
    def domain(self) -> str:
        return "environment"

    def fetch(self, **params: Any) -> dict:
        """Fetch air quality data from Open-Meteo.

        Args:
            latitude: Latitude of the location.
            longitude: Longitude of the location.
            hourly: Comma-separated hourly variables (optional).

        Returns:
            Raw JSON response as dict.

        Raises:
            ConnectorError: If the API call fails.
        """
        query = {
            "latitude": params.get("latitude", 25.03),
            "longitude": params.get("longitude", 121.57),
            "hourly": params.get("hourly", self.DEFAULT_HOURLY),
        }

        query["forecast_days"] = params.get("forecast_days", 7)

        try:
            response = requests.get(self.BASE_URL, params=query, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"{self.name}: API request failed - {exc}"
            ) from exc

        data = response.json()
        if "hourly" not in data:
            raise ConnectorError(
                f"{self.name}: unexpected response format - missing 'hourly' key"
            )
        return data

    def normalize(self, raw_data: dict) -> pd.DataFrame:
        """Convert raw Open-Meteo air quality data to a DataFrame.

        Args:
            raw_data: Raw API response dict.

        Returns:
            DataFrame with columns: timestamp, latitude, longitude,
            pm2_5, pm10, co, no2, o3, aqi.
        """
        hourly = raw_data.get("hourly", {})
        if not hourly or "time" not in hourly:
            raise ConnectorError(
                f"{self.name}: no hourly data available in response"
            )

        df = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(hourly["time"]),
                "latitude": raw_data.get("latitude"),
                "longitude": raw_data.get("longitude"),
                "pm2_5": hourly.get("pm2_5"),
                "pm10": hourly.get("pm10"),
                "co": hourly.get("carbon_monoxide"),
                "no2": hourly.get("nitrogen_dioxide"),
                "o3": hourly.get("ozone"),
                "aqi": hourly.get("european_aqi"),
            }
        )
        return df

    def _health_check_params(self) -> dict:
        """Minimal params for health check.

        Request only 1 day of a single variable to minimize response size
        and avoid timeouts on the free Open-Meteo API.
        """
        return {
            "latitude": 48.85,
            "longitude": 2.35,
            "hourly": "pm2_5",
            "forecast_days": 1,
        }
