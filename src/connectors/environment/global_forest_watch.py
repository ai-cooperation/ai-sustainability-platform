"""Global Forest Watch API connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class GlobalForestWatchConnector(BaseConnector):
    """Connector for Global Forest Watch Data API.

    Endpoint: https://data-api.globalforestwatch.org/dataset/{dataset}/latest
    Auth: API key (GLOBAL_FOREST_WATCH_API_KEY)
    """

    BASE_URL = "https://data-api.globalforestwatch.org"

    DEFAULT_DATASET = "umd_tree_cover_loss"

    @property
    def name(self) -> str:
        return "global_forest_watch"

    @property
    def domain(self) -> str:
        return "environment"

    def _get_api_key(self) -> str:
        """Retrieve Global Forest Watch API key from settings.

        Raises:
            ConnectorError: If API key is not configured.
        """
        key = self._settings.global_forest_watch_api_key
        if not key:
            raise ConnectorError(
                f"{self.name}: GLOBAL_FOREST_WATCH_API_KEY not configured"
            )
        return key

    def fetch(self, **params: Any) -> dict:
        """Fetch forest data from Global Forest Watch.

        Args:
            dataset: Dataset identifier (default: umd_tree_cover_loss).
            country: ISO 3166-1 alpha-3 country code (optional).

        Returns:
            Raw JSON response dict.

        Raises:
            ConnectorError: If the API call fails.
        """
        api_key = self._get_api_key()
        dataset = params.get("dataset", self.DEFAULT_DATASET)
        url = f"{self.BASE_URL}/dataset/{dataset}/latest"

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
        }
        query: dict[str, Any] = {}
        if "country" in params:
            query["iso"] = params["country"]

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
        if not isinstance(data, dict):
            raise ConnectorError(
                f"{self.name}: unexpected response format"
            )
        return data

    def normalize(self, raw_data: dict) -> pd.DataFrame:
        """Convert raw Global Forest Watch data to a DataFrame.

        Args:
            raw_data: Raw API response dict.

        Returns:
            DataFrame with columns: year, country, tree_cover_loss_ha,
            co2_emissions, timestamp.
        """
        # Data may be nested under 'data' key
        records = raw_data.get("data", raw_data)
        if isinstance(records, dict):
            records = [records]

        if not records:
            raise ConnectorError(f"{self.name}: no data in response")

        rows = []
        for record in records:
            rows.append(
                {
                    "year": record.get("year"),
                    "country": record.get("country", record.get("iso")),
                    "tree_cover_loss_ha": record.get("tree_cover_loss_ha",
                                                      record.get("area_ha")),
                    "co2_emissions": record.get("co2_emissions",
                                                 record.get("emissions")),
                }
            )

        df = pd.DataFrame(rows)

        # Create timestamp from year
        if "year" in df.columns and df["year"].notna().any():
            df["timestamp"] = pd.to_datetime(
                df["year"].astype(int).astype(str), format="%Y", errors="coerce"
            )
        else:
            df["timestamp"] = pd.Timestamp.now()

        return df

    def _health_check_params(self) -> dict:
        return {"dataset": self.DEFAULT_DATASET}
