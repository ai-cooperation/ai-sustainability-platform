"""EU Agri-Food data connector (via Eurostat API, with USDA FAS fallback)."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class EUAgriFoodConnector(BaseConnector):
    """Fetch agricultural data from Eurostat API (crop production).

    Primary: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/
    Fallback: https://apps.fas.usda.gov/OpenData/api/esr/exports/
    Auth: None required for either endpoint.
    """

    EUROSTAT_BASE = (
        "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
    )
    USDA_FAS_BASE = "https://apps.fas.usda.gov/OpenData/api/esr/exports"

    @property
    def name(self) -> str:
        return "eu_agri_food"

    @property
    def domain(self) -> str:
        return "agriculture"

    def fetch(self, **params: Any) -> dict:
        """Fetch crop production data from Eurostat, falling back to USDA FAS.

        Args:
            dataset: Eurostat dataset code. Default: 'apro_cpsh1'.
            geo: Geographic area. Default: 'EU27_2020'.
            crops: Crop code. Default: 'C0000' (total cereals).
            strucpro: Structure of production. Default: 'PR_HU_EU'.
            commodity_code: USDA commodity code for fallback. Default: '0100000'.

        Returns:
            Dict with normalized structure containing data records.

        Raises:
            ConnectorError: If both APIs fail.
        """
        try:
            return self._fetch_eurostat(**params)
        except ConnectorError:
            self.logger.warning(
                "Eurostat API failed, falling back to USDA FAS API"
            )
            return self._fetch_usda_fas(**params)

    def _fetch_eurostat(self, **params: Any) -> dict:
        """Fetch from Eurostat API."""
        dataset = params.get("dataset", "apro_cpsh1")
        geo = params.get("geo", "EU27_2020")
        crops = params.get("crops", "C0000")
        strucpro = params.get("strucpro", "PR_HU_EU")

        url = f"{self.EUROSTAT_BASE}/{dataset}"
        query_params = {
            "format": "JSON",
            "lang": "en",
            "geo": geo,
            "crops": crops,
            "strucpro": strucpro,
        }

        try:
            response = requests.get(url, params=query_params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"Eurostat API request failed for dataset '{dataset}': {exc}"
            ) from exc

        raw = response.json()
        return self._convert_eurostat_response(raw, geo, crops)

    def _convert_eurostat_response(
        self, raw: dict, geo: str, crops: str
    ) -> dict:
        """Convert Eurostat JSON-stat format to a flat record list."""
        values = raw.get("value", {})
        dimensions = raw.get("dimension", {})

        time_dim = dimensions.get("time", {}).get("category", {}).get("index", {})
        # time_dim is {year_label: positional_index}
        index_to_year = {v: k for k, v in time_dim.items()}

        records = []
        for idx_str, val in values.items():
            year_label = index_to_year.get(int(idx_str))
            if year_label is None:
                continue
            records.append({
                "year": int(year_label),
                "product": crops,
                "country": geo,
                "value": float(val),
                "unit": raw.get("extension", {}).get("annotation", [{}])[0].get("title", ""),
            })

        return {"data": records, "source": "eurostat"}

    def _fetch_usda_fas(self, **params: Any) -> dict:
        """Fetch from USDA FAS API as fallback."""
        commodity_code = params.get("commodity_code", "0100000")
        url = f"{self.USDA_FAS_BASE}/commodityCode/{commodity_code}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"USDA FAS API request failed for commodity '{commodity_code}': {exc}"
            ) from exc

        raw = response.json()
        if not isinstance(raw, list):
            raw = [raw]

        records = []
        for entry in raw:
            year = entry.get("dataYear") or entry.get("year")
            if year is None:
                continue
            records.append({
                "year": int(year),
                "product": entry.get("commodityDescription", entry.get("commodity", "")),
                "country": entry.get("countryDescription", entry.get("country", "")),
                "value": float(entry.get("quantity", entry.get("value", 0))),
                "unit": entry.get("unitDescription", entry.get("unit", "")),
            })

        return {"data": records, "source": "usda_fas"}

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw response to a standardized DataFrame.

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
        return {"dataset": "apro_cpsh1"}
