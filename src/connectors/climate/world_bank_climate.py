"""World Bank Climate Data API connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class WorldBankClimateConnector(BaseConnector):
    """Fetch climate data from World Bank Climate Data API.

    Endpoint: http://climatedataapi.worldbank.org/climateweb/rest/v1/country/
    Auth: None (public API)
    """

    BASE_URL = "http://climatedataapi.worldbank.org/climateweb/rest/v1/country"

    @property
    def name(self) -> str:
        return "world_bank_climate"

    @property
    def domain(self) -> str:
        return "climate"

    def fetch(self, **params: Any) -> dict:
        """Fetch climate data for a country.

        Args:
            var: Climate variable - 'tas' (temperature) or 'pr' (precipitation).
                Default: 'tas'.
            aggregation: Time aggregation - 'mavg' (monthly avg), 'annualavg',
                'manom' (monthly anomaly). Default: 'annualavg'.
            country_iso: ISO 3166-1 alpha-3 country code. Default: 'TWN'.

        Returns:
            Dict with 'data' (list of records) and request metadata.

        Raises:
            ConnectorError: If the API request fails.
        """
        var = params.get("var", "tas")
        aggregation = params.get("aggregation", "annualavg")
        country_iso = params.get("country_iso", "TWN")

        url = f"{self.BASE_URL}/{aggregation}/{var}/1980/2099/{country_iso}.json"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            return {
                "data": data,
                "var": var,
                "aggregation": aggregation,
                "country_iso": country_iso,
            }
        except requests.exceptions.JSONDecodeError as e:
            raise ConnectorError(f"{self.name}: invalid JSON response - {e}") from e
        except requests.exceptions.RequestException as e:
            raise ConnectorError(f"{self.name}: API request failed - {e}") from e

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert World Bank climate response to standardized DataFrame.

        Args:
            raw_data: Dict with 'data' list and metadata.

        Returns:
            DataFrame with columns: timestamp, country, scenario,
            variable, value.

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

        country = raw_data.get("country_iso", "UNKNOWN")
        var = raw_data.get("var", "unknown")

        records = []
        for entry in data:
            scenario = entry.get("scenario", "historical")
            from_year = entry.get("fromYear")
            to_year = entry.get("toYear")
            annual_data = entry.get("annualData", entry.get("monthVals", []))

            if isinstance(annual_data, list) and annual_data:
                # Monthly data (12 values)
                if len(annual_data) == 12:
                    base_year = from_year if from_year else 2000
                    for month_idx, val in enumerate(annual_data, start=1):
                        if val is not None:
                            records.append({
                                "timestamp": pd.Timestamp(year=int(base_year), month=month_idx, day=1),
                                "country": country,
                                "scenario": scenario,
                                "variable": var,
                                "value": float(val),
                            })
            elif isinstance(annual_data, (int, float)):
                year = from_year if from_year else 2000
                records.append({
                    "timestamp": pd.Timestamp(year=int(year), month=1, day=1),
                    "country": country,
                    "scenario": scenario,
                    "variable": var,
                    "value": float(annual_data),
                })

            # Handle direct annual average responses (single value per model/scenario)
            if not records or (isinstance(annual_data, list) and len(annual_data) != 12):
                annual_val = entry.get("annualVal")
                if annual_val is not None and from_year:
                    records.append({
                        "timestamp": pd.Timestamp(year=int(from_year), month=1, day=1),
                        "country": country,
                        "scenario": scenario,
                        "variable": var,
                        "value": float(annual_val),
                    })

        if not records:
            raise ConnectorError(f"{self.name}: could not extract any records from response")

        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {"var": "tas", "aggregation": "annualavg", "country_iso": "USA"}
