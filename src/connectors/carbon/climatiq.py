"""Climatiq emissions estimation connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class ClimatiqConnector(BaseConnector):
    """Estimate CO2e emissions using the Climatiq API.

    Endpoint: https://api.climatiq.io/estimate
    Auth: API key required (Bearer token).
    """

    BASE_URL = "https://api.climatiq.io/estimate"

    @property
    def name(self) -> str:
        return "climatiq"

    @property
    def domain(self) -> str:
        return "carbon"

    def fetch(self, **params: Any) -> dict:
        """Send an estimation request to the Climatiq API.

        Args:
            emission_factor_id: The emission factor ID (required).
            activity_value: Activity value (required).
            activity_unit: Activity unit (required, e.g. 'kWh', 'kg').

        Returns:
            Raw JSON response dict.

        Raises:
            ConnectorError: If API key is missing or request fails.
        """
        api_key = self._settings.climatiq_api_key
        if not api_key:
            raise ConnectorError(
                "Climatiq API key is not configured. "
                "Set CLIMATIQ_API_KEY in environment."
            )

        emission_factor_id = params.get("emission_factor_id")
        activity_value = params.get("activity_value")
        activity_unit = params.get("activity_unit")

        if not emission_factor_id or activity_value is None or not activity_unit:
            raise ConnectorError(
                "Climatiq requires 'emission_factor_id', 'activity_value', "
                "and 'activity_unit' parameters."
            )

        payload = {
            "emission_factor": {
                "id": emission_factor_id,
            },
            "parameters": {
                "money": activity_value,
                "money_unit": activity_unit,
            },
        }

        # Allow custom payload structure via 'body' param
        body_override = params.get("body")
        if body_override and isinstance(body_override, dict):
            payload = body_override

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.BASE_URL, json=payload, headers=headers, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"Climatiq API request failed: {exc}"
            ) from exc

        return response.json()

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert Climatiq estimation response to a standardized DataFrame.

        Returns:
            DataFrame with columns: timestamp, activity, emission_factor,
            co2e, co2e_unit, source.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError("Expected dict response from Climatiq API")

        co2e = raw_data.get("co2e")
        if co2e is None:
            raise ConnectorError("Missing 'co2e' field in Climatiq response")

        row = {
            "timestamp": pd.Timestamp.now(tz="UTC"),
            "activity": raw_data.get("activity_id", ""),
            "emission_factor": raw_data.get("emission_factor", {}).get("id", ""),
            "co2e": co2e,
            "co2e_unit": raw_data.get("co2e_unit", "kg"),
            "source": raw_data.get("source", ""),
        }

        df = pd.DataFrame([row])
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        return df

    def _health_check_params(self) -> dict:
        """Minimal params for health check - requires valid API key."""
        return {
            "emission_factor_id": "electricity-supply_grid-source_residual_mix",
            "activity_value": 1,
            "activity_unit": "kWh",
        }
