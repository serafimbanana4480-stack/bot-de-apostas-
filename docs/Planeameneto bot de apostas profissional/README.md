# VBQ-UNIFIED — Sistema Quantitativo de Value Betting NBA

Sistema completo de apostas desportivas quantitativas focado em NBA, com ML, gestao de risco, pipeline automatizado e distribuicao de sinais via Telegram.

---

## Links do Sistema

- [[00_Master_Index/INDEX]] — Cerebro operacional e mapa completo
- [[GAP_NOTES]] — Lacunas e melhorias pendentes
- [[00_Master_Index/GETTING_STARTED]] — Guia de inicio rapido para novos devs
- [[00_Master_Index/ONBOARDING_GUIDE]] — Onboarding da equipa

---

## Stack Tecnologico

| Camada | Tecnologia |
|--------|-----------|
| API | FastAPI + Uvicorn |
| Auth | JWT (python-jose) + bcrypt |
| Banco de Dados | PostgreSQL 15 + SQLAlchemy |
| Cache | Redis 7 |
| ML | XGBoost, LightGBM, CatBoost, scikit-learn |
| Experiment Tracking | MLflow |
| Orquestracao | Prefect 2.x |
| Monitorizacao | Prometheus + Grafana |
| Distribuicao de Sinais | Telegram Bot (python-telegram-bot v20+) |
| Odds | Betfair API + Odds API (fallback) |
| Alertas | Telegram + SendGrid Email |

## Estrutura do Projeto

```
app/                  # FastAPI application
  routers/            # API endpoints (auth, predictions, signals, telegram, alerts)
src/                  # Core source code
  api/                # Internal API route stubs
  auth/               # JWT authentication (models, security, dependencies)
  cache/              # Redis client with health checks
  database/           # SQLAlchemy models and connection
  engine/             # Edge calculator, pipeline orchestrator
  features/           # Feature engineering (form, context, market, lookahead)
  ingestion/          # Data ingestion (NBA API, Betfair, Odds API)
  middleware/         # Rate limiting (slowapi + Redis)
  models/             # ML models (ensemble, meta-model)
  pipeline/           # Prefect daily flow and scheduler
  risk/               # Kelly criterion, circuit breakers
  alerting/           # Alert manager with deduplication
  telegram/           # Bot, handlers, subscriptions
  mlflow_client.py    # MLflow experiment tracking wrapper
alembic/              # SQL schema migrations
monitoring/           # Prometheus and Grafana configs
tests/                # Unit, integration and E2E tests
```

## Modulos de Codigo

- [[app/INDEX]] — FastAPI routers e endpoints
- [[src/INDEX]] — Core source code completo
- [[src/auth/INDEX]] — Sistema de autenticacao JWT
- [[src/features/INDEX]] — Feature engineering
- [[src/pipeline/INDEX]] — Pipeline Prefect diario

## Quick Start

```bash
# 1. Copiar e preencher .env
cp .env.example .env
# Editar .env com as tuas credenciais

# 2. Subir infraestrutura
docker-compose up -d postgres redis mlflow grafana prometheus prefect-api

# 3. Subir API
docker-compose up -d api

# 4. Testar
open http://localhost:8000/docs
```

## Estado do Projeto

| Componente | Estado |
|------------|--------|
| Documentacao geral | 95% |
| Backend core NBA | 82% |
| Auth JWT | 90% |
| Telegram Bot | 80% |
| Pipeline E2E | 78% |
| Alertas | 80% |
| Dashboard/Frontend | 0% |
| Player Props NBA | 0% |
| Multi-Desporto | 0% |

Ver [[GAP_NOTES]] para lacunas detalhadas.

## Documentacao Principal

- [[01_Vision_And_Strategy/INDEX]] — Visao e estrategia
- [[02_Business_Model/INDEX]] — Modelo de negocio e SaaS
- [[04_Data_Engineering/INDEX]] — Pipelines ETL e ingestao
- [[05_Machine_Learning/INDEX]] — Modelos ML e calibracao
- [[06_Backtesting/INDEX]] — Backtesting e validacao
- [[07_Value_Detection/INDEX]] — Motor de edge
- [[08_Risk_Management/INDEX]] — Kelly, drawdown, circuit breakers
- [[09_Execution_System/INDEX]] — Execucao manual e automatica
- [[10_Infrastructure/INDEX]] — VPS, Docker, networking
- [[19_Telegram_System/INDEX]] — Bot e distribuicao de sinais
- [[20_Dashboarding/INDEX]] — Dashboards e web app
- [[24_Product_Roadmap/INDEX]] — Roadmap 24 meses
- [[33_Alerting/INDEX]] — Sistema de alertas
- [[34_Security/INDEX]] — Arquitetura de seguranca
- [[42_Player_Props/INDEX]] — Player Props NBA
- [[43_Multi_Sport_Expansion/INDEX]] — Multi-desporto

## Licenca

Uso privado. Nao distribuir sem autorizacao.
