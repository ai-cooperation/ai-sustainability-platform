"""NREL Alternative Fuel Stations connector."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class NRELAltFuelConnector(BaseConnector):
    """Fetch alternative fuel station data from the NREL API.

    Endpoint: https://developer.nrel.gov/api/alt-fuel-stations/v1.json
    Auth: API key required (NREL_API_KEY).
    """

    BASE_URL = "https://developer.nrel.gov/api/alt-fuel-stations/v1.json"

    @property
    def name(self) -> str:
        return "nrel_alt_fuel"

    @property
    def domain(self) -> str:
        return "transport"

    def fetch(self, **params: Any) -> dict:
        """Fetch alternative fuel station data.

        Args:
            fuel_type: Fuel type filter (default "ELEC").
            state: US state code (default "CA").
            limit: Maximum results (default 200).

        Returns:
            Raw JSON response dict.
        """
        api_key = self._settings.nrel_api_key
        if not api_key:
            raise ConnectorError(
                "NREL API key is required. Set NREL_API_KEY in environment."
            )

        fuel_type = params.get("fuel_type", "ELEC")
        state = params.get("state", "CA")
        limit = params.get("limit", 200)

        request_params: dict[str, Any] = {
            "api_key": api_key,
            "fuel_type": fuel_type,
            "state": state,
            "limit": limit,
        }

        try:
            response = requests.get(
                self.BASE_URL, params=request_params, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"NREL Alt Fuel API request failed: {exc}"
            ) from exc

        data = response.json()
        if not isinstance(data, dict):
            raise ConnectorError(
                "NREL Alt Fuel API returned unexpected format: expected a dict"
            )

        return data

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw NREL response to a standardized DataFrame.

        Returns:
            DataFrame with columns: id, station_name, latitude, longitude,
            fuel_type, city, state, access_code, timestamp.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError(
                "Expected dict response from NREL Alt Fuel API"
            )

        stations = raw_data.get("alt_fuel_stations")
        if stations is None:
            raise ConnectorError(
                "Missing 'alt_fuel_stations' in NREL Alt Fuel response"
            )

        records = []
        for station in stations:
            records.append(
                {
                    "id": station.get("id"),
                    "station_name": station.get("station_name", ""),
                    "latitude": station.get("latitude"),
                    "longitude": station.get("longitude"),
                    "fuel_type": station.get("fuel_type_code", ""),
                    "city": station.get("city", ""),
                    "state": station.get("state", ""),
                    "access_code": station.get("access_code", ""),
                }
            )

        df = pd.DataFrame(records)
        df["timestamp"] = pd.Timestamp(datetime.now(tz=UTC))
        return df

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {"fuel_type": "ELEC", "state": "CA", "limit": 1}
