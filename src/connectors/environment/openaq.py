"""OpenAQ API connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class OpenAQConnector(BaseConnector):
    """Connector for OpenAQ API v3.

    Endpoint: https://api.openaq.org/v3/locations, /measurements
    Auth: API key (OPENAQ_API_KEY)
    """

    BASE_URL = "https://api.openaq.org/v3"

    @property
    def name(self) -> str:
        return "openaq"

    @property
    def domain(self) -> str:
        return "environment"

    def _get_api_key(self) -> str:
        """Retrieve OpenAQ API key from settings.

        Raises:
            ConnectorError: If API key is not configured.
        """
        key = self._settings.openaq_api_key
        if not key:
            raise ConnectorError(
                f"{self.name}: OPENAQ_API_KEY not configured"
            )
        return key

    def fetch(self, **params: Any) -> dict:
        """Fetch air quality measurements from OpenAQ.

        Args:
            endpoint: API endpoint ('locations' or 'measurements').
            country: ISO country code (optional).
            limit: Max results (default: 100).
            page: Page number (default: 1).

        Returns:
            Raw JSON response dict.

        Raises:
            ConnectorError: If the API call fails.
        """
        api_key = self._get_api_key()
        endpoint = params.get("endpoint", "locations")
        url = f"{self.BASE_URL}/{endpoint}"

        headers = {"X-API-Key": api_key}
        query: dict[str, Any] = {
            "limit": params.get("limit", 100),
            "page": params.get("page", 1),
        }
        if "country" in params:
            query["country"] = params["country"]

        try:
            response = requests.get(
                url, headers=headers, params=query, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"{self.name}: API request failed - {exc}"
            ) from exc

        data = response.json()
        if "results" not in data:
            raise ConnectorError(
                f"{self.name}: unexpected response format - missing 'results' key"
            )
        return data

    def normalize(self, raw_data: dict) -> pd.DataFrame:
        """Convert raw OpenAQ data to a DataFrame.

        Args:
            raw_data: Raw API response dict.

        Returns:
            DataFrame with columns: timestamp, location, parameter,
            value, unit, country.
        """
        results = raw_data.get("results", [])
        if not results:
            raise ConnectorError(f"{self.name}: no results in response")

        rows = []
        for item in results:
            # Handle both locations and measurements endpoints
            if "measurements" in item:
                for m in item["measurements"]:
                    rows.append(
                        {
                            "timestamp": item.get("datetime", {}).get(
                                "utc", item.get("lastUpdated")
                            ),
                            "location": item.get("name", ""),
                            "parameter": m.get("parameter", {}).get(
                                "name", ""
                            ),
                            "value": m.get("value"),
                            "unit": m.get("parameter", {}).get("units", ""),
                            "country": item.get("country", {}).get(
                                "code", ""
                            ),
                        }
                    )
            else:
                rows.append(
                    {
                        "timestamp": item.get("datetime", {}).get(
                            "utc",
                            item.get("lastUpdated"),
                        ),
                        "location": item.get("name", ""),
                        "parameter": item.get("parameter", ""),
                        "value": item.get("value"),
                        "unit": item.get("unit", ""),
                        "country": item.get("country", {}).get("code", "")
                        if isinstance(item.get("country"), dict)
                        else item.get("country", ""),
                    }
                )

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df

    def _health_check_params(self) -> dict:
        return {"endpoint": "locations", "limit": 1}
