"""
Telegram alert bot — sends formatted alerts to a Telegram chat.

Supports commands: /status, /bankroll, /pause, /resume
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("telegram_alerter")

# Icons for alert levels
LEVEL_ICONS = {
    "CRITICAL": "\U0001F534",  # Red circle
    "WARNING": "\U0001F7E1",   # Yellow circle
    "INFO": "\U0001F535",      # Blue circle
}


class TelegramAlerter:
    """
    Sends alerts to Telegram via the Bot API.

    Also supports interactive commands for monitoring the bot remotely.
    """

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._bot = None

    def _get_bot(self):
        """Lazy-initialize the Telegram bot."""
        if self._bot is None:
            try:
                from telegram import Bot
                self._bot = Bot(token=self.bot_token)
            except ImportError:
                logger.warning("python-telegram-bot not installed — Telegram alerts disabled")
                return None
        return self._bot

    def send_alert(
        self,
        level: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send a formatted alert message to Telegram."""
        bot = self._get_bot()
        if not bot:
            return

        icon = LEVEL_ICONS.get(level, "\u2139")
        text = f"{icon} *[{level}] {title}*\n\n{message}"

        if data:
            # Add key data points
            data_lines = []
            for k, v in list(data.items())[:5]:  # Limit to 5 fields
                data_lines.append(f"  {k}: `{v}`")
            text += "\n\n" + "\n".join(data_lines)

        text += "\n\n_VBQ Alert System_"

        try:
            asyncio.get_event_loop().run_until_complete(
                bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                )
            )
        except RuntimeError:
            # No event loop — create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                )
            )
            loop.close()

    def send_status(self, status_data: Dict[str, Any]) -> None:
        """Send a status update message."""
        bot = self._get_bot()
        if not bot:
            return

        text = "\U0001F4CA *VBQ Status*\n\n"
        for k, v in status_data.items():
            text += f"  {k}: `{v}`\n"

        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                bot.send_message(chat_id=self.chat_id, text=text, parse_mode="Markdown")
            )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                bot.send_message(chat_id=self.chat_id, text=text, parse_mode="Markdown")
            )
            loop.close()
