"""Copernicus Climate Data Store (CDS) connector using cdsapi."""

from __future__ import annotations

import time
from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class CopernicusCDSConnector(BaseConnector):
    """Fetch climate reanalysis data from Copernicus CDS.

    Uses the cdsapi package (optional dependency) for queue-based retrieval.
    Auth: CDS API key (COPERNICUS_CDS_KEY or ~/.cdsapirc)

    Install cdsapi: pip install cdsapi
    """

    @property
    def name(self) -> str:
        return "copernicus_cds"

    @property
    def domain(self) -> str:
        return "climate"

    def _get_client(self) -> Any:
        """Create a cdsapi Client instance.

        Returns:
            cdsapi.Client instance.

        Raises:
            ConnectorError: If cdsapi is not installed or key is missing.
        """
        try:
            import cdsapi  # noqa: F811
        except ImportError as e:
            raise ConnectorError(
                f"{self.name}: cdsapi package is not installed. "
                "Install it with: pip install cdsapi"
            ) from e

        cds_key = self._settings.copernicus_cds_key
        if not cds_key:
            raise ConnectorError(
                f"{self.name}: Copernicus CDS key not configured. "
                "Set COPERNICUS_CDS_KEY in environment or .env file, "
                "or create a ~/.cdsapirc file."
            )

        try:
            client = cdsapi.Client(
                url="https://cds.climate.copernicus.eu/api",
                key=cds_key,
            )
            return client
        except Exception as e:
            raise ConnectorError(f"{self.name}: failed to create CDS client - {e}") from e

    def fetch(self, **params: Any) -> dict:
        """Fetch data from Copernicus CDS (queue-based retrieval).

        Args:
            dataset: CDS dataset name
                (default: 'reanalysis-era5-single-levels-monthly-means').
            product_type: Product type (default: 'monthly_averaged_reanalysis').
            variable: Variable(s) to retrieve (default: '2m_temperature').
            year: Year(s) to retrieve (default: ['2023']).
            month: Month(s) to retrieve (default: all 12 months).
            time: Time of day (default: '00:00').
            area: Bounding box [N, W, S, E] (optional).
            format: Output format (default: 'netcdf').

        Returns:
            Dict with downloaded data information and parsed values.

        Raises:
            ConnectorError: If the retrieval fails.
        """
        client = self._get_client()

        dataset = params.get("dataset", "reanalysis-era5-single-levels-monthly-means")
        request_body = {
            "product_type": params.get("product_type", "monthly_averaged_reanalysis"),
            "variable": params.get("variable", "2m_temperature"),
            "year": params.get("year", ["2023"]),
            "month": params.get(
                "month",
                [f"{m:02d}" for m in range(1, 13)],
            ),
            "time": params.get("time", "00:00"),
            "format": params.get("format", "netcdf"),
        }

        if "area" in params:
            request_body["area"] = params["area"]

        try:
            result = client.retrieve(dataset, request_body)
            return {
                "result": str(result),
                "dataset": dataset,
                "request": request_body,
            }
        except Exception as e:
            raise ConnectorError(f"{self.name}: CDS retrieval failed - {e}") from e

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert CDS response metadata to a tracking DataFrame.

        Since CDS returns NetCDF files that require xarray for full parsing,
        this normalize method creates a summary DataFrame from the request
        metadata.

        Args:
            raw_data: Dict with CDS result information.

        Returns:
            DataFrame with columns: timestamp, dataset, variable, status.

        Raises:
            ConnectorError: If response structure is unexpected.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError(f"{self.name}: expected dict, got {type(raw_data).__name__}")

        request_info = raw_data.get("request", {})
        dataset = raw_data.get("dataset", "unknown")

        years = request_info.get("year", [])
        months = request_info.get("month", [])
        variable = request_info.get("variable", "unknown")

        if isinstance(years, str):
            years = [years]
        if isinstance(months, str):
            months = [months]

        records = []
        for year in years:
            for month in months:
                records.append({
                    "timestamp": pd.Timestamp(year=int(year), month=int(month), day=1),
                    "dataset": dataset,
                    "variable": variable,
                    "status": "retrieved",
                })

        if not records:
            raise ConnectorError(f"{self.name}: could not build records from request metadata")

        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def health_check(self) -> dict:
        """Check CDS API availability via HTTP without requiring cdsapi package.

        Uses a lightweight HTTP HEAD/GET request to the CDS API endpoint
        instead of going through the full cdsapi client flow.

        Returns:
            Dict with keys: status (healthy|degraded|down), latency_ms, message.
        """
        cds_api_url = "https://cds.climate.copernicus.eu/api"
        start = time.time()
        try:
            resp = requests.get(cds_api_url, timeout=15)
            latency = (time.time() - start) * 1000
            if resp.status_code < 500:
                return {
                    "status": "healthy",
                    "latency_ms": round(latency),
                    "message": f"CDS API reachable (HTTP {resp.status_code})",
                }
            return {
                "status": "degraded",
                "latency_ms": round(latency),
                "message": f"CDS API returned HTTP {resp.status_code}",
            }
        except requests.RequestException as e:
            latency = (time.time() - start) * 1000
            return {"status": "down", "latency_ms": round(latency), "message": str(e)}

    def _health_check_params(self) -> dict:
        """Minimal params for health check (used if base health_check is called)."""
        return {
            "dataset": "reanalysis-era5-single-levels-monthly-means",
            "year": ["2023"],
            "month": ["01"],
        }
