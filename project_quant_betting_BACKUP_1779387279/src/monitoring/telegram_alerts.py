"""
Telegram Alerts Module.
Sends notifications for bets and system alerts using python-telegram-bot.
"""
import logging
from typing import Dict, Any, Optional
from telegram import Bot
from src.core.config import settings

logger = logging.getLogger(__name__)

class TelegramAlerts:
    """Manages Telegram notifications and commands."""
    
    def __init__(self, chat_id: Optional[str] = None):
        self.token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        self.chat_id = chat_id or getattr(settings, "TELEGRAM_CHAT_ID", None)
        self.bot = Bot(token=self.token) if self.token else None
        
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to the configured chat group."""
        if not self.bot or not self.chat_id:
            logger.warning("Telegram not configured. Skipping message.")
            return False
            
        try:
            await self.bot.send_message(
                chat_id=self.chat_id, 
                text=text, 
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
            
    async def notify_bet_placed(self, bet_info: Dict[str, Any]) -> bool:
        """Format and send a notification for a placed bet."""
        msg = (
            f"🎯 <b>NEW BET PLACED</b> 🎯\n\n"
            f"<b>Match:</b> {bet_info.get('match_name')}\n"
            f"<b>Selection:</b> {bet_info.get('selection')}\n"
            f"<b>Odds:</b> {bet_info.get('odds')}\n"
            f"<b>Stake:</b> {bet_info.get('stake_pct', 0)}% (EUR {bet_info.get('stake_amount', 0)})\n"
            f"<b>Edge:</b> {bet_info.get('edge_pct', 0)}%\n"
            f"<b>Probability:</b> {bet_info.get('probability', 0)*100:.1f}%\n"
            f"<b>Bookmaker:</b> {bet_info.get('bookmaker')}"
        )
        return await self.send_message(msg)
        
    async def notify_circuit_breaker(self, breaker_name: str, details: str) -> bool:
        """Send a high-priority alert for circuit breaker trips."""
        msg = (
            f"🚨 <b>CIRCUIT BREAKER TRIGGERED</b> 🚨\n\n"
            f"<b>Type:</b> {breaker_name}\n"
            f"<b>Details:</b> {details}\n\n"
            f"<i>Betting has been temporarily suspended.</i>"
        )
        return await self.send_message(msg)
