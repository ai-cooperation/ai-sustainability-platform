"""Tests for src.monitor.reporter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.monitor.reporter import (
    detect_changes,
    format_change_notification,
    format_telegram_report,
    load_previous_status,
    save_history,
    save_status,
)


def _make_report(
    apis: list[dict] | None = None,
    healthy: int = 2,
    down: int = 0,
    degraded: int = 0,
) -> dict:
    """Create a test health check report."""
    if apis is None:
        apis = [
            {"id": "api_a", "domain": "energy", "status": "healthy",
             "latency_ms": 100, "message": "OK", "checked_at": "2026-03-08T12:00:00Z"},
            {"id": "api_b", "domain": "climate", "status": "healthy",
             "latency_ms": 200, "message": "OK", "checked_at": "2026-03-08T12:00:00Z"},
        ]
    return {
        "checked_at": "2026-03-08T12:00:00Z",
        "total": len(apis),
        "healthy": healthy,
        "degraded": degraded,
        "down": down,
        "apis": apis,
    }


class TestSaveStatus:
    """Tests for save_status()."""

    def test_saves_json_file(self, tmp_path: Path) -> None:
        report = _make_report()
        out = tmp_path / "status.json"
        result = save_status(report, path=out)

        assert result == out
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["total"] == 2

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        out = tmp_path / "deep" / "nested" / "status.json"
        save_status(_make_report(), path=out)

        assert out.exists()

    def test_overwrites_existing(self, tmp_path: Path) -> None:
        out = tmp_path / "status.json"
        save_status(_make_report(healthy=2), path=out)
        save_status(_make_report(healthy=5, apis=[
            {"id": f"api_{i}", "domain": "energy", "status": "healthy",
             "latency_ms": 100, "message": "OK", "checked_at": "2026-03-08T12:00:00Z"}
            for i in range(5)
        ]), path=out)

        data = json.loads(out.read_text())
        assert data["healthy"] == 5


class TestSaveHistory:
    """Tests for save_history()."""

    def test_creates_daily_file(self, tmp_path: Path) -> None:
        report = _make_report()
        result = save_history(report, base_dir=tmp_path)

        assert result.exists()
        assert result.suffix == ".json"
        entries = json.loads(result.read_text())
        assert len(entries) == 1

    def test_appends_to_existing_file(self, tmp_path: Path) -> None:
        report1 = _make_report()
        path = save_history(report1, base_dir=tmp_path)

        report2 = _make_report(healthy=1, down=1)
        save_history(report2, base_dir=tmp_path)

        entries = json.loads(path.read_text())
        assert len(entries) == 2

    def test_handles_corrupted_history(self, tmp_path: Path) -> None:
        # Write corrupted JSON
        from datetime import datetime, timezone
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        corrupted = tmp_path / f"{today}.json"
        corrupted.write_text("not valid json{{{")

        report = _make_report()
        save_history(report, base_dir=tmp_path)

        entries = json.loads(corrupted.read_text())
        assert len(entries) == 1


class TestFormatTelegramReport:
    """Tests for format_telegram_report()."""

    def test_all_healthy(self) -> None:
        report = _make_report()
        text = format_telegram_report(report)

        assert "<b>API Health Report</b>" in text
        assert "Healthy: 2" in text
        assert "Down: 0" in text

    def test_includes_down_apis(self) -> None:
        apis = [
            {"id": "dead_api", "domain": "energy", "status": "down",
             "latency_ms": 0, "message": "timeout", "checked_at": "2026-03-08T12:00:00Z"},
        ]
        report = _make_report(apis=apis, healthy=0, down=1)
        text = format_telegram_report(report)

        assert "<b>DOWN:</b>" in text
        assert "dead_api" in text
        assert "timeout" in text

    def test_includes_degraded_apis(self) -> None:
        apis = [
            {"id": "slow_api", "domain": "climate", "status": "degraded",
             "latency_ms": 3000, "message": "slow", "checked_at": "2026-03-08T12:00:00Z"},
        ]
        report = _make_report(apis=apis, healthy=0, degraded=1)
        text = format_telegram_report(report)

        assert "<b>DEGRADED:</b>" in text
        assert "slow_api" in text
        assert "3000ms" in text


class TestDetectChanges:
    """Tests for detect_changes()."""

    def test_no_previous_returns_empty(self) -> None:
        current = _make_report()
        changes = detect_changes(current, None)
        assert changes == []

    def test_no_changes(self) -> None:
        report = _make_report()
        changes = detect_changes(report, report)
        assert changes == []

    def test_detects_healthy_to_down(self) -> None:
        previous = _make_report(apis=[
            {"id": "api_a", "status": "healthy", "domain": "energy",
             "latency_ms": 100, "message": "OK", "checked_at": "2026-03-08T11:00:00Z"},
        ], healthy=1)
        current = _make_report(apis=[
            {"id": "api_a", "status": "down", "domain": "energy",
             "latency_ms": 0, "message": "timeout", "checked_at": "2026-03-08T12:00:00Z"},
        ], healthy=0, down=1)

        changes = detect_changes(current, previous)
        assert len(changes) == 1
        assert changes[0]["id"] == "api_a"
        assert changes[0]["old_status"] == "healthy"
        assert changes[0]["new_status"] == "down"

    def test_detects_down_to_healthy(self) -> None:
        previous = _make_report(apis=[
            {"id": "api_a", "status": "down", "domain": "energy",
             "latency_ms": 0, "message": "err", "checked_at": "2026-03-08T11:00:00Z"},
        ], healthy=0, down=1)
        current = _make_report(apis=[
            {"id": "api_a", "status": "healthy", "domain": "energy",
             "latency_ms": 100, "message": "OK", "checked_at": "2026-03-08T12:00:00Z"},
        ], healthy=1, down=0)

        changes = detect_changes(current, previous)
        assert len(changes) == 1
        assert changes[0]["new_status"] == "healthy"

    def test_new_api_not_in_previous_is_not_a_change(self) -> None:
        previous = _make_report(apis=[
            {"id": "api_a", "status": "healthy", "domain": "energy",
             "latency_ms": 100, "message": "OK", "checked_at": "2026-03-08T11:00:00Z"},
        ], healthy=1)
        current = _make_report(apis=[
            {"id": "api_a", "status": "healthy", "domain": "energy",
             "latency_ms": 100, "message": "OK", "checked_at": "2026-03-08T12:00:00Z"},
            {"id": "api_b", "status": "down", "domain": "climate",
             "latency_ms": 0, "message": "err", "checked_at": "2026-03-08T12:00:00Z"},
        ], healthy=1, down=1)

        changes = detect_changes(current, previous)
        assert len(changes) == 0


class TestFormatChangeNotification:
    """Tests for format_change_notification()."""

    def test_formats_changes(self) -> None:
        changes = [
            {"id": "api_a", "old_status": "healthy", "new_status": "down"},
            {"id": "api_b", "old_status": "down", "new_status": "healthy"},
        ]
        text = format_change_notification(changes)

        assert "Status Changes" in text
        assert "api_a" in text
        assert "api_b" in text
        assert "healthy -> down" in text
        assert "down -> healthy" in text


class TestLoadPreviousStatus:
    """Tests for load_previous_status()."""

    def test_returns_none_if_no_file(self, tmp_path: Path) -> None:
        result = load_previous_status(tmp_path / "nonexistent.json")
        assert result is None

    def test_loads_valid_json(self, tmp_path: Path) -> None:
        path = tmp_path / "status.json"
        report = _make_report()
        path.write_text(json.dumps(report))

        result = load_previous_status(path)
        assert result is not None
        assert result["total"] == 2

    def test_returns_none_on_corrupted(self, tmp_path: Path) -> None:
        path = tmp_path / "status.json"
        path.write_text("not json")

        result = load_previous_status(path)
        assert result is None
