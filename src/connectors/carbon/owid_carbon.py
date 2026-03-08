"""Our World in Data CO2 emissions connector."""

from __future__ import annotations

from io import StringIO
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class OWIDCarbonConnector(BaseConnector):
    """Fetch CO2 emissions data from Our World in Data GitHub repository.

    Downloads CSV from the OWID co2-data repo.
    Auth: None required.
    """

    BASE_URL = (
        "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
    )

    COLUMNS = [
        "year",
        "country",
        "co2",
        "co2_per_capita",
        "population",
        "gdp",
        "energy_per_capita",
    ]

    @property
    def name(self) -> str:
        return "owid_carbon"

    @property
    def domain(self) -> str:
        return "carbon"

    def fetch(self, **params: Any) -> dict:
        """Download OWID CO2 CSV data.

        Args:
            country: Filter by country name (optional).
            start_year: Filter from year (optional).
            end_year: Filter to year (optional).

        Returns:
            Dict with 'csv_text' key containing raw CSV content.
        """
        try:
            response = requests.get(self.BASE_URL, timeout=60)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"OWID Carbon data download failed: {exc}"
            ) from exc

        return {"csv_text": response.text, "params": params}

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Parse OWID CSV and produce a standardized DataFrame.

        Returns:
            DataFrame with columns: timestamp, country, co2, co2_per_capita,
            population, gdp, energy_per_capita.
        """
        if not isinstance(raw_data, dict) or "csv_text" not in raw_data:
            raise ConnectorError("Expected dict with 'csv_text' key from OWID fetch")

        csv_text = raw_data["csv_text"]
        params = raw_data.get("params", {})

        try:
            df = pd.read_csv(StringIO(csv_text))
        except Exception as exc:
            raise ConnectorError(f"Failed to parse OWID CSV: {exc}") from exc

        # Select only the columns we need (if they exist)
        available = [c for c in self.COLUMNS if c in df.columns]
        if not available:
            raise ConnectorError("No expected columns found in OWID CSV data")
        df = df[available].copy()

        # Apply optional filters
        country = params.get("country")
        if country:
            df = df[df["country"] == country].copy()

        start_year = params.get("start_year")
        if start_year and "year" in df.columns:
            df = df[df["year"] >= int(start_year)].copy()

        end_year = params.get("end_year")
        if end_year and "year" in df.columns:
            df = df[df["year"] <= int(end_year)].copy()

        # Create timestamp from year (January 1 of that year)
        if "year" in df.columns:
            df["timestamp"] = pd.to_datetime(
                df["year"].astype(int), format="%Y"
            )
        else:
            raise ConnectorError("Missing 'year' column in OWID data")

        return df.reset_index(drop=True)

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {"country": "World", "start_year": 2020, "end_year": 2020}
