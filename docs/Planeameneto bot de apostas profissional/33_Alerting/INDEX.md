# 33 Alerting

## Overview

Multi-channel alerting system for the VBQ-UNIFIED betting platform.

## Architecture

- **AlertManager**: Deduplication, routing, and delivery
- **AlertRules**: Predefined business logic triggers
- **Channels**: Telegram (all levels), email via SendGrid (WARNING+), JSON log file (all levels)

## Alert Levels

| Level    | Channels            | Deduplication |
|----------|---------------------|---------------|
| INFO     | Telegram, Log       | 15 min        |
| WARNING  | Telegram, Email, Log| 15 min        |
| CRITICAL | Telegram, Email, Log| 15 min        |

## Predefined Rules

1. **Circuit breaker triggered** -> CRITICAL
2. **Model accuracy < 55%** -> WARNING
3. **API error rate > 10%** -> WARNING
4. **Daily PnL negative** -> INFO
5. **No signals in 24h** -> WARNING

## API Endpoints

- `GET /alerts/status` - System status
- `GET /alerts/history` - Recent alert log
- `POST /alerts/test` - Send test alert

## Files

- `src/alerting/manager.py` - Core manager
- `src/alerting/rules.py` - Rule definitions
- `app/routers/alerts.py` - FastAPI routes
