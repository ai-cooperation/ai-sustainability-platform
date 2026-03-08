"""Emissions API connector (emissions-api.org)."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class EmissionsAPIConnector(BaseConnector):
    """Connector for Emissions API v2.

    Endpoint: https://api.v2.emissions-api.org/api/v2/{product}/geo.json
    Auth: None
    Products: carbonmonoxide, nitrogendioxide, ozone, sulfurdioxide
    """

    BASE_URL = "https://api.v2.emissions-api.org/api/v2"

    VALID_PRODUCTS = (
        "carbonmonoxide",
        "nitrogendioxide",
        "ozone",
        "sulfurdioxide",
    )

    @property
    def name(self) -> str:
        return "emissions_api"

    @property
    def domain(self) -> str:
        return "environment"

    def fetch(self, **params: Any) -> dict:
        """Fetch emissions data from Emissions API.

        Args:
            product: One of carbonmonoxide, nitrogendioxide, ozone, sulfurdioxide.
            country: ISO 3166-1 alpha-2 country code (optional).
            begin: Start date string YYYY-MM-DD (optional).
            end: End date string YYYY-MM-DD (optional).
            limit: Max number of results (default: 100).

        Returns:
            GeoJSON dict.

        Raises:
            ConnectorError: If the API call fails.
        """
        product = params.get("product", "carbonmonoxide")
        if product not in self.VALID_PRODUCTS:
            raise ConnectorError(
                f"{self.name}: invalid product '{product}', "
                f"must be one of {self.VALID_PRODUCTS}"
            )

        url = f"{self.BASE_URL}/{product}/geo.json"
        query: dict[str, Any] = {}
        if "country" in params:
            query["country"] = params["country"]
        if "begin" in params:
            query["begin"] = params["begin"]
        if "end" in params:
            query["end"] = params["end"]
        query["limit"] = params.get("limit", 100)

        try:
            response = requests.get(url, params=query, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"{self.name}: API request failed - {exc}"
            ) from exc

        data = response.json()
        if not isinstance(data, dict) or "features" not in data:
            raise ConnectorError(
                f"{self.name}: unexpected response format - missing 'features' key"
            )
        return data

    def normalize(self, raw_data: dict) -> pd.DataFrame:
        """Convert GeoJSON response to a DataFrame.

        Args:
            raw_data: GeoJSON dict with features.

        Returns:
            DataFrame with columns: timestamp, latitude, longitude, product, value.
        """
        features = raw_data.get("features", [])
        if not features:
            raise ConnectorError(f"{self.name}: no features in response")

        rows = []
        for feature in features:
            props = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            coordinates = geometry.get("coordinates", [None, None])

            # GeoJSON uses [lon, lat] order
            lon = coordinates[0] if len(coordinates) > 0 else None
            lat = coordinates[1] if len(coordinates) > 1 else None

            rows.append(
                {
                    "timestamp": props.get("time_start"),
                    "latitude": lat,
                    "longitude": lon,
                    "product": props.get("product"),
                    "value": props.get("value"),
                }
            )

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df

    def _health_check_params(self) -> dict:
        return {"product": "carbonmonoxide", "limit": 1}
