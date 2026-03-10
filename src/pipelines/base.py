"""Base pipeline interface for ETL processing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.connectors.base import ConnectorResult
from src.utils.config import get_settings
from src.utils.logging import get_logger
from src.utils.telegram import send_telegram


class PipelineError(Exception):
    """Raised when a pipeline encounters an error."""


class BasePipeline(ABC):
    """Abstract base class for all data pipelines.

    A pipeline orchestrates multiple connectors, merges their outputs,
    and writes processed data to the data lake.
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self._settings = get_settings()

    @property
    @abstractmethod
    def name(self) -> str:
        """Pipeline identifier (e.g., 'energy')."""

    @property
    @abstractmethod
    def domain(self) -> str:
        """Domain: energy|climate|environment|agriculture|transport|carbon|cross_domain."""

    @abstractmethod
    def extract(self) -> list[ConnectorResult]:
        """Run all relevant connectors and collect results.

        Returns:
            List of ConnectorResult from each data source.
        """

    @abstractmethod
    def transform(self, results: list[ConnectorResult]) -> pd.DataFrame:
        """Merge and transform connector outputs into a unified DataFrame.

        Args:
            results: Raw connector results.

        Returns:
            Cleaned, merged DataFrame.
        """

    def load(self, df: pd.DataFrame, path: Path | None = None) -> Path:
        """Write processed data to parquet.

        Args:
            df: Processed DataFrame.
            path: Optional custom output path.

        Returns:
            Path to the written file.
        """
        if path is None:
            path = self._output_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        # Coerce mixed-type object columns to numeric where possible
        # (prevents pyarrow ArrowInvalid errors from mixed str/float columns)
        for col in df.select_dtypes(include=["object"]).columns:
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().sum() > df[col].notna().sum() * 0.5:
                df = df.assign(**{col: converted})
        df.to_parquet(path, index=False)
        self.logger.info(f"Saved {len(df)} records to {path}")
        return path

    def _output_path(self) -> Path:
        """Generate the default output path with date partition."""
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        return self._settings.processed_dir / self.domain / f"{self.name}_{date_str}.parquet"

    def notify(self, record_count: int, path: Path) -> None:
        """Send completion notification via Telegram."""
        msg = (
            f"📊 <b>Pipeline: {self.name}</b>\n"
            f"Records: {record_count}\n"
            f"Output: {path.name}\n"
            f"Time: {datetime.utcnow().strftime('%H:%M UTC')}"
        )
        send_telegram(msg)

    def run(self) -> Path:
        """Execute the full pipeline: extract → transform → load → notify.

        Returns:
            Path to the output file.

        Raises:
            PipelineError: If any step fails.
        """
        self.logger.info(f"Starting pipeline: {self.name}")

        try:
            results = self.extract()
            self.logger.info(f"Extracted {len(results)} sources")
        except Exception as e:
            raise PipelineError(f"{self.name}: extract failed - {e}") from e

        try:
            df = self.transform(results)
            self.logger.info(f"Transformed: {len(df)} records")
        except Exception as e:
            raise PipelineError(f"{self.name}: transform failed - {e}") from e

        path = self.load(df)
        self.notify(len(df), path)
        return path
