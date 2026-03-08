"""EPA Water Quality Portal connector."""

from __future__ import annotations

from io import StringIO
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class EPAWaterQualityConnector(BaseConnector):
    """Connector for EPA Water Quality Portal (waterqualitydata.us).

    Endpoint: https://www.waterqualitydata.us/data/Result/search
    Auth: None
    Returns CSV data.
    """

    BASE_URL = "https://www.waterqualitydata.us/data/Result/search"

    @property
    def name(self) -> str:
        return "epa_water_quality"

    @property
    def domain(self) -> str:
        return "environment"

    def fetch(self, **params: Any) -> dict:
        """Fetch water quality data from EPA Water Quality Portal.

        Args:
            statecode: US state code (e.g., 'US:06' for California).
            characteristicName: Parameter to query (e.g., 'Dissolved oxygen').

        Returns:
            Dict with 'csv_text' key containing raw CSV string.

        Raises:
            ConnectorError: If the API call fails.
        """
        query = {
            "statecode": params.get("statecode", "US:06"),
            "characteristicName": params.get(
                "characteristicName", "Dissolved oxygen"
            ),
            "mimeType": "csv",
            "sorted": "no",
            "zip": "no",
        }

        try:
            response = requests.get(self.BASE_URL, params=query, timeout=60)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"{self.name}: API request failed - {exc}"
            ) from exc

        content_type = response.headers.get("Content-Type", "")
        if "text" not in content_type and "csv" not in content_type:
            raise ConnectorError(
                f"{self.name}: expected CSV response, got Content-Type: {content_type}"
            )

        return {"csv_text": response.text}

    def normalize(self, raw_data: dict) -> pd.DataFrame:
        """Parse CSV response into a DataFrame.

        Args:
            raw_data: Dict with 'csv_text' key.

        Returns:
            DataFrame with columns: timestamp, station, parameter, value, unit.
        """
        csv_text = raw_data.get("csv_text", "")
        if not csv_text.strip():
            raise ConnectorError(f"{self.name}: empty CSV response")

        try:
            df = pd.read_csv(StringIO(csv_text), low_memory=False)
        except Exception as exc:
            raise ConnectorError(
                f"{self.name}: failed to parse CSV - {exc}"
            ) from exc

        if df.empty:
            raise ConnectorError(f"{self.name}: parsed CSV has no rows")

        # Map columns to standard names
        column_map = {
            "ActivityStartDate": "timestamp",
            "MonitoringLocationIdentifier": "station",
            "CharacteristicName": "parameter",
            "ResultMeasureValue": "value",
            "ResultMeasure/MeasureUnitCode": "unit",
        }

        result = pd.DataFrame()
        for source_col, target_col in column_map.items():
            if source_col in df.columns:
                result[target_col] = df[source_col]

        if "timestamp" in result.columns:
            result["timestamp"] = pd.to_datetime(
                result["timestamp"], errors="coerce"
            )
        else:
            result["timestamp"] = pd.Timestamp.now()

        return result

    def _health_check_params(self) -> dict:
        return {
            "statecode": "US:06",
            "characteristicName": "Dissolved oxygen",
        }
