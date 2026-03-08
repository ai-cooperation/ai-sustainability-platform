"""FAOSTAT data connector for crop production, land use, and trade."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class FAOSTATConnector(BaseConnector):
    """Fetch agricultural data from the FAOSTAT API.

    Endpoint: https://fenixservices.fao.org/faostat/api/v1/en/data/{domain}
    Domains: QCL (crop production), RL (land use), GT (trade).
    Auth: None required.
    """

    BASE_URL = "https://fenixservices.fao.org/faostat/api/v1/en/data"

    @property
    def name(self) -> str:
        return "faostat"

    @property
    def domain(self) -> str:
        return "agriculture"

    def fetch(self, **params: Any) -> dict:
        """Fetch data from a FAOSTAT domain.

        Args:
            faostat_domain: FAOSTAT domain code (default "QCL").
            area_code: Country/area code (e.g., "5000" for world).
            item_code: Item code (e.g., "15" for wheat).
            element_code: Element code (e.g., "5510" for production).
            year: Year or comma-separated years (e.g., "2020,2021,2022").

        Returns:
            Raw JSON response dict.
        """
        faostat_domain = params.get("faostat_domain", "QCL")
        url = f"{self.BASE_URL}/{faostat_domain}"

        query_params: dict[str, Any] = {}

        area_code = params.get("area_code")
        if area_code:
            query_params["area_code"] = area_code

        item_code = params.get("item_code")
        if item_code:
            query_params["item_code"] = item_code

        element_code = params.get("element_code")
        if element_code:
            query_params["element_code"] = element_code

        year = params.get("year")
        if year:
            query_params["year"] = year

        try:
            response = requests.get(url, params=query_params, timeout=60)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"FAOSTAT API request failed for domain '{faostat_domain}': {exc}"
            ) from exc

        data = response.json()
        if not isinstance(data, dict):
            raise ConnectorError(
                f"FAOSTAT API returned unexpected format: expected dict, got {type(data).__name__}"
            )
        return data

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw FAOSTAT response to a standardized DataFrame.

        Returns:
            DataFrame with columns: timestamp, country, item, element, value, unit.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError("Expected dict response from FAOSTAT API")

        records = raw_data.get("data")
        if records is None:
            raise ConnectorError("Missing 'data' key in FAOSTAT response")

        if not records:
            raise ConnectorError("FAOSTAT response contains no records")

        rows = []
        for record in records:
            year = record.get("Year")
            if year is None:
                continue
            rows.append(
                {
                    "timestamp": pd.Timestamp(year=int(year), month=1, day=1),
                    "country": record.get("Area", ""),
                    "item": record.get("Item", ""),
                    "element": record.get("Element", ""),
                    "value": record.get("Value"),
                    "unit": record.get("Unit", ""),
                }
            )

        if not rows:
            raise ConnectorError("No valid records found in FAOSTAT response")

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {"faostat_domain": "QCL", "area_code": "5000", "year": "2022"}
