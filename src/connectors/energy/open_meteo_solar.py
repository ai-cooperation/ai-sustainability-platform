"""Open-Meteo Solar Radiation connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class OpenMeteoSolarConnector(BaseConnector):
    """Fetch solar radiation data from the Open-Meteo API.

    Endpoint: https://api.open-meteo.com/v1/forecast
    Auth: None required.
    Rate limit: 10,000 requests/day.
    """

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    @property
    def name(self) -> str:
        return "open_meteo_solar"

    @property
    def domain(self) -> str:
        return "energy"

    def fetch(self, **params: Any) -> dict:
        """Fetch solar radiation data for a given location.

        Args:
            latitude: Location latitude (default 52.52).
            longitude: Location longitude (default 13.41).
            hourly: Comma-separated hourly variables.

        Returns:
            Raw JSON response dict.
        """
        latitude = params.get("latitude", 52.52)
        longitude = params.get("longitude", 13.41)
        hourly = params.get(
            "hourly",
            "shortwave_radiation,direct_radiation,diffuse_radiation",
        )

        request_params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": hourly,
        }

        try:
            response = requests.get(self.BASE_URL, params=request_params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"Open-Meteo Solar API request failed: {exc}"
            ) from exc

        return response.json()

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw Open-Meteo response to a standardized DataFrame.

        Returns:
            DataFrame with columns: timestamp, latitude, longitude,
            shortwave_radiation, direct_radiation, diffuse_radiation.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError("Expected dict response from Open-Meteo Solar API")

        hourly = raw_data.get("hourly")
        if not hourly or "time" not in hourly:
            raise ConnectorError("Missing 'hourly' data in Open-Meteo Solar response")

        df = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(hourly["time"]),
                "latitude": raw_data.get("latitude"),
                "longitude": raw_data.get("longitude"),
                "shortwave_radiation": hourly.get("shortwave_radiation"),
                "direct_radiation": hourly.get("direct_radiation"),
                "diffuse_radiation": hourly.get("diffuse_radiation"),
            }
        )
        return df

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {"latitude": 0, "longitude": 0}
