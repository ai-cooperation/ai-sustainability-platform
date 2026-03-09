"""Climatiq emissions estimation connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError

# Map common units to Climatiq parameter type keys.
# The Climatiq API expects activity parameters keyed by type,
# e.g. {"energy": 100, "energy_unit": "kWh"}.
_UNIT_TO_PARAM_TYPE: dict[str, str] = {
    "kWh": "energy",
    "MWh": "energy",
    "GWh": "energy",
    "MJ": "energy",
    "GJ": "energy",
    "therm": "energy",
    "BTU": "energy",
    "kg": "weight",
    "t": "weight",
    "lb": "weight",
    "g": "weight",
    "ton": "weight",
    "tonne": "weight",
    "short_ton": "weight",
    "long_ton": "weight",
    "km": "distance",
    "mi": "distance",
    "m": "distance",
    "nmi": "distance",
    "ft": "distance",
    "L": "volume",
    "gal": "volume",
    "m3": "volume",
    "ft3": "volume",
    "bbl": "volume",
    "USD": "money",
    "EUR": "money",
    "GBP": "money",
    "TWD": "money",
    "JPY": "money",
    "usd": "money",
    "eur": "money",
    "gbp": "money",
    "number": "number",
    "passenger": "passengers",
    "tonne_km": "weight_distance",
    "tkm": "weight_distance",
}


def _resolve_param_type(unit: str) -> str:
    """Resolve a unit string to its Climatiq parameter type.

    Falls back to ``"energy"`` when the unit is not recognised,
    since electricity estimation is the most common use-case.
    """
    return _UNIT_TO_PARAM_TYPE.get(unit, "energy")


class ClimatiqConnector(BaseConnector):
    """Estimate CO2e emissions using the Climatiq API.

    Endpoint: https://api.climatiq.io/data/v1/estimate
    Auth: API key required (Bearer token).
    """

    BASE_URL = "https://api.climatiq.io/data/v1/estimate"

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

        param_type = _resolve_param_type(activity_unit)

        payload: dict[str, Any] = {
            "emission_factor": {
                "activity_id": emission_factor_id,
                "data_version": "^6",
            },
            "parameters": {
                param_type: activity_value,
                f"{param_type}_unit": activity_unit,
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
