"""Cross-domain pipeline — correlates energy, climate, and carbon data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.connectors.base import ConnectorResult
from src.pipelines.base import BasePipeline


class CrossDomainPipeline(BasePipeline):
    """Pipeline that reads processed outputs from other pipelines and creates
    cross-domain correlations (energy x climate x carbon).
    """

    @property
    def name(self) -> str:
        return "cross_domain"

    @property
    def domain(self) -> str:
        return "cross_domain"

    def _latest_parquet(self, domain: str) -> Path | None:
        """Find the most recent parquet file for a domain."""
        domain_dir = self._settings.processed_dir / domain
        if not domain_dir.exists():
            return None
        files = sorted(domain_dir.glob("*.parquet"), reverse=True)
        return files[0] if files else None

    def extract(self) -> list[ConnectorResult]:
        """Read the latest processed files from energy, climate, and carbon domains."""
        from datetime import UTC, datetime

        results: list[ConnectorResult] = []
        for domain in ("energy", "climate", "carbon"):
            path = self._latest_parquet(domain)
            if path is None:
                self.logger.warning(f"No processed data found for {domain}")
                continue
            try:
                df = pd.read_parquet(path)
                result = ConnectorResult(
                    data=df,
                    source=f"{domain}_processed",
                    fetched_at=datetime.now(tz=UTC),
                    record_count=len(df),
                    metadata={"path": str(path)},
                )
                results.append(result)
            except Exception as exc:
                self.logger.error(f"Failed to read {domain} data: {exc}")
        return results

    def transform(self, results: list[ConnectorResult]) -> pd.DataFrame:
        """Merge cross-domain data on shared dimensions and add correlation metadata."""
        if not results:
            return pd.DataFrame()

        frames = [r.data.assign(source_pipeline=r.source) for r in results]
        df = pd.concat(frames, ignore_index=True)
        df = df.assign(domain=self.domain)
        df = df.drop_duplicates()

        # Add cross-domain correlation markers when timestamp column exists
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp").reset_index(drop=True)

        return df
