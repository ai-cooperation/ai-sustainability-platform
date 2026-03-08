"""Open Climate Data connector (GitHub-hosted CSV datasets)."""

from __future__ import annotations

from io import StringIO
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


_DATASET_URLS: dict[str, str] = {
    "global-carbon-budget": (
        "https://raw.githubusercontent.com/openclimatedata/"
        "global-carbon-budget/main/data/global-carbon-budget.csv"
    ),
    "national-climate-plans": (
        "https://raw.githubusercontent.com/openclimatedata/"
        "national-climate-plans/main/data/pledges.csv"
    ),
}


class OpenClimateDataConnector(BaseConnector):
    """Fetch emissions data from Open Climate Data GitHub repositories.

    Supports multiple datasets hosted on GitHub:
    - global-carbon-budget
    - national-climate-plans

    Auth: None required.
    """

    @property
    def name(self) -> str:
        return "open_climate_data"

    @property
    def domain(self) -> str:
        return "carbon"

    def fetch(self, **params: Any) -> dict:
        """Download CSV data from an Open Climate Data GitHub repo.

        Args:
            dataset: Dataset name (default 'global-carbon-budget').
                Must be one of: global-carbon-budget, national-climate-plans.
            url: Custom raw CSV URL (overrides dataset selection).

        Returns:
            Dict with 'csv_text' key and metadata.
        """
        dataset = params.get("dataset", "global-carbon-budget")
        url = params.get("url")

        if url is None:
            url = _DATASET_URLS.get(dataset)
            if url is None:
                available = ", ".join(_DATASET_URLS.keys())
                raise ConnectorError(
                    f"Unknown dataset '{dataset}'. Available: {available}"
                )

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"Open Climate Data download failed for '{dataset}': {exc}"
            ) from exc

        return {
            "csv_text": response.text,
            "dataset": dataset,
            "url": url,
        }

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Parse Open Climate Data CSV into a standardized DataFrame.

        Returns:
            DataFrame with columns: timestamp, plus dataset-specific columns
            such as year, country, emissions, category.
        """
        if not isinstance(raw_data, dict) or "csv_text" not in raw_data:
            raise ConnectorError(
                "Expected dict with 'csv_text' key from Open Climate Data fetch"
            )

        csv_text = raw_data["csv_text"]

        try:
            df = pd.read_csv(StringIO(csv_text))
        except Exception as exc:
            raise ConnectorError(
                f"Failed to parse Open Climate Data CSV: {exc}"
            ) from exc

        if df.empty:
            raise ConnectorError("Open Climate Data CSV contains no data rows")

        # Detect year column (case-insensitive)
        year_col = _find_column(df, ["year", "Year", "YEAR"])
        if year_col is not None:
            df["timestamp"] = pd.to_datetime(
                df[year_col].astype(int), format="%Y"
            )
        else:
            # Fallback: use index as a simple sequence, warn via logger
            self.logger.warning(
                "No 'year' column found in Open Climate Data; "
                "using row index for timestamp."
            )
            df["timestamp"] = pd.Timestamp("1970-01-01")

        return df.reset_index(drop=True)

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {"dataset": "global-carbon-budget"}


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first matching column name from candidates."""
    for col in candidates:
        if col in df.columns:
            return col
    return None
