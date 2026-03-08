"""EU Open Power System Data connector."""

from __future__ import annotations

from io import StringIO
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class OpenPowerSystemConnector(BaseConnector):
    """Fetch European power system time-series data.

    Source: https://data.open-power-system-data.org/time_series/
    Auth: None required.
    Downloads static CSV files.
    """

    BASE_URL = (
        "https://data.open-power-system-data.org/time_series/"
        "latest/time_series_60min_singleindex.csv"
    )

    @property
    def name(self) -> str:
        return "open_power_system"

    @property
    def domain(self) -> str:
        return "energy"

    def fetch(self, **params: Any) -> dict:
        """Fetch Open Power System CSV data.

        Args:
            url: Override the CSV download URL.
            nrows: Limit number of rows to read (for large files).
            country: Optional country filter (e.g., 'DE', 'FR').

        Returns:
            Dict with 'csv_text' and 'nrows' keys.
        """
        url = params.get("url", self.BASE_URL)
        nrows = params.get("nrows", 1000)

        try:
            response = requests.get(url, timeout=120, stream=True)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"Open Power System Data download failed: {exc}"
            ) from exc

        # Read only the needed rows to limit memory usage
        lines = []
        for i, line in enumerate(response.iter_lines(decode_unicode=True)):
            if line is not None:
                lines.append(line)
            if i >= nrows:
                break

        if len(lines) < 2:
            raise ConnectorError("Open Power System Data: insufficient data in CSV")

        return {"csv_text": "\n".join(lines), "country": params.get("country")}

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw CSV text to a standardized DataFrame.

        Returns:
            DataFrame with columns: timestamp, country, load,
            wind_onshore, wind_offshore, solar (among others).
        """
        if not isinstance(raw_data, dict) or "csv_text" not in raw_data:
            raise ConnectorError("Expected dict with 'csv_text' key")

        csv_text = raw_data["csv_text"]
        country_filter = raw_data.get("country")

        try:
            df = pd.read_csv(StringIO(csv_text))
        except Exception as exc:
            raise ConnectorError(
                f"Failed to parse Open Power System CSV: {exc}"
            ) from exc

        # The CSV has a 'utc_timestamp' column
        timestamp_col = None
        for candidate in ("utc_timestamp", "timestamp", "Unnamed: 0"):
            if candidate in df.columns:
                timestamp_col = candidate
                break

        if timestamp_col is None:
            raise ConnectorError(
                "Could not find timestamp column in Open Power System Data"
            )

        df = df.rename(columns={timestamp_col: "timestamp"})
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

        # Optionally filter columns by country prefix
        if country_filter:
            prefix = f"{country_filter}_"
            keep_cols = ["timestamp"] + [
                c for c in df.columns if c.startswith(prefix)
            ]
            df = df[keep_cols]
            df.columns = [
                c.replace(prefix, "") if c != "timestamp" else c for c in df.columns
            ]
            df["country"] = country_filter

        return df

    def _health_check_params(self) -> dict:
        """Minimal params: fetch just a few rows."""
        return {"nrows": 5}
