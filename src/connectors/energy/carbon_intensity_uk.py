"""UK Grid Carbon Intensity connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class CarbonIntensityUKConnector(BaseConnector):
    """Fetch UK grid carbon intensity data.

    Endpoint: https://api.carbonintensity.org.uk/intensity
    Auth: None required.
    """

    BASE_URL = "https://api.carbonintensity.org.uk"

    @property
    def name(self) -> str:
        return "carbon_intensity_uk"

    @property
    def domain(self) -> str:
        return "energy"

    def fetch(self, **params: Any) -> dict:
        """Fetch carbon intensity data.

        Args:
            date: Optional date string (YYYY-MM-DD) to fetch a specific day.
            endpoint: One of 'current', 'date', 'regional' (default 'current').

        Returns:
            Raw JSON response dict.
        """
        endpoint = params.get("endpoint", "current")

        if endpoint == "date":
            date = params.get("date", "")
            if not date:
                raise ConnectorError("Parameter 'date' is required for date endpoint")
            url = f"{self.BASE_URL}/intensity/date/{date}"
        elif endpoint == "regional":
            url = f"{self.BASE_URL}/regional"
        else:
            url = f"{self.BASE_URL}/intensity"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"Carbon Intensity UK API request failed: {exc}"
            ) from exc

        return response.json()

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw Carbon Intensity response to a standardized DataFrame.

        Returns:
            DataFrame with columns: timestamp, intensity_forecast,
            intensity_actual, index, region.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError("Expected dict response from Carbon Intensity UK API")

        data_list = raw_data.get("data", [])
        if not data_list:
            raise ConnectorError("No data found in Carbon Intensity UK response")

        rows = []

        # Handle regional data which nests differently
        if isinstance(data_list, dict) and "regionid" in data_list:
            data_list = [data_list]

        for item in data_list:
            # Regional responses have a 'data' key with sub-items
            if "regions" in item:
                for region in item["regions"]:
                    intensity = region.get("intensity", {})
                    rows.append(
                        {
                            "timestamp": pd.to_datetime(item.get("from")),
                            "intensity_forecast": intensity.get("forecast"),
                            "intensity_actual": intensity.get("actual"),
                            "index": intensity.get("index"),
                            "region": region.get("shortname", ""),
                        }
                    )
            else:
                intensity = item.get("intensity", {})
                rows.append(
                    {
                        "timestamp": pd.to_datetime(item.get("from")),
                        "intensity_forecast": intensity.get("forecast"),
                        "intensity_actual": intensity.get("actual"),
                        "index": intensity.get("index"),
                        "region": "national",
                    }
                )

        return pd.DataFrame(rows)

    def _health_check_params(self) -> dict:
        """Minimal params: fetch current intensity."""
        return {"endpoint": "current"}
