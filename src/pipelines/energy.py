"""Energy domain pipeline — merges all energy connectors."""

from __future__ import annotations

import pandas as pd

from src.connectors.base import ConnectorResult
from src.connectors.energy import (
    CarbonIntensityUKConnector,
    EIAConnector,
    ElectricityMapsConnector,
    NASAPowerConnector,
    NRELConnector,
    OpenMeteoSolarConnector,
    OpenPowerSystemConnector,
    TaiPowerConnector,
)
from src.pipelines.base import BasePipeline


class EnergyPipeline(BasePipeline):
    """Pipeline that orchestrates all energy-domain connectors."""

    @property
    def name(self) -> str:
        return "energy"

    @property
    def domain(self) -> str:
        return "energy"

    def _connector_classes(self) -> list[type]:
        """Return all energy connector classes."""
        return [
            OpenMeteoSolarConnector,
            NASAPowerConnector,
            CarbonIntensityUKConnector,
            OpenPowerSystemConnector,
            EIAConnector,
            ElectricityMapsConnector,
            NRELConnector,
            TaiPowerConnector,
        ]

    def extract(self) -> list[ConnectorResult]:
        """Run each energy connector, catching per-connector errors."""
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
