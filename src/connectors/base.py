"""Base connector interface for all data sources."""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from src.utils.config import get_settings
from src.utils.logging import get_logger


class ConnectorError(Exception):
    """Raised when a connector encounters an error."""


class ValidationError(ConnectorError):
    """Raised when data validation fails."""


@dataclass(frozen=True)
class ConnectorResult:
    """Immutable result from a connector run."""

    data: pd.DataFrame
    source: str
    fetched_at: datetime
    record_count: int
    metadata: dict = field(default_factory=dict)


class BaseConnector(ABC):
    """Abstract base class for all data connectors.

    Every connector must implement:
        - name: unique identifier
        - domain: one of energy|climate|environment|agriculture|transport|carbon
        - fetch(): retrieve raw data from API
        - normalize(): convert raw data to standardized DataFrame
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)
        self._settings = get_settings()

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique connector identifier (e.g., 'open_meteo_solar')."""

    @property
    @abstractmethod
    def domain(self) -> str:
        """Domain: energy|climate|environment|agriculture|transport|carbon."""

    @abstractmethod
    def fetch(self, **params: Any) -> dict | list:
        """Fetch raw data from the API.

        Args:
            **params: Query parameters specific to the connector.

        Returns:
            Raw API response data.

        Raises:
            ConnectorError: If the API call fails.
        """

    @abstractmethod
    def normalize(self, raw_data: dict | list) -> pd.DataFrame:
        """Convert raw API data to a standardized DataFrame.

        The DataFrame must include a 'timestamp' column (datetime64).

        Args:
            raw_data: Raw data from fetch().

        Returns:
            Normalized pandas DataFrame.
        """

    def validate(self, df: pd.DataFrame) -> bool:
        """Validate the normalized DataFrame.

        Args:
            df: DataFrame to validate.

        Returns:
            True if valid.

        Raises:
            ValidationError: If validation fails.
        """
        if df.empty:
            raise ValidationError(f"{self.name}: DataFrame is empty")
        return True

    def health_check(self) -> dict:
        """Check API availability.

        Returns:
            Dict with keys: status (healthy|degraded|down), latency_ms, message.
        """
        start = time.time()
        try:
            self.fetch(**self._health_check_params())
            latency = (time.time() - start) * 1000
            return {"status": "healthy", "latency_ms": round(latency), "message": "OK"}
        except Exception as e:
            latency = (time.time() - start) * 1000
            return {"status": "down", "latency_ms": round(latency), "message": str(e)}

    def _health_check_params(self) -> dict:
        """Override to provide minimal params for health check."""
        return {}

    def run(self, **params: Any) -> ConnectorResult:
        """Execute the full connector pipeline: fetch → normalize → validate.

        Args:
            **params: Query parameters passed to fetch().

        Returns:
            ConnectorResult with normalized data.

        Raises:
            ConnectorError: If any step fails.
        """
        self.logger.info(f"Running connector: {self.name}")

        try:
            raw = self.fetch(**params)
        except Exception as e:
            raise ConnectorError(f"{self.name}: fetch failed - {e}") from e

        try:
            df = self.normalize(raw)
        except Exception as e:
            raise ConnectorError(f"{self.name}: normalize failed - {e}") from e

        self.validate(df)

        result = ConnectorResult(
            data=df,
            source=self.name,
            fetched_at=datetime.now(tz=UTC),
            record_count=len(df),
            metadata={"params": params},
        )
        self.logger.info(f"{self.name}: fetched {result.record_count} records")
        return result

    # --- Caching helpers ---

    def _cache_path(self, params: dict) -> Path:
        """Generate a cache file path for given params."""
        key = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
        cache_dir = self._settings.cache_dir / self.domain / self.name
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"{key}.json"

    def _read_cache(self, params: dict, max_age_seconds: int = 3600) -> dict | list | None:
        """Read cached data if fresh enough."""
        path = self._cache_path(params)
        if not path.exists():
            return None
        age = time.time() - path.stat().st_mtime
        if age > max_age_seconds:
            return None
        self.logger.debug(f"Cache hit: {path}")
        return json.loads(path.read_text())

    def _write_cache(self, params: dict, data: dict | list) -> None:
        """Write data to cache."""
        path = self._cache_path(params)
        path.write_text(json.dumps(data))
