"""Telegram notification utility."""

from __future__ import annotations

import requests

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


def send_telegram(message: str, parse_mode: str = "HTML") -> bool:
    """Send a message via Telegram bot.

    Args:
        message: Text to send.
        parse_mode: Telegram parse mode (HTML or Markdown).

    Returns:
        True if sent successfully, False otherwise.
    """
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning("Telegram credentials not configured, skipping notification")
        return False

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": message,
        "parse_mode": parse_mode,
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False
