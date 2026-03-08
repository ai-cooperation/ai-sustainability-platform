"""US Energy Information Administration (EIA) connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class EIAConnector(BaseConnector):
    """Fetch energy data from the US EIA API v2.

    Endpoint: https://api.eia.gov/v2/
    Auth: API key required (EIA_API_KEY).
    """

    BASE_URL = "https://api.eia.gov/v2"

    @property
    def name(self) -> str:
        return "eia"

    @property
    def domain(self) -> str:
        return "energy"

    def fetch(self, **params: Any) -> dict:
        """Fetch data from the EIA API.

        Args:
            route: API route, e.g. 'electricity/rto/fuel-type-data'
                   (default 'electricity/rto/fuel-type-data').
            frequency: Data frequency: 'hourly', 'monthly', 'annual'.
            data: List of data columns to fetch.
            start: Start date (YYYY-MM).
            end: End date (YYYY-MM).
            sort: Sort configuration.
            length: Number of records to return (default 100).

        Returns:
            Raw JSON response dict.
        """
        api_key = self._settings.eia_api_key
        if not api_key:
            raise ConnectorError("EIA API key not configured (EIA_API_KEY)")

        route = params.get("route", "electricity/rto/fuel-type-data")
        url = f"{self.BASE_URL}/{route}/data/"

        request_params: dict[str, Any] = {"api_key": api_key}

        frequency = params.get("frequency")
        if frequency:
            request_params["frequency"] = frequency

        data_cols = params.get("data")
        if data_cols:
            request_params["data[]"] = data_cols

        start = params.get("start")
        if start:
            request_params["start"] = start

        end = params.get("end")
        if end:
            request_params["end"] = end

        length = params.get("length", 100)
        request_params["length"] = length

        try:
            response = requests.get(url, params=request_params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(f"EIA API request failed: {exc}") from exc

        data = response.json()

        # EIA v2 wraps errors in the response body
        resp = data.get("response", {})
        if "error" in resp:
            raise ConnectorError(f"EIA API error: {resp['error']}")

        return data

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw EIA response to a standardized DataFrame.

        Returns:
            DataFrame with a 'timestamp' column plus data-specific columns.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError("Expected dict response from EIA API")

        response = raw_data.get("response", {})
        records = response.get("data", [])

        if not records:
            raise ConnectorError("No data records in EIA response")

        df = pd.DataFrame(records)

        # EIA uses 'period' as the time column
        if "period" in df.columns:
            df["timestamp"] = pd.to_datetime(df["period"], utc=True)
        else:
            raise ConnectorError("Missing 'period' column in EIA response data")

        return df

    def _health_check_params(self) -> dict:
        """Minimal params: fetch a single record."""
        return {"route": "electricity/rto/fuel-type-data", "length": 1}
