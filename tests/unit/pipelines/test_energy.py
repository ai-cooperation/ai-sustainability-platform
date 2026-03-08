"""Tests for EnergyPipeline."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorResult
from src.pipelines.energy import EnergyPipeline


@pytest.fixture
def pipeline():
    with patch("src.pipelines.base.get_settings") as mock_settings, \
         patch("src.pipelines.base.send_telegram"):
        mock_settings.return_value = MagicMock(
            processed_dir=MagicMock(),
        )
        yield EnergyPipeline()


@pytest.fixture
def sample_results():
    """Two ConnectorResult objects with overlapping rows for dedup testing."""
    df1 = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        "value": [10.0, 20.0],
    })
    df2 = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-02", "2026-01-03"]),
        "value": [20.0, 30.0],
    })
    return [
        ConnectorResult(data=df1, source="solar", fetched_at=datetime(2026, 1, 1), record_count=2),
        ConnectorResult(data=df2, source="wind", fetched_at=datetime(2026, 1, 1), record_count=2),
    ]


class TestEnergyPipelineProperties:
    def test_name(self, pipeline):
        assert pipeline.name == "energy"

    def test_domain(self, pipeline):
        assert pipeline.domain == "energy"


class TestEnergyPipelineExtract:
    def test_extract_catches_connector_errors(self, pipeline):
        """Pipeline should not fail if one connector raises."""
        failing_cls = MagicMock(side_effect=RuntimeError("API down"), __name__="FailingConnector")
        ok_result = ConnectorResult(
            data=pd.DataFrame({"timestamp": [datetime(2026, 1, 1)], "v": [1]}),
            source="ok",
            fetched_at=datetime(2026, 1, 1),
            record_count=1,
        )
        ok_cls = MagicMock()
        ok_cls.return_value.run.return_value = ok_result

        with patch.object(pipeline, "_connector_classes", return_value=[failing_cls, ok_cls]):
            results = pipeline.extract()

        assert len(results) == 1
        assert results[0].source == "ok"

    def test_extract_all_fail_returns_empty(self, pipeline):
        failing = MagicMock(side_effect=RuntimeError("boom"), __name__="FailingConnector")
        with patch.object(pipeline, "_connector_classes", return_value=[failing, failing]):
            results = pipeline.extract()
        assert results == []

    def test_extract_has_seven_connectors(self, pipeline):
        assert len(pipeline._connector_classes()) == 7


class TestEnergyPipelineTransform:
    def test_transform_concatenates(self, pipeline, sample_results):
        df = pipeline.transform(sample_results)
        # 4 rows before dedup, but row with timestamp=2026-01-02, value=20.0
        # appears in both with different source, so all 4 remain
        assert len(df) == 4
        assert "domain" in df.columns
        assert "source" in df.columns
        assert (df["domain"] == "energy").all()

    def test_transform_deduplicates(self, pipeline):
        """Identical rows across connectors should be deduped."""
        df1 = pd.DataFrame({"timestamp": pd.to_datetime(["2026-01-01"]), "v": [1.0]})
        results = [
            ConnectorResult(
                data=df1, source="src_a",
                fetched_at=datetime(2026, 1, 1),
                record_count=1,
            ),
            ConnectorResult(
                data=df1, source="src_a",
                fetched_at=datetime(2026, 1, 1),
                record_count=1,
            ),
        ]
        df = pipeline.transform(results)
        assert len(df) == 1

    def test_transform_empty_results(self, pipeline):
        df = pipeline.transform([])
        assert df.empty

    def test_transform_adds_domain_column(self, pipeline, sample_results):
        df = pipeline.transform(sample_results)
        assert set(df["domain"].unique()) == {"energy"}
