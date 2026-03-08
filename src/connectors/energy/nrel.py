"""NREL Solar and Wind resource connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class NRELConnector(BaseConnector):
    """Fetch solar and wind resource data from NREL.

    Endpoint: https://developer.nrel.gov/api/solar/solar_resource/v1.json
    Auth: API key required (NREL_API_KEY).
    """

    SOLAR_URL = "https://developer.nrel.gov/api/solar/solar_resource/v1.json"

    @property
    def name(self) -> str:
        return "nrel"

    @property
    def domain(self) -> str:
        return "energy"

    def fetch(self, **params: Any) -> dict:
        """Fetch solar resource data from NREL.

        Args:
            latitude: Location latitude (default 40.0).
            longitude: Location longitude (default -105.0).

        Returns:
            Raw JSON response dict.
        """
        api_key = self._settings.nrel_api_key
        if not api_key:
            raise ConnectorError("NREL API key not configured (NREL_API_KEY)")

        request_params = {
            "api_key": api_key,
            "lat": params.get("latitude", 40.0),
            "lon": params.get("longitude", -105.0),
        }

        try:
            response = requests.get(self.SOLAR_URL, params=request_params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(f"NREL API request failed: {exc}") from exc

        data = response.json()

        # NREL returns errors in the response body
        errors = data.get("errors")
        if errors:
            raise ConnectorError(f"NREL API error: {errors}")

        return data

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw NREL solar resource response to a standardized DataFrame.

        The NREL solar resource endpoint returns monthly averages.

        Returns:
            DataFrame with columns: timestamp, latitude, longitude,
            ghi, dni, wind_speed.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError("Expected dict response from NREL API")

        outputs = raw_data.get("outputs", {})
        if not outputs:
            raise ConnectorError("No outputs found in NREL response")

        inputs = raw_data.get("inputs", {})
        lat = inputs.get("lat")
        lon = inputs.get("lon")

        avg_ghi = outputs.get("avg_ghi", {})
        avg_dni = outputs.get("avg_dni", {})

        # Monthly keys: 'jan', 'feb', ... 'dec' plus 'annual'
        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4,
            "may": 5, "jun": 6, "jul": 7, "aug": 8,
            "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }

        rows = []
        for month_name, month_num in month_map.items():
            rows.append(
                {
                    "timestamp": pd.Timestamp(year=2024, month=month_num, day=1),
                    "latitude": lat,
                    "longitude": lon,
                    "ghi": avg_ghi.get(month_name),
                    "dni": avg_dni.get(month_name),
                    "wind_speed": None,
                }
            )

        return pd.DataFrame(rows)

    def _health_check_params(self) -> dict:
        """Minimal params: fetch for a single point."""
        return {"latitude": 40.0, "longitude": -105.0}
