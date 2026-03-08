"""Tests for src.monitor.health_checker."""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

import pytest

from src.monitor.health_checker import (
    check_all,
    check_connector_health,
    generate_summary,
)


def _make_connector(
    name: str = "test_api",
    domain: str = "energy",
    health_result: dict | None = None,
    health_raises: Exception | None = None,
) -> MagicMock:
    """Create a mock connector with configurable health_check behavior."""
    connector = MagicMock()
    type(connector).name = PropertyMock(return_value=name)
    type(connector).domain = PropertyMock(return_value=domain)

    if health_raises is not None:
        connector.health_check.side_effect = health_raises
    else:
        result = health_result or {
            "status": "healthy",
            "latency_ms": 100,
            "message": "OK",
        }
        connector.health_check.return_value = result

    return connector


class TestCheckConnectorHealth:
    """Tests for check_connector_health()."""

    def test_healthy_connector(self) -> None:
        conn = _make_connector(name="solar_api", domain="energy")
        result = check_connector_health(conn)

        assert result["id"] == "solar_api"
        assert result["domain"] == "energy"
        assert result["status"] == "healthy"
        assert result["latency_ms"] == 100
        assert result["message"] == "OK"
        assert "checked_at" in result

    def test_down_connector(self) -> None:
        conn = _make_connector(
            name="broken_api",
            health_result={"status": "down", "latency_ms": 5000, "message": "timeout"},
        )
        result = check_connector_health(conn)

        assert result["status"] == "down"
        assert result["message"] == "timeout"

    def test_degraded_connector(self) -> None:
        conn = _make_connector(
            name="slow_api",
            health_result={"status": "degraded", "latency_ms": 3000, "message": "slow"},
        )
        result = check_connector_health(conn)

        assert result["status"] == "degraded"
        assert result["latency_ms"] == 3000

    def test_health_check_exception_caught(self) -> None:
        """If health_check() itself throws, the connector is marked down."""
        conn = _make_connector(
            name="crash_api",
            health_raises=RuntimeError("connection refused"),
        )
        result = check_connector_health(conn)

        assert result["status"] == "down"
        assert result["latency_ms"] == 0
        assert "connection refused" in result["message"]

    def test_checked_at_is_utc_iso(self) -> None:
        conn = _make_connector()
        result = check_connector_health(conn)

        assert result["checked_at"].endswith("Z")


class TestCheckAll:
    """Tests for check_all()."""

    def test_all_healthy(self) -> None:
        connectors = [_make_connector(name=f"api_{i}") for i in range(3)]
        report = check_all(connectors)

        assert report["total"] == 3
        assert report["healthy"] == 3
        assert report["degraded"] == 0
        assert report["down"] == 0
        assert len(report["apis"]) == 3

    def test_mixed_statuses(self) -> None:
        connectors = [
            _make_connector(name="ok1"),
            _make_connector(name="slow1", health_result={
                "status": "degraded", "latency_ms": 3000, "message": "slow",
            }),
            _make_connector(name="dead1", health_result={
                "status": "down", "latency_ms": 0, "message": "timeout",
            }),
        ]
        report = check_all(connectors)

        assert report["total"] == 3
        assert report["healthy"] == 1
        assert report["degraded"] == 1
        assert report["down"] == 1

    def test_empty_connectors_list(self) -> None:
        report = check_all([])

        assert report["total"] == 0
        assert report["healthy"] == 0
        assert len(report["apis"]) == 0

    def test_exception_in_one_does_not_affect_others(self) -> None:
        connectors = [
            _make_connector(name="good"),
            _make_connector(name="bad", health_raises=RuntimeError("boom")),
            _make_connector(name="also_good"),
        ]
        report = check_all(connectors)

        assert report["total"] == 3
        assert report["healthy"] == 2
        assert report["down"] == 1

    def test_report_has_checked_at(self) -> None:
        report = check_all([_make_connector()])
        assert "checked_at" in report
        assert report["checked_at"].endswith("Z")


class TestGenerateSummary:
    """Tests for generate_summary()."""

    def test_all_healthy_summary(self) -> None:
        report = {
            "checked_at": "2026-03-08T12:00:00Z",
            "total": 3,
            "healthy": 3,
            "degraded": 0,
            "down": 0,
            "apis": [
                {"id": "a", "status": "healthy", "latency_ms": 100, "message": "OK"},
                {"id": "b", "status": "healthy", "latency_ms": 200, "message": "OK"},
                {"id": "c", "status": "healthy", "latency_ms": 150, "message": "OK"},
            ],
        }
        summary = generate_summary(report)

        assert "Healthy: 3" in summary
        assert "Down: 0" in summary
        assert "DOWN:" not in summary

    def test_summary_with_down_apis(self) -> None:
        report = {
            "checked_at": "2026-03-08T12:00:00Z",
            "total": 2,
            "healthy": 1,
            "degraded": 0,
            "down": 1,
            "apis": [
                {"id": "ok_api", "status": "healthy", "latency_ms": 100, "message": "OK"},
                {"id": "bad_api", "status": "down", "latency_ms": 0, "message": "timeout"},
            ],
        }
        summary = generate_summary(report)

        assert "DOWN:" in summary
        assert "bad_api" in summary
        assert "timeout" in summary

    def test_summary_with_degraded_apis(self) -> None:
        report = {
            "checked_at": "2026-03-08T12:00:00Z",
            "total": 1,
            "healthy": 0,
            "degraded": 1,
            "down": 0,
            "apis": [
                {"id": "slow_api", "status": "degraded", "latency_ms": 3000, "message": "slow"},
            ],
        }
        summary = generate_summary(report)

        assert "DEGRADED:" in summary
        assert "slow_api" in summary
        assert "3000ms" in summary
