"""Climate domain pipeline — merges all climate connectors."""

from __future__ import annotations

import pandas as pd

from src.connectors.base import ConnectorResult
from src.connectors.climate import (
    CopernicusCDSConnector,
    NOAACDOConnector,
    NOAAGHGConnector,
    OpenMeteoClimateConnector,
    OpenMeteoWeatherConnector,
    WorldBankClimateConnector,
)
from src.pipelines.base import BasePipeline


class ClimatePipeline(BasePipeline):
    """Pipeline that orchestrates all climate-domain connectors."""

    @property
    def name(self) -> str:
        return "climate"

    @property
    def domain(self) -> str:
        return "climate"

    def _connector_classes(self) -> list[type]:
        """Return all climate connector classes."""
        return [
            OpenMeteoWeatherConnector,
            OpenMeteoClimateConnector,
            NOAAGHGConnector,
            WorldBankClimateConnector,
            NOAACDOConnector,
            CopernicusCDSConnector,
        ]

    def extract(self) -> list[ConnectorResult]:
        """Run each climate connector, catching per-connector errors."""
        results: list[ConnectorResult] = []
        for cls in self._connector_classes():
            try:
                connector = cls()
                result = connector.run()
                results.append(result)
            except Exception as exc:
                self.logger.error(f"Connector {cls.__name__} failed: {exc}")
        return results

    def transform(self, results: list[ConnectorResult]) -> pd.DataFrame:
        """Concatenate connector outputs, add domain column, deduplicate."""
        if not results:
            return pd.DataFrame()

        frames = [r.data.assign(source=r.source) for r in results]
        df = pd.concat(frames, ignore_index=True)
        df = df.assign(domain=self.domain)
        df = df.drop_duplicates()
        return df
