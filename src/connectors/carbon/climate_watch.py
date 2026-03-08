"""Climate Watch historical emissions connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class ClimateWatchConnector(BaseConnector):
    """Fetch historical emissions data from Climate Watch Data API.

    Endpoint: https://www.climatewatchdata.org/api/v1/data/historical_emissions
    Auth: None required.
    """

    BASE_URL = "https://www.climatewatchdata.org/api/v1/data/historical_emissions"

    @property
    def name(self) -> str:
        return "climate_watch"

    @property
    def domain(self) -> str:
        return "carbon"

    def fetch(self, **params: Any) -> dict:
        """Fetch historical emissions data from Climate Watch.

        Args:
            source: Data source (default 'CAIT').
            gas: Greenhouse gas filter (default 'All GHG').
            sector: Emissions sector (default 'Total including LUCF').
            regions: Comma-separated country/region codes (optional).

        Returns:
            Raw JSON response dict.
        """
        request_params: dict[str, Any] = {
            "source": params.get("source", "CAIT"),
            "gas": params.get("gas", "All GHG"),
            "sector": params.get("sector", "Total including LUCF"),
        }

        regions = params.get("regions")
        if regions:
            request_params["regions"] = regions

        try:
            response = requests.get(
                self.BASE_URL, params=request_params, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"Climate Watch API request failed: {exc}"
            ) from exc

        return response.json()

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert Climate Watch JSON response to a standardized DataFrame.

        Returns:
            DataFrame with columns: timestamp, country, sector, gas, value.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError(
                "Expected dict response from Climate Watch API"
            )

        data_entries = raw_data.get("data", [])
        if not data_entries:
            raise ConnectorError("No 'data' entries in Climate Watch response")

        rows: list[dict[str, Any]] = []
        for entry in data_entries:
            country = entry.get("country", "")
            sector = entry.get("sector", "")
            gas = entry.get("gas", "")
            emissions = entry.get("emissions", [])

            for emission in emissions:
                year = emission.get("year")
                value = emission.get("value")
                if year is not None:
                    rows.append(
                        {
                            "year": int(year),
                            "country": country,
                            "sector": sector,
                            "gas": gas,
                            "value": value,
                        }
                    )

        if not rows:
            raise ConnectorError("No emission records found in Climate Watch data")

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["year"].astype(int), format="%Y")

        return df.reset_index(drop=True)

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {"source": "CAIT", "regions": "USA"}
