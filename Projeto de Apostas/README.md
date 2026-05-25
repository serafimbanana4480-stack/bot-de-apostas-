# VBQ-UNIFIED — Bot de Apostas Quantitativo (0€)

Sistema profissional de value betting (Futebol, UFC, NBA) com **custo operacional mínimo**: treino local, dados gratuitos, MLflow SQLite, Parquet em disco.

## Quick start (0€ — sem APIs pagas)

```powershell
cd "Projeto de Apostas"
poetry install

# 1) Gerar / ingerir dados gratuitos
poetry run python scripts/ingest_free_data.py --sport football --source mock

# 2) Treinar modelo futebol (Poisson + calibração OOF)
poetry run python scripts/train_bot.py football --source mock --calibrate

# 2b) Treino / backtest com odds reais e fechamento Pinnacle
poetry run python scripts/ingest_free_data.py --sport football --source football-data-co-uk
poetry run python scripts/train_bot.py football --source football_real_odds --walk-forward

# 3) Walk-forward + métricas (Sortino, Calmar, profit factor)
poetry run python scripts/train_bot.py football --source mock --walk-forward

# 4) Relatório CLV (prova de edge vs closing line)
poetry run python scripts/run_clv_report.py

# 5) Regenerar dados mock com open vs closing (obrigatório 1x)
py -3 scripts/refresh_mock_data.py

# 6) Pipeline unificado (Tier B — sharp + dynamic EV)
py -3 scripts/run_pipeline.py --sport football --mode live
py -3 scripts/run_pipeline.py --sport football --mode backtest --start 2023-01-01 --end 2024-12-31 --check-leakage
py -3 scripts/backtest_season.py --sport football --start 2023-01-01 --end 2024-12-31 --compare-tier-b --check-leakage
py -3 scripts/settle_yesterday.py --sport football
py -3 scripts/daily_report.py

# 6) Pipeline legado
poetry run python scripts/run_football_pipeline.py
```

## Fontes de dados gratuitas

| Fonte | Custo | Uso |
|-------|-------|-----|
| `mock` (sintético) | 0€ | Smoke tests e treino offline imediato |
| `football_real_odds` | 0€ | Backtest/CLV com Pinnacle closing lines de football-data.co.uk |
| [football-data.org](https://www.football-data.org/client/register) | 0€ | Resultados ligas europeias sem odds |
| [nba_api](https://github.com/swar/nba_api) | 0€ | NBA (`scripts/ingest_nba_data.py`) |
| [The Odds API](https://the-odds-api.com/) | 0€ (500 req/dia) | Odds live (`ODDS_API_KEY`) |
| UFCStats scraper | 0€ | `src/ingestion/ufc_scraper.py` |

Definir token futebol gratuito:

```env
FOOTBALL_DATA_ORG_TOKEN=your_free_token
ZERO_COST_MODE=true
DATA_DIR=data
MLFLOW_TRACKING_URI=./mlruns
```

## Estrutura de dados local

```
data/
├── bronze/          # matches_*.parquet, odds_*.parquet
├── gold/            # features_*.parquet
├── reports/         # clv_report.json, last_football_train.json
└── mock_football.csv
```

## Stack mínima Docker (opcional)

9 serviços no `docker-compose.yml` completo. Para **menor custo de recursos**:

```powershell
docker compose -f docker-compose.minimal.yml up -d
```

Só Postgres + MLflow local — Redis/Prefect/Grafana opcionais.

## Treino NBA (gratuito)

Com Postgres a correr:

```powershell
poetry run python scripts/ingest_nba_data.py
poetry run python -c "from src.models.train import ModelTrainer; ..."
```

## Testes

```powershell
poetry run pytest tests/ -q
poetry run ruff check .
```

## Nota sobre edge

O valor de edge atualmente validado em `mock` e nos backtests sintéticos não deve ser tratado como prova final.
Para decisão profissional, use `football_real_odds` e valide CLV real antes de qualquer execução paga.

## Documentação

- [docs/ZERO_COST_STACK.md](docs/ZERO_COST_STACK.md) — stack 0€ completa
- [docs/CURSOR_AUTOMATION.md](docs/CURSOR_AUTOMATION.md) — automação diária no Cursor
- [docs/audit/AUDIT_REPORT.md](docs/audit/AUDIT_REPORT.md) — auditoria técnica
- Planeamento Obsidian: `../Planeameneto bot de apostas profissional/`

## Repositório canónico

Use **`Projeto de Apostas`** como base. `project_quant_betting/` é scaffold para fundir módulos (feature store, leakage detector).

## Cursor Agent

Ver [AGENTS.md](../AGENTS.md) na raiz do workspace para instruções ao agente AI.
