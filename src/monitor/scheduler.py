"""Health check scheduler — main entry point.

Usage:
    python -m src.monitor.scheduler
"""

from __future__ import annotations

from src.monitor.health_checker import check_all, create_all_connectors, generate_summary
from src.monitor.reporter import (
    detect_changes,
    format_change_notification,
    load_previous_status,
    save_history,
    save_status,
    send_health_report,
)
from src.utils.logging import get_logger
from src.utils.telegram import send_telegram

logger = get_logger(__name__)


def run_health_check() -> dict:
    """Run a full health check cycle.

    Steps:
        1. Load previous status (if any).
        2. Instantiate all connectors and check health.
        3. Save current status and history.
        4. If any statuses changed, send a Telegram notification.

    Returns:
        The current health check report.
    """
    logger.info("Starting health check cycle")

    # 1. Load previous status for change detection
    previous = load_previous_status()

    # 2. Run health checks
    connectors = create_all_connectors()
    report = check_all(connectors)

    summary = generate_summary(report)
    logger.info(f"Health check complete:\n{summary}")

    # 3. Persist results
    save_status(report)
    save_history(report)

    # 4. Notify on status changes only
    changes = detect_changes(report, previous)
    if changes:
        logger.info(f"Detected {len(changes)} status change(s), sending notification")
        message = format_change_notification(changes)
        send_telegram(message, parse_mode="HTML")
    else:
        logger.info("No status changes detected, skipping notification")

    return report


def main() -> None:
    """CLI entry point."""
    report = run_health_check()
    print(f"Checked {report['total']} APIs: "
          f"{report['healthy']} healthy, "
          f"{report['degraded']} degraded, "
          f"{report['down']} down")


if __name__ == "__main__":
    main()
