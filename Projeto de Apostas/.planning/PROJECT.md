# VBQ-UNIFIED — Projeto de Apostas Quantitativo

## Overview

Sistema profissional de value betting (Futebol, UFC, NBA) com custo operacional minimo.

- **Repo canonico**: `Projeto de Apostas/`
- **Modo**: ZERO_COST_MODE=true (treino local, dados gratuitos)
- **Python**: 3.14.3 (migrar para 3.12 recomendado)
- **Testes**: 221 passed, 14 skipped
- **Edge validado em mock**: CLV medio 1.36% em mock; edge real ainda depende de `football_real_odds`

## Stack

| Camada | Opcao |
|--------|-------|
| Dados | mock + football_real_odds + football-data.org + nba_api |
| Storage | Parquet em `data/` |
| DB | Postgres (Docker) opcional |
| MLflow | `sqlite:///mlflow.db` (migrado de filesystem) |
| Orquestracao | `scripts/train_bot.py` + Cursor Automation |
| API | FastAPI + uvicorn |

## Comandos Diarios

```powershell
cd "Projeto de Apostas"
py scripts/ingest_free_data.py --sport football --source mock
py scripts/ingest_free_data.py --sport football --source football-data-co-uk
py scripts/train_bot.py football --source football_real_odds --walk-forward
py scripts/run_clv_report.py
py scripts/run_pipeline.py --sport football --mode live
py scripts/daily_report.py
```

## Estrutura

```
src/
  core/          — Config (Pydantic), interfaces, factory
  data/          — LocalDataStore (Parquet)
  ingestion/     — Dados gratuitos (mock, football_real_odds, football-data.org, nba_api)
  engine/        — Edge detection, normalizer, prediction
  ml/            — Modelos (Poisson, XGBoost, ensemble, RL)
  validation/    — LeakageDetector, WalkForward, CLVTracker
  risk/          — Bankroll, Kelly, limits
  execution/     — Paper trading, adapters (Betfair, Pinnacle, Polymarket)
  monitoring/    — Metrics, alerting
  api/           — FastAPI router
  telegram/      — Bot notifications
scripts/         — 35 scripts de pipeline, treino, backtest, auditoria
tests/           — 36 ficheiros de teste
```

## Decisoes Arquiteturais

1. **Parquet local** em vez de S3/BigQuery (zero custo)
2. **Walk-forward validation** obrigatorio (nunca random split em odds)
3. **LeakageDetector** bloqueia pipeline se features suspeitas
4. **Paper trading only** ate CLV > 1% validado
5. **MLflow SQLite** (migrado de filesystem devido a deprecacao Feb 2026)
6. **Mock não conta como prova final** — apenas `football_real_odds` valida CLV real
