"""Shared test fixtures."""

from __future__ import annotations

import pytest

from src.utils.config import Settings


@pytest.fixture
def settings():
    """Test settings with no real API keys."""
    return Settings(
        groq_api_key="test-key",
        data_dir="data",
    )


@pytest.fixture
def sample_connector_result():
    """Sample ConnectorResult for testing."""
    import pandas as pd
    from datetime import datetime
    from src.connectors.base import ConnectorResult

    df = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        "value": [42.0, 43.0],
    })
    return ConnectorResult(
        data=df,
        source="test_connector",
        fetched_at=datetime(2026, 1, 1),
        record_count=2,
    )
