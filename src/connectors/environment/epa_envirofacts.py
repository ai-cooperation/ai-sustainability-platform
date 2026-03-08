"""EPA Envirofacts API connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class EPAEnvirofactsConnector(BaseConnector):
    """Connector for EPA Envirofacts API.

    Endpoint: https://data.epa.gov/efservice/{table}/JSON
    Auth: None
    """

    BASE_URL = "https://data.epa.gov/efservice"

    VALID_TABLES = (
        "GHG_EMITTER_SECTOR",
        "TRI_FACILITY",
        "V_GHG_EMITTER_FACILITIES",
    )

    @property
    def name(self) -> str:
        return "epa_envirofacts"

    @property
    def domain(self) -> str:
        return "environment"

    def fetch(self, **params: Any) -> list:
        """Fetch data from EPA Envirofacts.

        Args:
            table: Table name (default: GHG_EMITTER_SECTOR).
            rows: Row range string like '0:99' (default: '0:99').

        Returns:
            Raw JSON response as list of dicts.

        Raises:
            ConnectorError: If the API call fails.
        """
        table = params.get("table", "GHG_EMITTER_SECTOR")
        rows = params.get("rows", "0:99")
        url = f"{self.BASE_URL}/{table}/rows/{rows}/JSON"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"{self.name}: API request failed - {exc}"
            ) from exc

        data = response.json()
        if not isinstance(data, list):
            raise ConnectorError(
                f"{self.name}: expected list response, got {type(data).__name__}"
            )
        return data

    def normalize(self, raw_data: list) -> pd.DataFrame:
        """Convert raw EPA Envirofacts data to a DataFrame.

        Args:
            raw_data: Raw API response list of dicts.

        Returns:
            DataFrame with a timestamp column derived from available year data.
        """
        if not raw_data:
            raise ConnectorError(f"{self.name}: empty response data")

        df = pd.DataFrame(raw_data)

        # Add timestamp from year column if available
        year_col = None
        for col in df.columns:
            if "year" in col.lower():
                year_col = col
                break

        if year_col is not None:
            df["timestamp"] = pd.to_datetime(
                df[year_col].astype(str), format="%Y", errors="coerce"
            )
        else:
            df["timestamp"] = pd.Timestamp.now()

        return df

    def _health_check_params(self) -> dict:
        return {"table": "GHG_EMITTER_SECTOR", "rows": "0:0"}
