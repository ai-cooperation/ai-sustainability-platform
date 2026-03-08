"""NOAA Climate Data Online (CDO) API connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class NOAACDOConnector(BaseConnector):
    """Fetch climate observation data from NOAA CDO API.

    Endpoint: https://www.ncei.noaa.gov/cdo-web/api/v2/data
    Auth: Token required (NOAA_CDO_TOKEN)
    Rate limit: 5 req/sec, 10,000/day
    """

    BASE_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2"

    @property
    def name(self) -> str:
        return "noaa_cdo"

    @property
    def domain(self) -> str:
        return "climate"

    def _get_token(self) -> str:
        """Get NOAA CDO API token from settings.

        Returns:
            API token string.

        Raises:
            ConnectorError: If token is not configured.
        """
        token = self._settings.noaa_cdo_token
        if not token:
            raise ConnectorError(
                f"{self.name}: NOAA CDO token not configured. "
                "Set NOAA_CDO_TOKEN in environment or .env file."
            )
        return token

    def fetch(self, **params: Any) -> dict:
        """Fetch climate observation data from NOAA CDO.

        Args:
            datasetid: Dataset ID (default: GHCND - Global Historical
                Climatology Network Daily).
            startdate: Start date YYYY-MM-DD (required).
            enddate: End date YYYY-MM-DD (required).
            locationid: Location ID (e.g., 'FIPS:37' for North Carolina).
            datatypeid: Data type (e.g., 'TMAX', 'TMIN', 'PRCP').
            limit: Max records to return (default: 1000, max: 1000).
            offset: Pagination offset (default: 1).

        Returns:
            Raw JSON response with 'results' and 'metadata'.

        Raises:
            ConnectorError: If the API request fails.
        """
        token = self._get_token()

        if "startdate" not in params or "enddate" not in params:
            raise ConnectorError(
                f"{self.name}: 'startdate' and 'enddate' parameters are required"
            )

        request_params = {
            "datasetid": params.get("datasetid", "GHCND"),
            "startdate": params["startdate"],
            "enddate": params["enddate"],
            "limit": params.get("limit", 1000),
            "offset": params.get("offset", 1),
        }

        if "locationid" in params:
            request_params["locationid"] = params["locationid"]
        if "datatypeid" in params:
            request_params["datatypeid"] = params["datatypeid"]

        headers = {"token": token}
        url = f"{self.BASE_URL}/data"

        try:
            response = requests.get(
                url, params=request_params, headers=headers, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectorError(f"{self.name}: API request failed - {e}") from e

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert NOAA CDO response to standardized DataFrame.

        Args:
            raw_data: Raw API response with 'results' key.

        Returns:
            DataFrame with columns: timestamp, station, datatype, value.

        Raises:
            ConnectorError: If response structure is unexpected.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError(f"{self.name}: expected dict, got {type(raw_data).__name__}")

        results = raw_data.get("results")
        if not results:
            raise ConnectorError(f"{self.name}: no results in response")

        records = []
        for entry in results:
            records.append({
                "timestamp": pd.to_datetime(entry.get("date")),
                "station": entry.get("station", ""),
                "datatype": entry.get("datatype", ""),
                "value": entry.get("value"),
            })

        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {
            "datasetid": "GHCND",
            "startdate": "2024-01-01",
            "enddate": "2024-01-02",
            "limit": 1,
        }
