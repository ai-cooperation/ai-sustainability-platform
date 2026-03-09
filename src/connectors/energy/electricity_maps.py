"""Electricity Maps connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class ElectricityMapsConnector(BaseConnector):
    """Fetch carbon intensity data from Electricity Maps.

    Endpoint: https://api.electricitymaps.com/v3/carbon-intensity/latest
    Auth: API key via ``auth-token`` header.
    """

    BASE_URL = "https://api.electricitymaps.com/v3"

    @property
    def name(self) -> str:
        return "electricity_maps"

    @property
    def domain(self) -> str:
        return "energy"

    def fetch(self, **params: Any) -> dict:
        """Fetch carbon intensity data for a zone.

        Args:
            zone: Electricity zone code (default 'DE').
            endpoint: One of 'latest', 'history' (default 'latest').

        Returns:
            Raw JSON response dict.
        """
        api_key = self._settings.electricity_maps_api_key
        if not api_key:
            raise ConnectorError(
                "Electricity Maps API key not configured (ELECTRICITY_MAPS_API_KEY)"
            )

        zone = params.get("zone", "DE")
        endpoint = params.get("endpoint", "latest")

        url = f"{self.BASE_URL}/carbon-intensity/{endpoint}"
        headers = {"auth-token": api_key}
        request_params = {"zone": zone}

        try:
            response = requests.get(
                url, headers=headers, params=request_params, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"Electricity Maps API request failed: {exc}"
            ) from exc

        return response.json()

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw Electricity Maps response to a standardized DataFrame.

        Returns:
            DataFrame with columns: timestamp, zone, carbon_intensity,
            fossil_fuel_percentage.
        """
        if isinstance(raw_data, dict):
            items = [raw_data]
        elif isinstance(raw_data, list):
            items = raw_data
        else:
            raise ConnectorError("Unexpected response format from Electricity Maps API")

        rows = []
        for item in items:
            rows.append(
                {
                    "timestamp": pd.to_datetime(
                        item.get("datetime") or item.get("updatedAt")
                    ),
                    "zone": item.get("zone", ""),
                    "carbon_intensity": item.get("carbonIntensity"),
                    "fossil_fuel_percentage": item.get("fossilFuelPercentage"),
                }
            )

        if not rows:
            raise ConnectorError("No data in Electricity Maps response")

        return pd.DataFrame(rows)

    def _health_check_params(self) -> dict:
        """Minimal params: fetch latest for a single zone."""
        return {"zone": "DE", "endpoint": "latest"}
