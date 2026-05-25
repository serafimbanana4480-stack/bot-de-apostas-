# VBQ-UNIFIED Production Guide

Step-by-step guide for deploying VBQ-UNIFIED in production with real money.

## Table of Contents

1. [Pre-Flight Checklist](#pre-flight-checklist)
2. [Environment Setup](#environment-setup)
3. [Betfair SSL Certificates](#betfair-ssl-certificates)
4. [Paper Trading Week](#paper-trading-week)
5. [Going Live (Micro-Stakes)](#going-live)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Troubleshooting](#troubleshooting)
8. [Daily Operations](#daily-operations)

---

## Pre-Flight Checklist

Before risking real money, verify:

| # | Check | Command / Action |
|---|---|---|
| 1 | Python 3.11+ installed | `python --version` |
| 2 | All dependencies installed | `poetry install` |
| 3 | Tests pass | `poetry run pytest tests/ -q` |
| 4 | Ruff clean | `poetry run ruff check src scripts tests` |
| 5 | vbq doctor healthy | `poetry run python scripts/vbq_doctor.py` |
| 6 | CLV report shows edge | `poetry run python scripts/run_clv_report.py` |
| 7 | `.env` configured | See [Environment Setup](#environment-setup) |
| 8 | Backups working | `poetry run python scripts/backup.py --test` |
| 9 | Telegram bot configured (optional) | `TELEGRAM_BOT_TOKEN` set |
| 10 | Bankroll allocated | Set `INITIAL_BANKROLL` |

---

## Environment Setup

### 1. Create `.env` file

```bash
cp .env.example .env
```

### 2. Required variables

```bash
# === API KEYS (get from providers) ===
ODDS_API_KEY=your_odds_api_key_here
BETFAIR_APP_KEY=your_betfair_app_key
BETFAIR_CERT_PATH=/path/to/betfair.crt
BETFAIR_KEY_PATH=/path/to/betfair.key
PINNACLE_CLIENT_ID=your_pinnacle_id
PINNACLE_PASSWORD=your_pinnacle_password
FOOTBALL_DATA_ORG_TOKEN=your_fdo_token

# === DATABASE (optional — zero-cost mode works without) ===
DB_HOST=localhost
DB_PORT=5432
DB_NAME=valuebetting
DB_USER=vb_admin
DB_PASS=secure_password

# === TELEGRAM ALERTS (optional) ===
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# === BANKROLL ===
INITIAL_BANKROLL=1000.0
MAX_STAKE_PCT=0.10
KELLY_FRACTION=0.25

# === MODE ===
ZERO_COST_MODE=false
PAPER_TRADING=true
DRY_RUN=false
```

### 3. Verify configuration

```bash
poetry run python scripts/vbq_doctor.py --verbose
```

Expected output: `HEALTHY (8/9 passed)` (backups may show FAIL initially).

---

## Betfair SSL Certificates

Betfair Exchange requires SSL client certificates for API access.

### Generate certificates

```bash
# Generate private key
openssl genrsa -out betfair.key 2048

# Generate certificate signing request
openssl req -new -key betfair.key -out betfair.csr \
  -subj "/C=GB/ST=London/L=London/O=VBQ/CN=your-email@example.com"

# Generate self-signed certificate (for development)
openssl x509 -req -days 365 -in betfair.csr -signkey betfair.key -out betfair.crt
```

### Upload to Betfair

1. Log in to [Betfair Developer](https://developer.betfair.com)
2. Go to **My Apps** → **Certificates**
3. Upload `betfair.crt` (NOT the `.key` file!)
4. Wait for approval (usually instant for test, 24h for production)

### Update `.env`

```bash
BETFAIR_CERT_PATH=/home/user/.certs/betfair.crt
BETFAIR_KEY_PATH=/home/user/.certs/betfair.key
```

### Test connection

```bash
poetry run python -c "
from src.execution.adapters.betfair_real import BetfairRealConnector
c = BetfairRealConnector(
    app_key='your_app_key',
    cert_path='/home/user/.certs/betfair.crt',
    key_path='/home/user/.certs/betfair.key',
    sandbox=True,
)
print('SSL context:', c._build_ssl_context())
"
```

---

## Paper Trading Week

**Goal:** Run the system for 7 days with `PAPER_TRADING=true` to validate signals without risking money.

### Day 1: Setup

```bash
# Enable paper trading
export PAPER_TRADING=true

# Run daily pipeline
poetry run python scripts/run_daily.py --mode paper
```

### Daily commands

```bash
# Morning: Check health
poetry run python scripts/vbq_doctor.py

# During day: Monitor signals
poetry run python scripts/run_daily.py --mode paper --sport football

# Evening: Generate report
poetry run python scripts/run_clv_report.py
```

### Expected outcomes after 7 days

| Metric | Target | Action if below |
|---|---|---|
| CLV mean | > 1% | Review model features |
| Bets placed | > 20 | Check signal thresholds |
| Win rate | 45-55% | Normal for value betting |
| P&L (paper) | Any | Track vs. CLV |
| Drawdown | < 10% | Reduce Kelly fraction |

### Paper trading report

```bash
poetry run python scripts/generate_paper_report.py --days 7
```

Generates `reports/paper_trading_week_1.html` with:
- Daily P&L chart
- CLV vs. actual returns scatter
- Signal quality histogram
- Recommended Kelly adjustment

---

## Going Live

### Phase 1: Micro-stakes (Week 2)

```bash
# Switch to real money with tiny stakes
export PAPER_TRADING=false
export MIN_STAKE_EUR=0.01
export MAX_STAKE_EUR=0.50

# Run with extreme caution
poetry run python scripts/run_daily.py --mode live --max-bets 3
```

### Phase 2: Small stakes (Week 3-4)

If Week 2 shows positive CLV:

```bash
export MIN_STAKE_EUR=0.50
export MAX_STAKE_EUR=2.00
export MAX_DAILY_BETS=10
```

### Phase 3: Full deployment (Month 2+)

If CLV remains > 1% after 50+ bets:

```bash
# Full Kelly fraction
export KELLY_FRACTION=0.25
export MAX_STAKE_EUR=10.00
```

---

## Monitoring & Alerts

### Dashboard URLs (if Prometheus/Grafana configured)

| Dashboard | URL | What it shows |
|---|---|---|
| System health | `http://localhost:9090` | CPU, memory, API latency |
| P&L real-time | `http://localhost:3000` | Daily/weekly returns |
| Cost breakdown | `http://localhost:3000/d/costs` | API fees, commissions |
| Signal quality | `http://localhost:3000/d/signals` | CLV, calibration |

### Telegram alerts

Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` to receive:
- Bet placed confirmations
- Daily P&L summaries
- Circuit breaker triggers
- API connectivity failures

### Key metrics to watch

| Metric | Green | Yellow | Red |
|---|---|---|---|
| Daily CLV | > 1% | 0-1% | < 0% |
| Operational cost % | < 10% | 10-20% | > 20% |
| Drawdown | < 5% | 5-10% | > 10% |
| API success rate | > 95% | 90-95% | < 90% |
| Model calibration | < 0.05 Brier | 0.05-0.1 | > 0.1 |

---

## Troubleshooting

### "psycopg2 not installed"

```bash
poetry add psycopg2-binary
# Or: pip install psycopg2-binary
```

### "Betfair SSL certificate not found"

1. Verify paths in `.env`
2. Check file permissions: `chmod 600 betfair.key`
3. Ensure `.crt` was uploaded to Betfair developer portal

### "No historical data found"

```bash
# Run ingestion
poetry run python scripts/ingest_free_data.py --source mock --sport football

# Or download real data
poetry run python scripts/ingest_free_data.py --source football-data --sport football
```

### "CLV report shows 0% edge"

1. Check if model is trained: `ls models/`
2. Retrain: `poetry run python scripts/train_bot.py --sport football`
3. Verify data freshness: `poetry run python scripts/vbq_doctor.py`

### "Circuit breaker triggered"

```bash
# Check recent losses
poetry run python scripts/run_clv_report.py --show-trades

# Reset circuit breaker (manual override)
poetry run python -c "
from src.risk.circuit_breaker import CircuitBreaker
cb = CircuitBreaker(initial_bankroll=1000.0, max_drawdown_limit=0.10)
cb.reset()
print('Circuit breaker reset')
"
```

---

## Daily Operations

### Morning routine (10 min)

```bash
# 1. Health check
poetry run python scripts/vbq_doctor.py

# 2. Check overnight results
poetry run python scripts/run_clv_report.py

# 3. Review alerts
# (Check Telegram or logs/alerts.log)
```

### During trading hours

The system runs automatically via:
- **Cron** (Linux/Mac): `crontab -e` → add `*/15 * * * * cd /path && poetry run python scripts/run_daily.py`
- **Windows Task Scheduler**: Run `scripts/run_daily.py` every 15 minutes
- **Docker**: `docker-compose up -d` (see `docker-compose.yml`)

### Evening routine (5 min)

```bash
# 1. Daily backup
poetry run python scripts/backup.py

# 2. Generate daily report
poetry run python scripts/generate_paper_report.py --days 1

# 3. Review tomorrow's fixtures
poetry run python scripts/list_upcoming.py --sport football --days 2
```

### Weekly routine (30 min, every Sunday)

```bash
# 1. Weekly P&L review
poetry run python scripts/generate_paper_report.py --days 7

# 2. Model drift check
poetry run python scripts/check_drift.py --sport football

# 3. Retrain if needed
poetry run python scripts/train_bot.py --sport football --retrain-if-drift

# 4. Backup verification
poetry run python scripts/backup.py --verify-latest

# 5. Cost analysis
poetry run python scripts/analyze_costs.py --days 7
```

---

## Emergency Procedures

### If you suspect a bug is causing bad bets

1. **STOP immediately:** Set `CIRCUIT_BREAKER=true` in `.env`
2. **Check logs:** `tail -f logs/decisions.log`
3. **Run vbq doctor:** `poetry run python scripts/vbq_doctor.py`
4. **Review last 10 bets:** `poetry run python scripts/review_bets.py --last 10`
5. **Contact:** Open issue at `https://github.com/yourrepo/vbq-unified/issues`

### If API provider blocks you

1. Switch to fallback: Set `FALLBACK_PROVIDER=true`
2. Use cached data: `poetry run python scripts/ingest_free_data.py --source parquet`
3. Contact provider support with request logs

### If database is corrupted

```bash
# Restore from latest backup
poetry run python scripts/backup.py --restore-latest

# Verify data integrity
poetry run python scripts/vbq_doctor.py --check-schemas
```

---

## Checklist Summary

```
□ Environment configured (.env)
□ SSL certificates generated and uploaded
□ Paper trading completed (7 days)
□ CLV > 1% confirmed
□ Backups working
□ Telegram alerts configured
□ Prometheus/Grafana running (optional)
□ Micro-stakes tested (0.01 EUR)
□ Kelly fraction set appropriately
□ Circuit breaker configured
□ Daily cron job set up
□ Disaster recovery tested
```

---

*Last updated: 2026-05-21*
*For support: See `docs/TROUBLESHOOTING.md` or open a GitHub issue*
