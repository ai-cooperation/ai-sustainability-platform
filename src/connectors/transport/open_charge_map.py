"""OpenChargeMap EV charging station connector."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class OpenChargeMapConnector(BaseConnector):
    """Fetch EV charging station data from the OpenChargeMap API.

    Endpoint: https://api.openchargemap.io/v3/poi/
    Auth: Optional API key.
    """

    BASE_URL = "https://api.openchargemap.io/v3/poi/"

    @property
    def name(self) -> str:
        return "open_charge_map"

    @property
    def domain(self) -> str:
        return "transport"

    def fetch(self, **params: Any) -> list:
        """Fetch EV charging station POI data.

        Args:
            countrycode: ISO country code (default "US").
            maxresults: Maximum results to return (default 100).

        Returns:
            Raw JSON response as a list of station dicts.
        """
        countrycode = params.get("countrycode", "US")
        maxresults = params.get("maxresults", 100)

        request_params: dict[str, Any] = {
            "output": "json",
            "countrycode": countrycode,
            "maxresults": maxresults,
        }

        headers: dict[str, str] = {}
        api_key = self._settings.open_charge_map_api_key
        if api_key:
            headers["X-API-Key"] = api_key

        try:
            response = requests.get(
                self.BASE_URL, params=request_params, headers=headers, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"OpenChargeMap API request failed: {exc}"
            ) from exc

        data = response.json()
        if not isinstance(data, list):
            raise ConnectorError(
                "OpenChargeMap API returned unexpected format: expected a list"
            )

        return data

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw OpenChargeMap response to a standardized DataFrame.

        Returns:
            DataFrame with columns: id, title, latitude, longitude,
            country, power_kw, connector_type, operator, timestamp.
        """
        if not isinstance(raw_data, list):
            raise ConnectorError(
                "Expected list response from OpenChargeMap API"
            )

        records = []
        for station in raw_data:
            address = station.get("AddressInfo") or {}
            connections = station.get("Connections") or []
            operator_info = station.get("OperatorInfo") or {}

            power_kw = None
            connector_type = None
            if connections:
                first_conn = connections[0]
                power_kw = first_conn.get("PowerKW")
                conn_type_info = first_conn.get("ConnectionType") or {}
                connector_type = conn_type_info.get("Title")

            records.append(
                {
                    "id": station.get("ID"),
                    "title": address.get("Title", ""),
                    "latitude": address.get("Latitude"),
                    "longitude": address.get("Longitude"),
                    "country": (address.get("Country") or {}).get("Title", ""),
                    "power_kw": power_kw,
                    "connector_type": connector_type,
                    "operator": operator_info.get("Title", ""),
                }
            )

        df = pd.DataFrame(records)
        df["timestamp"] = pd.Timestamp(datetime.now(tz=UTC))
        return df

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {"countrycode": "US", "maxresults": 1}
