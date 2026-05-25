"""
Central alert manager — routes alerts to Telegram, Email, and logs.

Provides deduplication (don't spam the same alert) and throttling
(max 1 alert per minute per type) to prevent alert fatigue.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from src.core.config import settings

logger = logging.getLogger("alert_manager")


class AlertManager:
    """
    Central alert dispatcher with deduplication and throttling.

    Usage:
        am = AlertManager()
        am.send("CRITICAL", "Circuit Breaker", "Daily loss limit exceeded", {...})
    """

    def __init__(
        self,
        throttle_seconds: int = 60,
        telegram_enabled: bool = True,
        email_enabled: bool = True,
    ):
        self.throttle_seconds = throttle_seconds
        self.telegram_enabled = telegram_enabled and settings.ALERT_TELEGRAM_ENABLED
        self.email_enabled = email_enabled and settings.ALERT_EMAIL_ENABLED

        self._last_alert_time: Dict[str, float] = {}  # key -> timestamp
        self._telegram_alerter: Optional[Any] = None
        self._email_alerter: Optional[Any] = None

        # Lazy-initialize alerters
        if self.telegram_enabled and settings.TELEGRAM_BOT_TOKEN:
            try:
                from src.monitoring.telegram_alerter import TelegramAlerter
                self._telegram_alerter = TelegramAlerter(
                    bot_token=settings.TELEGRAM_BOT_TOKEN,
                    chat_id=settings.TELEGRAM_CHAT_ID,
                )
                logger.info("Telegram alerter initialized")
            except Exception as e:
                logger.warning("Failed to initialize Telegram alerter: %s", e)
                self.telegram_enabled = False

        if self.email_enabled and settings.SMTP_HOST:
            try:
                from src.monitoring.email_alerter import EmailAlerter
                self._email_alerter = EmailAlerter(
                    smtp_host=settings.SMTP_HOST,
                    smtp_port=settings.SMTP_PORT,
                    smtp_user=settings.SMTP_USER,
                    smtp_password=settings.SMTP_PASSWORD,
                    to_address=settings.ALERT_EMAIL_TO,
                )
                logger.info("Email alerter initialized")
            except Exception as e:
                logger.warning("Failed to initialize Email alerter: %s", e)
                self.email_enabled = False

    def send(
        self,
        level: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        force: bool = False,
    ) -> bool:
        """
        Send an alert through all configured channels.

        Args:
            level: "CRITICAL", "WARNING", "INFO"
            title: Short alert title
            message: Detailed message
            data: Optional structured data
            force: Skip throttling/dedup

        Returns:
            True if alert was sent (not throttled)
        """
        # Deduplication key
        key = f"{level}:{title}"
        now = time.time()

        # Throttle check
        if not force:
            last_time = self._last_alert_time.get(key, 0)
            if now - last_time < self.throttle_seconds:
                logger.debug("Alert throttled: %s (last sent %.1fs ago)", key, now - last_time)
                return False

        self._last_alert_time[key] = now

        # Always log
        log_fn = {
            "CRITICAL": logger.critical,
            "WARNING": logger.warning,
            "INFO": logger.info,
        }.get(level, logger.info)
        log_fn("ALERT [%s] %s: %s", level, title, message)

        sent = False

        # Send to Telegram (critical + warning only)
        if self._telegram_alerter and level in ("CRITICAL", "WARNING"):
            try:
                self._telegram_alerter.send_alert(level, title, message, data)
                sent = True
            except Exception as e:
                logger.error("Telegram alert failed: %s", e)

        # Send to Email (all levels, but INFO only in daily digest)
        if self._email_alerter and level in ("CRITICAL", "WARNING"):
            try:
                self._email_alerter.send_alert(level, title, message, data)
                sent = True
            except Exception as e:
                logger.error("Email alert failed: %s", e)

        return sent

    def send_daily_report(self, report_data: Dict[str, Any]) -> None:
        """Send daily summary report via email."""
        if self._email_alerter:
            try:
                self._email_alerter.send_daily_report(report_data)
            except Exception as e:
                logger.error("Daily report email failed: %s", e)

    def clear_throttle(self, key: Optional[str] = None) -> None:
        """Clear throttle state (for testing or manual reset)."""
        if key:
            self._last_alert_time.pop(key, None)
        else:
            self._last_alert_time.clear()


# Singleton instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get or create the global AlertManager singleton."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
