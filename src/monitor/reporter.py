"""Health check reporting: persistence and Telegram notifications."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.utils.config import get_settings
from src.utils.logging import get_logger
from src.utils.telegram import send_telegram

logger = get_logger(__name__)


def save_status(report: dict[str, Any], path: Path | None = None) -> Path:
    """Save the current status report to JSON.

    Args:
        report: Health check report from check_all().
        path: Optional output path. Defaults to data/status/status.json.

    Returns:
        Path to the saved file.
    """
    if path is None:
        settings = get_settings()
        path = settings.data_dir / "status" / "status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    logger.info(f"Status saved to {path}")
    return path


def save_history(report: dict[str, Any], base_dir: Path | None = None) -> Path:
    """Append the report to the daily history file.

    Each day gets its own file: data/status/history/YYYY-MM-DD.json
    containing a JSON array of reports.

    Args:
        report: Health check report from check_all().
        base_dir: Optional base directory. Defaults to data/status/history/.

    Returns:
        Path to the history file.
    """
    if base_dir is None:
        settings = get_settings()
        base_dir = settings.data_dir / "status" / "history"
    base_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
    path = base_dir / f"{today}.json"

    entries: list[dict[str, Any]] = []
    if path.exists():
        try:
            entries = json.loads(path.read_text())
        except (json.JSONDecodeError, ValueError):
            logger.warning(f"Corrupted history file {path}, starting fresh")
            entries = []

    entries.append(report)
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False))
    logger.info(f"History appended to {path}")
    return path


def format_telegram_report(report: dict[str, Any]) -> str:
    """Format a health check report for Telegram (HTML parse mode).

    Args:
        report: Health check report from check_all().

    Returns:
        HTML-formatted string suitable for Telegram.
    """
    lines = [
        "<b>API Health Report</b>",
        f"<code>{report['checked_at']}</code>",
        "",
        f"Total: {report['total']}",
        f"Healthy: {report['healthy']}",
        f"Degraded: {report['degraded']}",
        f"Down: {report['down']}",
    ]

    down_apis = [a for a in report["apis"] if a["status"] == "down"]
    if down_apis:
        lines.append("")
        lines.append("<b>DOWN:</b>")
        for api in down_apis:
            lines.append(f"  - <code>{api['id']}</code>: {api['message']}")

    degraded_apis = [a for a in report["apis"] if a["status"] == "degraded"]
    if degraded_apis:
        lines.append("")
        lines.append("<b>DEGRADED:</b>")
        for api in degraded_apis:
            lines.append(f"  - <code>{api['id']}</code>: {api['latency_ms']}ms")

    return "\n".join(lines)


def detect_changes(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Detect status changes between two reports.

    Args:
        current: Current health check report.
        previous: Previous health check report, or None if first run.

    Returns:
        List of dicts with keys: id, old_status, new_status.
    """
    if previous is None:
        return []

    prev_statuses = {api["id"]: api["status"] for api in previous.get("apis", [])}
    changes: list[dict[str, str]] = []

    for api in current.get("apis", []):
        old_status = prev_statuses.get(api["id"])
        if old_status is not None and old_status != api["status"]:
            changes.append({
                "id": api["id"],
                "old_status": old_status,
                "new_status": api["status"],
            })

    return changes


def format_change_notification(changes: list[dict[str, str]]) -> str:
    """Format status changes for Telegram notification.

    Args:
        changes: List of status change dicts from detect_changes().

    Returns:
        HTML-formatted string for Telegram.
    """
    lines = ["<b>API Status Changes Detected</b>", ""]
    for change in changes:
        emoji = "RED" if change["new_status"] == "down" else "GREEN"
        marker = f"[{emoji}]"
        lines.append(
            f"{marker} <code>{change['id']}</code>: "
            f"{change['old_status']} -> {change['new_status']}"
        )
    return "\n".join(lines)


def send_health_report(report: dict[str, Any]) -> bool:
    """Send the health report via Telegram.

    Args:
        report: Health check report from check_all().

    Returns:
        True if sent successfully.
    """
    message = format_telegram_report(report)
    return send_telegram(message, parse_mode="HTML")


def load_previous_status(path: Path | None = None) -> dict[str, Any] | None:
    """Load the previous status.json file.

    Args:
        path: Optional path to status.json.

    Returns:
        Previous report dict, or None if not found.
    """
    if path is None:
        settings = get_settings()
        path = settings.data_dir / "status" / "status.json"

    if not path.exists():
        return None

    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, ValueError):
        logger.warning(f"Corrupted status file {path}")
        return None
