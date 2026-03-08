"""AQICN (World Air Quality Index) API connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class AQICNConnector(BaseConnector):
    """Connector for AQICN / WAQI API.

    Endpoint: https://api.waqi.info/feed/{city}/
    Auth: Token (AQICN_API_TOKEN)
    """

    BASE_URL = "https://api.waqi.info"

    @property
    def name(self) -> str:
        return "aqicn"

    @property
    def domain(self) -> str:
        return "environment"

    def _get_api_token(self) -> str:
        """Retrieve AQICN API token from settings.

        Raises:
            ConnectorError: If API token is not configured.
        """
        token = self._settings.aqicn_api_token
        if not token:
            raise ConnectorError(
                f"{self.name}: AQICN_API_TOKEN not configured"
            )
        return token

    def fetch(self, **params: Any) -> dict:
        """Fetch air quality data from AQICN.

        Args:
            city: City name or station ID (default: 'beijing').

        Returns:
            Raw JSON response dict.

        Raises:
            ConnectorError: If the API call fails.
        """
        token = self._get_api_token()
        city = params.get("city", "beijing")
        url = f"{self.BASE_URL}/feed/{city}/"

        try:
            response = requests.get(
                url, params={"token": token}, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"{self.name}: API request failed - {exc}"
            ) from exc

        data = response.json()
        if data.get("status") != "ok":
            message = data.get("data", "unknown error")
            raise ConnectorError(
                f"{self.name}: API returned error status - {message}"
            )
        return data

    def normalize(self, raw_data: dict) -> pd.DataFrame:
        """Convert raw AQICN data to a DataFrame.

        Args:
            raw_data: Raw API response dict.

        Returns:
            DataFrame with columns: timestamp, city, aqi, pm25, pm10,
            o3, no2, so2, co.
        """
        data = raw_data.get("data", {})
        if not data:
            raise ConnectorError(f"{self.name}: no data in response")

        iaqi = data.get("iaqi", {})
        time_info = data.get("time", {})

        row = {
            "timestamp": time_info.get("iso"),
            "city": data.get("city", {}).get("name", ""),
            "aqi": data.get("aqi"),
            "pm25": iaqi.get("pm25", {}).get("v"),
            "pm10": iaqi.get("pm10", {}).get("v"),
            "o3": iaqi.get("o3", {}).get("v"),
            "no2": iaqi.get("no2", {}).get("v"),
            "so2": iaqi.get("so2", {}).get("v"),
            "co": iaqi.get("co", {}).get("v"),
        }

        df = pd.DataFrame([row])
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df

    def _health_check_params(self) -> dict:
        return {"city": "beijing"}
