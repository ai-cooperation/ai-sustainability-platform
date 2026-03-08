"""World Bank Climate Data connector (via World Bank Indicators API)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class WorldBankClimateConnector(BaseConnector):
    """Fetch climate indicator data from the World Bank Indicators API.

    Endpoint: https://api.worldbank.org/v2/country/{country}/indicator/{indicator}
    Auth: None (public API)
    """

    BASE_URL = "https://api.worldbank.org/v2/country"

    # Common climate-related indicators
    INDICATORS = {
        "co2_per_capita": "EN.ATM.CO2E.PC",
        "energy_use_per_capita": "EG.USE.PCAP.KG.OE",
        "population": "SP.POP.TOTL",
        "renewable_energy_pct": "EG.FEC.RNEW.ZS",
    }

    DEFAULT_INDICATOR = "EG.USE.PCAP.KG.OE"

    @property
    def name(self) -> str:
        return "world_bank_climate"

    @property
    def domain(self) -> str:
        return "climate"

    def fetch(self, **params: Any) -> dict:
        """Fetch climate indicator data from the World Bank API.

        Args:
            country: Country code (ISO alpha-3 or 'WLD' for world).
                Default: 'WLD'.
            indicator: Indicator code or alias from INDICATORS dict.
                Default: 'EN.ATM.CO2E.PC' (CO2 emissions per capita).
            start_year: Start year for date range. Default: 10 years ago.
            end_year: End year for date range. Default: current year.

        Returns:
            Dict with 'data' (list of records) and request metadata.

        Raises:
            ConnectorError: If the API request fails.
        """
        country = params.get("country", "WLD")
        indicator_input = params.get("indicator", self.DEFAULT_INDICATOR)
        indicator = self.INDICATORS.get(indicator_input, indicator_input)

        current_year = datetime.now().year
        start_year = params.get("start_year", current_year - 10)
        end_year = params.get("end_year", current_year)

        url = (
            f"{self.BASE_URL}/{country}/indicator/{indicator}"
        )
        query_params = {
            "format": "json",
            "date": f"{start_year}:{end_year}",
            "per_page": 500,
        }

        try:
            response = requests.get(url, params=query_params, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.JSONDecodeError as e:
            raise ConnectorError(f"{self.name}: invalid JSON response - {e}") from e
        except requests.exceptions.RequestException as e:
            raise ConnectorError(f"{self.name}: API request failed - {e}") from e

        # World Bank API returns [metadata, data_records] on success,
        # or [{message: [...]}] on error (e.g., archived indicator).
        if not isinstance(payload, list):
            raise ConnectorError(
                f"{self.name}: unexpected response structure "
                f"(expected list, got {type(payload).__name__})"
            )

        if len(payload) == 1 and isinstance(payload[0], dict) and "message" in payload[0]:
            messages = payload[0]["message"]
            msg_text = messages[0].get("value", "unknown error") if messages else "unknown error"
            raise ConnectorError(f"{self.name}: API error - {msg_text}")

        if len(payload) < 2:
            raise ConnectorError(
                f"{self.name}: unexpected response structure "
                f"(expected list with 2 elements, got {len(payload)} elements)"
            )

        metadata = payload[0]
        records = payload[1]

        if records is None:
            records = []

        return {
            "data": records,
            "country": country,
            "indicator": indicator,
            "start_year": start_year,
            "end_year": end_year,
            "api_metadata": metadata,
        }

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert World Bank API response to standardized DataFrame.

        Args:
            raw_data: Dict with 'data' list and metadata from fetch().

        Returns:
            DataFrame with columns: timestamp, country, variable, value.

        Raises:
            ConnectorError: If response structure is unexpected.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError(f"{self.name}: expected dict, got {type(raw_data).__name__}")

        data = raw_data.get("data")
        if not data:
            raise ConnectorError(f"{self.name}: empty data in response")

        if not isinstance(data, list):
            raise ConnectorError(f"{self.name}: expected list for 'data', got {type(data).__name__}")

        indicator = raw_data.get("indicator", "unknown")

        records = []
        for entry in data:
            value = entry.get("value")
            if value is None:
                continue

            year_str = entry.get("date")
            if not year_str:
                continue

            country_info = entry.get("country", {})
            country_code = country_info.get("id", raw_data.get("country", "UNKNOWN"))

            indicator_info = entry.get("indicator", {})
            indicator_name = indicator_info.get("id", indicator)

            records.append({
                "timestamp": pd.Timestamp(year=int(year_str), month=1, day=1),
                "country": country_code,
                "variable": indicator_name,
                "value": float(value),
            })

        if not records:
            raise ConnectorError(f"{self.name}: could not extract any records from response")

        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {"country": "WLD", "indicator": self.DEFAULT_INDICATOR}
