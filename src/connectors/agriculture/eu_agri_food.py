"""EU Agri-Food data connector for dairy prices, cereal prices, and trade."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class EUAgriFoodConnector(BaseConnector):
    """Fetch agricultural market data from the EU Agri-Food Data Portal.

    Endpoint: https://agridata.ec.europa.eu/api/v1/
    Data: dairy prices, cereal prices, trade statistics.
    Auth: None required.
    """

    BASE_URL = "https://agridata.ec.europa.eu/api/v1"

    @property
    def name(self) -> str:
        return "eu_agri_food"

    @property
    def domain(self) -> str:
        return "agriculture"

    def fetch(self, **params: Any) -> dict:
        """Fetch data from the EU Agri-Food Data Portal.

        Args:
            dataset: Dataset identifier (default "cereals-prices").
            member_state: EU member state code (e.g., "FR", "DE").
            product: Product filter (e.g., "Common wheat").
            year: Year filter.

        Returns:
            Raw JSON response dict.
        """
        dataset = params.get("dataset", "cereals-prices")
        url = f"{self.BASE_URL}/{dataset}"

        query_params: dict[str, Any] = {}

        member_state = params.get("member_state")
        if member_state:
            query_params["memberState"] = member_state

        product = params.get("product")
        if product:
            query_params["product"] = product

        year = params.get("year")
        if year:
            query_params["year"] = year

        try:
            response = requests.get(url, params=query_params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"EU Agri-Food API request failed for dataset '{dataset}': {exc}"
            ) from exc

        data = response.json()
        return data

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw EU Agri-Food response to a standardized DataFrame.

        Returns:
            DataFrame with columns: timestamp, product, country, price, unit.
        """
        if isinstance(raw_data, dict):
            records = raw_data.get("data", raw_data.get("results", []))
        elif isinstance(raw_data, list):
            records = raw_data
        else:
            raise ConnectorError(
                f"EU Agri-Food API returned unexpected format: {type(raw_data).__name__}"
            )

        if not records:
            raise ConnectorError("EU Agri-Food response contains no records")

        rows = []
        for record in records:
            date_str = record.get("date") or record.get("beginDate")
            year = record.get("year")

            if date_str:
                timestamp = pd.Timestamp(date_str)
            elif year:
                timestamp = pd.Timestamp(year=int(year), month=1, day=1)
            else:
                continue

            rows.append(
                {
                    "timestamp": timestamp,
                    "product": record.get("product", record.get("productName", "")),
                    "country": record.get("memberState", record.get("country", "")),
                    "price": record.get("price", record.get("value")),
                    "unit": record.get("unit", record.get("priceUnit", "")),
                }
            )

        if not rows:
            raise ConnectorError("No valid records found in EU Agri-Food response")

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {"dataset": "cereals-prices"}
