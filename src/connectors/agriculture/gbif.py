"""Global Biodiversity Information Facility (GBIF) occurrence connector."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests

from src.connectors.base import BaseConnector, ConnectorError


class GBIFConnector(BaseConnector):
    """Fetch species occurrence data from the GBIF API.

    Endpoint: https://api.gbif.org/v1/occurrence/search
    Auth: Not required for basic occurrence search.
    """

    BASE_URL = "https://api.gbif.org/v1/occurrence/search"

    @property
    def name(self) -> str:
        return "gbif"

    @property
    def domain(self) -> str:
        return "agriculture"

    def fetch(self, **params: Any) -> dict:
        """Fetch species occurrence data from GBIF.

        Args:
            country: Two-letter country code (e.g., "TW", "US").
            limit: Maximum records to return (default 300, max 300).
            offset: Pagination offset (default 0).
            taxon_key: GBIF taxon key for species filtering.
            year: Year or year range (e.g., "2020,2023").
            has_coordinate: Whether to require coordinates (default True).

        Returns:
            Raw JSON response dict.
        """
        query_params: dict[str, Any] = {
            "limit": min(params.get("limit", 300), 300),
            "offset": params.get("offset", 0),
            "hasCoordinate": params.get("has_coordinate", True),
        }

        country = params.get("country")
        if country:
            query_params["country"] = country

        taxon_key = params.get("taxon_key")
        if taxon_key:
            query_params["taxonKey"] = taxon_key

        year = params.get("year")
        if year:
            query_params["year"] = year

        try:
            response = requests.get(
                self.BASE_URL, params=query_params, timeout=30
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ConnectorError(
                f"GBIF API request failed: {exc}"
            ) from exc

        data = response.json()
        if not isinstance(data, dict):
            raise ConnectorError(
                f"GBIF API returned unexpected format: expected dict, got {type(data).__name__}"
            )
        return data

    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw GBIF response to a standardized DataFrame.

        Returns:
            DataFrame with columns: timestamp, species, country, latitude,
            longitude, dataset.
        """
        if not isinstance(raw_data, dict):
            raise ConnectorError("Expected dict response from GBIF API")

        results = raw_data.get("results")
        if results is None:
            raise ConnectorError("Missing 'results' key in GBIF response")

        if not results:
            raise ConnectorError("GBIF response contains no occurrence records")

        rows = []
        for record in results:
            event_date = record.get("eventDate")
            year = record.get("year")

            if event_date:
                try:
                    timestamp = pd.Timestamp(event_date)
                except (ValueError, TypeError):
                    timestamp = (
                        pd.Timestamp(year=int(year), month=1, day=1)
                        if year
                        else None
                    )
            elif year:
                timestamp = pd.Timestamp(year=int(year), month=1, day=1)
            else:
                continue

            rows.append(
                {
                    "timestamp": timestamp,
                    "species": record.get("species", record.get("scientificName", "")),
                    "country": record.get("country", ""),
                    "latitude": record.get("decimalLatitude"),
                    "longitude": record.get("decimalLongitude"),
                    "dataset": record.get("datasetName", ""),
                }
            )

        if not rows:
            raise ConnectorError("No valid occurrence records found in GBIF response")

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def _health_check_params(self) -> dict:
        """Minimal params for health check."""
        return {"country": "TW", "limit": 1}
