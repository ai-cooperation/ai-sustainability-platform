"""Climate TRACE emissions connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class ClimateTRACEConnector(BaseConnector):
    """Fetch country-level emissions from the Climate TRACE API (beta).

    Endpoint: https://api.climatetrace.org/v6/country/emissions
    Auth: None required (beta access).
    """

    BASE_URL = "https://api.climatetrace.org/v6/country/emissions"

    @property
    def name(self) -> str:
        return "climate_trace"

    @property
    def domain(self) -> str:
        return "carbon"

    def fetch(self, **params: Any) -> dict | list:
        """Fetch country emissions data from Climate TRACE.

        Args:
            since: Start year (default 2015).
            to: End year (default 2023).
            countries: Comma-separated ISO country codes (optional).
            sectors: Comma-separated sector names (optional).

        Returns:
            Raw JSON response (list or dict).
        """
        request_params: dict[str, Any] = {
            "since": params.get("since", 2015),
            "to": params.get("to", 2023),
        }

        countries = params.get("countries")
        if countries:
            request_params["countries"] = countries

        sectors = params.get("sectors")
        if sectors:
            request_params["sectors"] = sectors

        try:
            response = requests.get(
                self.BASE_URL, params=request_params, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"Climate TRACE API request failed: {exc}"
            ) from exc

        return response.json()

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert Climate TRACE JSON response to a standardized DataFrame.

        Handles both list-of-records and dict-with-data-key formats.

        Returns:
            DataFrame with columns: timestamp, country, sector, subsector,
            co2, ch4, n2o, co2e.
        """
        records = _extract_records(raw_data)
        if not records:
            raise ConnectorError("No emission records in Climate TRACE response")

        rows: list[dict[str, Any]] = []
        for record in records:
            year = record.get("year")
            if year is None:
                continue
            rows.append(
                {
                    "year": int(year),
                    "country": record.get("country", ""),
                    "sector": record.get("sector", ""),
                    "subsector": record.get("subsector", ""),
                    "co2": record.get("co2"),
                    "ch4": record.get("ch4"),
                    "n2o": record.get("n2o"),
                    "co2e": record.get("co2e"),
                }
            )

        if not rows:
            raise ConnectorError(
                "No valid records with 'year' field in Climate TRACE data"
            )

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["year"].astype(int), format="%Y")

        return df.reset_index(drop=True)

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {"since": 2022, "to": 2022}


def _extract_records(raw_data: dict | list) -> list:
    """Extract a list of record dicts from the API response."""
    if isinstance(raw_data, list):
        return raw_data
    if isinstance(raw_data, dict):
        # Try common wrapper keys
        for key in ("data", "emissions", "results"):
            if key in raw_data and isinstance(raw_data[key], list):
                return raw_data[key]
        # If the dict itself looks like a single record, wrap it
        if "year" in raw_data:
            return [raw_data]
    return []
