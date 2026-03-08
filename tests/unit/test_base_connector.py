"""Tests for BaseConnector."""

from __future__ import annotations

import pandas as pd
import pytest

from src.connectors.base import BaseConnector, ConnectorError, ConnectorResult, ValidationError


class MockConnector(BaseConnector):
    """Concrete connector for testing."""

    @property
    def name(self) -> str:
        return "mock_connector"

    @property
    def domain(self) -> str:
        return "energy"

    def fetch(self, **params):
        return {"values": [{"timestamp": "2026-01-01", "value": 42.0}]}

    def normalize(self, raw_data):
        df = pd.DataFrame(raw_data["values"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df


class FailingConnector(BaseConnector):
    """Connector that always fails on fetch."""

    @property
    def name(self) -> str:
        return "failing_connector"

    @property
    def domain(self) -> str:
        return "climate"

    def fetch(self, **params):
        raise ConnectionError("API is down")

    def normalize(self, raw_data):
        return pd.DataFrame()


class EmptyConnector(BaseConnector):
    """Connector that returns empty data."""

    @property
    def name(self) -> str:
        return "empty_connector"

    @property
    def domain(self) -> str:
        return "environment"

    def fetch(self, **params):
        return {"values": []}

    def normalize(self, raw_data):
        return pd.DataFrame()


class TestBaseConnector:
    def test_run_success(self):
        conn = MockConnector()
        result = conn.run()
        assert isinstance(result, ConnectorResult)
        assert result.source == "mock_connector"
        assert result.record_count == 1
        assert "timestamp" in result.data.columns

    def test_run_fetch_failure(self):
        conn = FailingConnector()
        with pytest.raises(ConnectorError, match="fetch failed"):
            conn.run()

    def test_run_empty_data_raises(self):
        conn = EmptyConnector()
        with pytest.raises(ValidationError, match="empty"):
            conn.run()

    def test_health_check_healthy(self):
        conn = MockConnector()
        result = conn.health_check()
        assert result["status"] == "healthy"
        assert "latency_ms" in result

    def test_health_check_down(self):
        conn = FailingConnector()
        result = conn.health_check()
        assert result["status"] == "down"

    def test_result_is_immutable(self):
        conn = MockConnector()
        result = conn.run()
        with pytest.raises(AttributeError):
            result.source = "modified"
