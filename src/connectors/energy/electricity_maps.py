"""Electricity Maps connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class ElectricityMapsConnector(BaseConnector):
    """Fetch carbon intensity data from Electricity Maps.

    Free tier endpoint: https://api.electricitymaps.com/free-tier/carbon-intensity/latest
    Commercial endpoint: https://api.electricitymaps.com/v3/carbon-intensity/latest

    Auth headers differ by tier:
    - Free tier: API key via ``X-BLOBR-KEY`` header.
    - Commercial (v3): API key via ``auth-token`` header.

    Set ELECTRICITY_MAPS_API_TIER=v3 to use the commercial endpoint.
    """

    FREE_TIER_URL = "https://api.electricitymaps.com/free-tier"
    COMMERCIAL_URL = "https://api.electricitymaps.com/v3"

    @property
    def name(self) -> str:
        return "electricity_maps"

    @property
    def domain(self) -> str:
        return "energy"

    @property
    def _api_tier(self) -> str:
        """Return the configured API tier ('free-tier' or 'v3')."""
        return getattr(self._settings, "electricity_maps_api_tier", "free-tier")

    @property
    def _base_url(self) -> str:
        """Return base URL based on configured API tier.

        Defaults to free-tier. Set ELECTRICITY_MAPS_API_TIER=v3 for commercial.
        """
        if self._api_tier == "v3":
            return self.COMMERCIAL_URL
        return self.FREE_TIER_URL

    def _build_auth_headers(self, api_key: str) -> dict[str, str]:
        """Build authentication headers based on API tier.

        Free tier uses ``X-BLOBR-KEY``, commercial uses ``auth-token``.
        """
        if self._api_tier == "v3":
            return {"auth-token": api_key}
        return {"X-BLOBR-KEY": api_key}

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

        url = f"{self._base_url}/carbon-intensity/{endpoint}"
        headers = self._build_auth_headers(api_key)
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
