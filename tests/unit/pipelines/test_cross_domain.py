"""Tests for CrossDomainPipeline."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorResult
from src.pipelines.cross_domain import CrossDomainPipeline


@pytest.fixture
def pipeline():
    with patch("src.pipelines.base.get_settings") as mock_settings, \
         patch("src.pipelines.base.send_telegram"):
        mock_settings.return_value = MagicMock(
            processed_dir=Path("/tmp/test_processed"),
        )
        yield CrossDomainPipeline()


@pytest.fixture
def sample_results():
    df_energy = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        "carbon_intensity": [180.0, 195.0],
        "source": ["energy_processed", "energy_processed"],
    })
    df_climate = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        "temperature": [12.5, 13.0],
        "source": ["climate_processed", "climate_processed"],
    })
    return [
        ConnectorResult(
            data=df_energy, source="energy_processed",
            fetched_at=datetime(2026, 1, 1), record_count=2,
        ),
        ConnectorResult(
            data=df_climate, source="climate_processed",
            fetched_at=datetime(2026, 1, 1), record_count=2,
        ),
    ]


class TestCrossDomainPipelineProperties:
    def test_name(self, pipeline):
        assert pipeline.name == "cross_domain"

    def test_domain(self, pipeline):
        assert pipeline.domain == "cross_domain"


class TestCrossDomainPipelineExtract:
    def test_extract_skips_missing_domains(self, pipeline):
        """When no parquet files exist, extract returns empty."""
        results = pipeline.extract()
        assert results == []

    def test_extract_reads_parquet(self, pipeline, tmp_path):
        """When parquet files exist, they are read into ConnectorResults."""
        energy_dir = tmp_path / "energy"
        energy_dir.mkdir()
        df = pd.DataFrame({"timestamp": pd.to_datetime(["2026-01-01"]), "v": [1.0]})
        df.to_parquet(energy_dir / "energy_2026-01-01.parquet")

        pipeline._settings.processed_dir = tmp_path
        results = pipeline.extract()
        # Only energy exists, climate and carbon dirs missing
        assert len(results) == 1
        assert results[0].source == "energy_processed"


class TestCrossDomainPipelineTransform:
    def test_transform_concatenates(self, pipeline, sample_results):
        df = pipeline.transform(sample_results)
        assert len(df) == 4
        assert "domain" in df.columns
        assert (df["domain"] == "cross_domain").all()

    def test_transform_sorts_by_timestamp(self, pipeline, sample_results):
        df = pipeline.transform(sample_results)
        timestamps = df["timestamp"].tolist()
        assert timestamps == sorted(timestamps)

    def test_transform_empty(self, pipeline):
        assert pipeline.transform([]).empty

    def test_transform_deduplicates(self, pipeline):
        df1 = pd.DataFrame({
            "timestamp": pd.to_datetime(["2026-01-01"]),
            "v": [1.0],
        })
        results = [
            ConnectorResult(data=df1, source="a", fetched_at=datetime(2026, 1, 1), record_count=1),
            ConnectorResult(data=df1, source="a", fetched_at=datetime(2026, 1, 1), record_count=1),
        ]
        assert len(pipeline.transform(results)) == 1
