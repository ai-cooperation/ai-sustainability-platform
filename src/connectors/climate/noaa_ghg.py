"""NOAA Global Greenhouse Gas connector for CO2/CH4 trends."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class NOAAGHGConnector(BaseConnector):
    """Fetch greenhouse gas concentration data from NOAA GML.

    Endpoints:
        - Mauna Loa CO2: https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv
        - Global CO2: https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_gl.csv

    Auth: None (public data)
    Note: CSV files contain comment lines starting with '#' that must be skipped.
    """

    ENDPOINTS = {
        "mlo_co2": "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv",
        "gl_co2": "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_gl.csv",
    }

    @property
    def name(self) -> str:
        return "noaa_ghg"

    @property
    def domain(self) -> str:
        return "climate"

    def fetch(self, **params: Any) -> dict:
        """Fetch greenhouse gas CSV data from NOAA.

        Args:
            dataset: One of 'mlo_co2' or 'gl_co2' (default: 'mlo_co2').

        Returns:
            Dict with 'csv_text' (raw CSV string) and 'dataset' key.

        Raises:
            ConnectorError: If the request fails or dataset is unknown.
        """
        dataset = params.get("dataset", "mlo_co2")

        url = self.ENDPOINTS.get(dataset)
        if not url:
            raise ConnectorError(
                f"{self.name}: unknown dataset '{dataset}', "
                f"valid options: {list(self.ENDPOINTS.keys())}"
            )

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return {"csv_text": response.text, "dataset": dataset}
        except requests.exceptions.RequestException as e:
            raise ConnectorError(f"{self.name}: API request failed - {e}") from e

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Parse NOAA GHG CSV data, skipping comment lines starting with '#'.

        Args:
            raw_data: Dict with 'csv_text' and 'dataset' keys.

        Returns:
            DataFrame with columns: timestamp, co2_ppm, trend, location.

        Raises:
            ConnectorError: If parsing fails.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError(f"{self.name}: expected dict, got {type(raw_data).__name__}")

        csv_text = raw_data.get("csv_text", "")
        dataset = raw_data.get("dataset", "mlo_co2")

        if not csv_text.strip():
            raise ConnectorError(f"{self.name}: empty CSV response")

        # Filter out comment lines starting with '#'
        lines = csv_text.splitlines()
        data_lines = [line for line in lines if not line.startswith("#") and line.strip()]

        if not data_lines:
            raise ConnectorError(f"{self.name}: no data lines after removing comments")

        filtered_csv = "\n".join(data_lines)

        try:
            df = pd.read_csv(
                io.StringIO(filtered_csv),
                skipinitialspace=True,
            )
        except Exception as e:
            raise ConnectorError(f"{self.name}: CSV parsing failed - {e}") from e

        # Build standardized output
        location = "Mauna Loa" if "mlo" in dataset else "Global"

        # Expected columns: year, month, decimal date, monthly average, deseasonalized, ...
        # Column names vary; use positional approach for robustness
        columns = list(df.columns)
        if len(columns) < 5:
            raise ConnectorError(
                f"{self.name}: expected at least 5 columns, got {len(columns)}: {columns}"
            )

        year_col = columns[0]
        month_col = columns[1]
        average_col = columns[3]
        trend_col = columns[4]

        result = pd.DataFrame({
            "timestamp": pd.to_datetime(
                df[year_col].astype(int).astype(str)
                + "-"
                + df[month_col].astype(int).astype(str).str.zfill(2)
                + "-01"
            ),
            "co2_ppm": pd.to_numeric(df[average_col], errors="coerce"),
            "trend": pd.to_numeric(df[trend_col], errors="coerce"),
            "location": location,
        })

        # Remove rows where co2_ppm is missing (NOAA uses -99.99 for missing)
        result = result[result["co2_ppm"] > 0].reset_index(drop=True)

        return result

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {"dataset": "mlo_co2"}
