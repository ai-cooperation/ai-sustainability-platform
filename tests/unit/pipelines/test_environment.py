"""Tests for EnvironmentPipeline."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorResult
from src.pipelines.environment import EnvironmentPipeline


@pytest.fixture
def pipeline():
    with patch("src.pipelines.base.get_settings") as mock_settings, \
         patch("src.pipelines.base.send_telegram"):
        mock_settings.return_value = MagicMock(processed_dir=MagicMock())
        yield EnvironmentPipeline()


@pytest.fixture
def sample_results():
    df1 = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01"]),
        "pm2_5": [35.0],
    })
    df2 = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01"]),
        "water_quality": [7.2],
    })
    return [
        ConnectorResult(data=df1, source="air", fetched_at=datetime(2026, 1, 1), record_count=1),
        ConnectorResult(data=df2, source="water", fetched_at=datetime(2026, 1, 1), record_count=1),
    ]


class TestEnvironmentPipelineProperties:
    def test_name(self, pipeline):
        assert pipeline.name == "environment"

    def test_domain(self, pipeline):
        assert pipeline.domain == "environment"


class TestEnvironmentPipelineExtract:
    def test_extract_catches_errors(self, pipeline):
        failing = MagicMock(side_effect=RuntimeError("err"), __name__="FailingConnector")
        ok_result = ConnectorResult(
            data=pd.DataFrame({"v": [1]}), source="ok",
            fetched_at=datetime(2026, 1, 1), record_count=1,
        )
        ok_cls = MagicMock()
        ok_cls.return_value.run.return_value = ok_result

        with patch.object(pipeline, "_connector_classes", return_value=[failing, ok_cls]):
            results = pipeline.extract()
        assert len(results) == 1

    def test_extract_has_nine_connectors(self, pipeline):
        assert len(pipeline._connector_classes()) == 9


class TestEnvironmentPipelineTransform:
    def test_transform_concatenates(self, pipeline, sample_results):
        df = pipeline.transform(sample_results)
        assert len(df) == 2
        assert (df["domain"] == "environment").all()

    def test_transform_empty(self, pipeline):
        assert pipeline.transform([]).empty

    def test_transform_deduplicates(self, pipeline):
        df1 = pd.DataFrame({"v": [1.0]})
        results = [
            ConnectorResult(data=df1, source="s", fetched_at=datetime(2026, 1, 1), record_count=1),
            ConnectorResult(data=df1, source="s", fetched_at=datetime(2026, 1, 1), record_count=1),
        ]
        assert len(pipeline.transform(results)) == 1
