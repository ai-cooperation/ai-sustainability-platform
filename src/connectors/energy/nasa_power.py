"""NASA POWER API connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class NASAPowerConnector(BaseConnector):
    """Fetch solar and meteorological data from NASA POWER.

    Endpoint: https://power.larc.nasa.gov/api/temporal/daily/point
    Auth: None required.
    """

    BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

    @property
    def name(self) -> str:
        return "nasa_power"

    @property
    def domain(self) -> str:
        return "energy"

    def fetch(self, **params: Any) -> dict:
        """Fetch daily solar radiation and temperature data.

        Args:
            latitude: Location latitude (default 52.52).
            longitude: Location longitude (default 13.41).
            start: Start date as YYYYMMDD (default '20240101').
            end: End date as YYYYMMDD (default '20240107').
            parameters: Comma-separated parameter names.

        Returns:
            Raw JSON response dict.
        """
        request_params = {
            "parameters": params.get("parameters", "ALLSKY_SFC_SW_DWN,T2M"),
            "community": params.get("community", "RE"),
            "longitude": params.get("longitude", 13.41),
            "latitude": params.get("latitude", 52.52),
            "start": params.get("start", "20240101"),
            "end": params.get("end", "20240107"),
            "format": "JSON",
        }

        try:
            response = requests.get(self.BASE_URL, params=request_params, timeout=60)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(f"NASA POWER API request failed: {exc}") from exc

        return response.json()

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw NASA POWER response to a standardized DataFrame.

        Returns:
            DataFrame with columns: timestamp, latitude, longitude,
            solar_radiation, temperature.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError("Expected dict response from NASA POWER API")

        properties = raw_data.get("properties", {})
        parameter_data = properties.get("parameter", {})
        geometry = raw_data.get("geometry", {})
        coords = geometry.get("coordinates", [None, None])

        solar = parameter_data.get("ALLSKY_SFC_SW_DWN", {})
        temp = parameter_data.get("T2M", {})

        if not solar and not temp:
            raise ConnectorError("No parameter data found in NASA POWER response")

        # Use whichever parameter has data to get date keys
        date_keys = list(solar.keys()) if solar else list(temp.keys())

        rows = []
        for date_str in date_keys:
            rows.append(
                {
                    "timestamp": pd.to_datetime(date_str, format="%Y%m%d"),
                    "latitude": coords[1] if len(coords) > 1 else None,
                    "longitude": coords[0] if len(coords) > 0 else None,
                    "solar_radiation": solar.get(date_str),
                    "temperature": temp.get(date_str),
                }
            )

        return pd.DataFrame(rows)

    def _health_check_params(self) -> dict:
        """Minimal params: fetch a single day."""
        return {
            "latitude": 0,
            "longitude": 0,
            "start": "20240101",
            "end": "20240101",
        }
