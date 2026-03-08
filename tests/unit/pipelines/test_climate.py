"""Tests for ClimatePipeline."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.connectors.base import ConnectorResult
from src.pipelines.climate import ClimatePipeline


@pytest.fixture
def pipeline():
    with patch("src.pipelines.base.get_settings") as mock_settings, \
         patch("src.pipelines.base.send_telegram"):
        mock_settings.return_value = MagicMock(processed_dir=MagicMock())
        yield ClimatePipeline()


@pytest.fixture
def sample_results():
    df1 = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01"]),
        "temperature": [15.2],
    })
    df2 = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01"]),
        "co2_ppm": [421.5],
    })
    return [
        ConnectorResult(data=df1, source="weather", fetched_at=datetime(2026, 1, 1), record_count=1),
        ConnectorResult(data=df2, source="ghg", fetched_at=datetime(2026, 1, 1), record_count=1),
    ]


class TestClimatePipelineProperties:
    def test_name(self, pipeline):
        assert pipeline.name == "climate"

    def test_domain(self, pipeline):
        assert pipeline.domain == "climate"


class TestClimatePipelineExtract:
    def test_extract_catches_errors(self, pipeline):
        failing = MagicMock(side_effect=RuntimeError("down"), __name__="FailingConnector")
        ok_result = ConnectorResult(
            data=pd.DataFrame({"t": [1]}), source="ok",
            fetched_at=datetime(2026, 1, 1), record_count=1,
        )
        ok_cls = MagicMock()
        ok_cls.return_value.run.return_value = ok_result

        with patch.object(pipeline, "_connector_classes", return_value=[failing, ok_cls]):
            results = pipeline.extract()
        assert len(results) == 1

    def test_extract_has_six_connectors(self, pipeline):
        assert len(pipeline._connector_classes()) == 6


class TestClimatePipelineTransform:
    def test_transform_concatenates(self, pipeline, sample_results):
        df = pipeline.transform(sample_results)
        assert len(df) == 2
        assert "domain" in df.columns
        assert (df["domain"] == "climate").all()

    def test_transform_empty(self, pipeline):
        assert pipeline.transform([]).empty

    def test_transform_deduplicates(self, pipeline):
        df1 = pd.DataFrame({"v": [1.0]})
        results = [
            ConnectorResult(data=df1, source="s", fetched_at=datetime(2026, 1, 1), record_count=1),
            ConnectorResult(data=df1, source="s", fetched_at=datetime(2026, 1, 1), record_count=1),
        ]
        assert len(pipeline.transform(results)) == 1
