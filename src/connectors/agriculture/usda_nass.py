"""USDA National Agricultural Statistics Service (NASS) connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class USDANASSConnector(BaseConnector):
    """Fetch agricultural statistics from the USDA NASS QuickStats API.

    Endpoint: https://quickstats.nass.usda.gov/api/api_GET/
    Auth: API key required (USDA_NASS_API_KEY).
    Limit: 50,000 records per query.
    """

    BASE_URL = "https://quickstats.nass.usda.gov/api/api_GET/"

    @property
    def name(self) -> str:
        return "usda_nass"

    @property
    def domain(self) -> str:
        return "agriculture"

    def fetch(self, **params: Any) -> dict:
        """Fetch data from USDA NASS QuickStats API.

        Args:
            commodity_desc: Commodity description (e.g., "CORN", "WHEAT").
            year: Year filter (e.g., 2024).
            state_name: State name filter (e.g., "IOWA").
            statisticcat_desc: Statistic category (e.g., "PRODUCTION", "YIELD").
            format: Response format (default "JSON").

        Returns:
            Raw JSON response dict.
        """
        api_key = self._settings.usda_nass_api_key
        if not api_key:
            raise ConnectorError(
                "USDA NASS API key is required. Set USDA_NASS_API_KEY in environment."
            )

        query_params: dict[str, Any] = {
            "key": api_key,
            "format": params.get("format", "JSON"),
        }

        commodity_desc = params.get("commodity_desc")
        if commodity_desc:
            query_params["commodity_desc"] = commodity_desc

        year = params.get("year")
        if year:
            query_params["year"] = year

        state_name = params.get("state_name")
        if state_name:
            query_params["state_name"] = state_name

        statisticcat_desc = params.get("statisticcat_desc")
        if statisticcat_desc:
            query_params["statisticcat_desc"] = statisticcat_desc

        try:
            response = requests.get(
                self.BASE_URL, params=query_params, timeout=60
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"USDA NASS API request failed: {exc}"
            ) from exc

        data = response.json()
        if not isinstance(data, dict):
            raise ConnectorError(
                f"USDA NASS API returned unexpected format: expected dict, got {type(data).__name__}"
            )

        if "error" in data:
            raise ConnectorError(
                f"USDA NASS API error: {data['error']}"
            )

        return data

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw USDA NASS response to a standardized DataFrame.

        Returns:
            DataFrame with columns: timestamp, state, commodity, statistic, value, unit.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError("Expected dict response from USDA NASS API")

        records = raw_data.get("data")
        if records is None:
            raise ConnectorError("Missing 'data' key in USDA NASS response")

        if not records:
            raise ConnectorError("USDA NASS response contains no records")

        rows = []
        for record in records:
            year = record.get("year")
            if year is None:
                continue

            value_str = record.get("Value", "")
            try:
                value = float(str(value_str).replace(",", ""))
            except (ValueError, TypeError):
                value = None

            rows.append(
                {
                    "timestamp": pd.Timestamp(year=int(year), month=1, day=1),
                    "state": record.get("state_name", ""),
                    "commodity": record.get("commodity_desc", ""),
                    "statistic": record.get("statisticcat_desc", ""),
                    "value": value,
                    "unit": record.get("unit_desc", ""),
                }
            )

        if not rows:
            raise ConnectorError("No valid records found in USDA NASS response")

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {"commodity_desc": "CORN", "year": "2022", "state_name": "IOWA"}
