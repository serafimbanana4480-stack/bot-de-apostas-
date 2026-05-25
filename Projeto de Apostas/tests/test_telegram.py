from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.telegram.bot import (
    get_db_status,
    send_signal_alert,
    start_command,
    status_command,
)


@pytest.mark.asyncio
@patch("src.telegram.bot.SessionLocal")
@patch("redis.Redis")
async def test_get_db_status(mock_redis_cls, mock_session_local):
    """Test connection status checkers for Postgres and Redis."""
    # Scenario 1: All healthy
    mock_db = MagicMock()
    mock_session_local.return_value = mock_db
    
    mock_redis = MagicMock()
    mock_redis_cls.return_value = mock_redis
    
    postgres_ok, redis_ok = await get_db_status()
    assert postgres_ok is True
    assert redis_ok is True

    # Scenario 2: Postgres offline, Redis online
    mock_db.execute.side_effect = Exception("DB Connection Lost")
    postgres_ok, redis_ok = await get_db_status()
    assert postgres_ok is False
    assert redis_ok is True


@pytest.mark.asyncio
@patch("src.telegram.bot.Bot")
@patch("src.telegram.bot.settings")
async def test_send_signal_alert(mock_settings, mock_bot_cls):
    """Test broadcasting value signals to Telegram channel configuration."""
    mock_settings.TELEGRAM_BOT_TOKEN = "12345:fake_token"
    mock_settings.TELEGRAM_CHAT_ID = "@my_betting_channel"
    
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    mock_bot_cls.return_value = mock_bot

    signal_data = {
        "game_id": "20261020-BOS-LAL",
        "bet_side": "HOME",
        "bookmaker_odds": 1.95,
        "predicted_prob": 0.585,
        "expected_edge": 0.14,
        "stake_size": 25.0,
        "approved": True
    }

    res = await send_signal_alert(signal_data)
    assert res is True
    mock_bot.send_message.assert_called_once()
    
    # Missing config returns False
    mock_settings.TELEGRAM_BOT_TOKEN = ""
    res = await send_signal_alert(signal_data)
    assert res is False


@pytest.mark.asyncio
async def test_commands_execution():
    """Test Telegram bot commands behavior with mock input updates."""
    # 1. Test /start command
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await start_command(update, context)
    update.message.reply_text.assert_called_once()
    assert "VBQ-UNIFIED Telegram Bot" in update.message.reply_text.call_args[0][0]

    # 2. Test /status command
    update.message.reply_text.reset_mock()
    with patch("src.telegram.bot.get_db_status", return_value=(True, True)):
        await status_command(update, context)
        # Reply text should be called twice (one for scanning status, one for result)
        assert update.message.reply_text.call_count == 2
        assert "Status de Saúde" in update.message.reply_text.call_args_list[1][0][0]
