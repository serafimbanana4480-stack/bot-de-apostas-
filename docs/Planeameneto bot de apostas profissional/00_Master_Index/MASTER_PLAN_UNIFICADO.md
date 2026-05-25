# MASTER PLAN UNIFICADO — Fundo Quantitativo de Apostas Desportivas

**ID do Sistema:** `VBQ-UNIFIED`
**Versão:** `4.0.2-AUDIT-COMPLETE`
**Data:** `2026-05-17`
**Autor:** Chief Systems Architect + Principal Quant Engineer
**Estado:** `PLANO DE EXECUÇÃO — PRONTO PARA IMPLEMENTAR (AUDITORIA SISTÉMICA COMPLETA)`

---

## RESUMO EXECUTIVO

Este documento é o **plano-mestre definitivo** que unifica e substitui todos os planos anteriores (VBQ-001 Conservative, VBQ-002 Aggressive, VBQ-003 Institutional). Contém a arquitetura completa, o roadmap faseado com milestones verificáveis, as especificações técnicas de cada módulo, e as regras de gestão de risco que garantem a sobrevivência do capital.

**Objetivo:** Construir um sistema quantitativo de value betting que gera retorno composto sobre o capital através de vantagem matemática comprovada, com execução disciplinada e monetização diversificada.

**Filosofia:** Rigor estatístico desde o dia 1. Complexidade só quando o edge a justifica. Validação progressiva com dinheiro real. Escala financiada pelos próprios lucros.

**Auditoria Sistémica (2026-05-17):** Concluída auditoria completa com resolução de 8 inconsistências críticas (C-001 a C-012). Decisões formalizadas em RESOLUCAO_INCONSISTENCIAS_CRITICAS.md. Criados 11 documentos críticos adicionais para garantir consistência técnica e operacional.

---

## ÍNDICE

1. [Arquitetura Global do Sistema](#1-arquitetura-global-do-sistema)
2. [Stack Tecnológica](#2-stack-tecnológica)
3. [Estrutura de Código e Ficheiros](#3-estrutura-de-código-e-ficheiros)
4. [Base de Dados — Schema SQL Completo](#4-base-de-dados--schema-sql-completo)
5. [Pipeline de Dados](#5-pipeline-de-dados)
6. [Feature Engineering](#6-feature-engineering)
7. [Modelação — Ensemble Stacking + Meta-Labeling](#7-modelação--ensemble-stacking--meta-labeling)
8. [Validação e Backtest](#8-validação-e-backtest)
9. [Motor de Edge e Geração de Sinais](#9-motor-de-edge-e-geração-de-sinais)
10. [Gestão de Risco e Sizing](#10-gestão-de-risco-e-sizing)

> **Nota:** Secções 11–20 (Execução, Operação, Monitorização, MLOps, Modelo de Negócio, Roadmap, Circuit Breakers, Contingência, Compliance, Glossário) estão documentadas como blocos de texto dentro da Secção 10 ou em notas dedicadas da vault (ex: `09_Execution_System`, `11_MLOps`, `02_Business_Model`). Não existem como headers independentes neste documento.

---

## 1. ARQUITETURA GLOBAL DO SISTEMA

### 1.1 Diagrama de Módulos

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SISTEMA VBQ-UNIFIED                           │
├───────────────┬───────────────┬───────────────┬───────────────────────┤
│  INGESTÃO     │  FEATURES     │  MODELOS      │  DECISÃO              │
│  (batch 2h)   │  (pré-jogo)   │  (ensemble)   │  (edge + meta)        │
├───────────────┴───────────────┴───────────────┴───────────────────────┤
│                          POSTGRESQL + REDIS                          │
├───────────────┬───────────────┬───────────────┬───────────────────────┤
│  EXECUÇÃO     │  DISTRIBUIÇÃO │  MONITORIZAÇÃO│  NEGÓCIO              │
│  (Betfair)    │  (Telegram)   │  (Grafana)    │  (Tipster)            │
└───────────────┴───────────────┴───────────────┴───────────────────────┘
```

### 1.2 Fluxo de Dados (End-to-End)

```
[Fontes Externas]                [Sistema VBQ]                    [Output]
                                                                 
NBA API ─────┐              ┌─ PostgreSQL (raw_)                 
Betfair API ─┤              │                                    
BasketballRef ├──► INGESTÃO ─┤─ PostgreSQL (clean_)              
ESPN RSS ────┤   (Python)   │                                    
Twitter ─────┘              │─ Redis (odds_cache)                
                             │                                    
                    ┌────────┘                                    
                    ▼                                            
              FEATURE ENGINEERING
              (80 features)                                   
              ├─ feat_team_form                                   
              ├─ feat_market_metrics                              
              ├─ feat_game_context                                
              └─ feat_interactions                                
                    │                                            
                    ▼                                            
              MODELO PRIMÁRIO                                     
              (XGBoost + LightGBM + CatBoost)                     
              → Probabilidade calibrada                           
                    │                                            
                    ▼                                            
              CÁLCULO DE EDGE                                     
              edge = P_cal * odd - 1                              
                    │                                            
                    ▼                                            
              META-MODELO (filtro)                                
              P(CLV > 0 | edge, features)                         
                    │                                            
                    ▼                                            
              MOTOR DE DECISÃO                                    
              ├─ Edge > 4%?                                       
              ├─ P_meta > 0.6?                                    
              └─ Circuit breakers OK?                             
                    │                                            
                    ▼                                            
              SINAL APROVADO                                      
              ├─ Telegram Bot ──► Subscritor                      
              ├─ Email ──► Subscritor                             
              └─ Betfair API ──► Aposta automática (Fase 3+)     
```

---

## 2. STACK TECNOLÓGICA

| Camada | Tecnologia | Versão | Justificação |
|--------|-----------|--------|-------------|
| **Linguagem** | Python | 3.11+ | Ecossistema ML completo, async, tipos |
| **Base Dados** | PostgreSQL | 15-alpine | ACID, window functions, particionamento |
| **Cache** | Redis | 7.2 | Odds em memória, filas, circuit breakers |
| **ML - Modelo 1** | XGBoost | 2.0+ | Melhor para dados tabulares |
| **ML - Modelo 2** | LightGBM | 4.3+ | Mais rápido, melhor com muitas features |
| **ML - Modelo 3** | CatBoost | 1.2+ | Lida bem com categóricas, menos tuning |
| **ML - Stacking** | scikit-learn | 1.4.0 | LogisticRegression como meta-modelo |
| **ML - Tuning** | Optuna | 3.6+ | Bayesian optimization |
| **ML - Tracking** | MLflow | 2.12+ | Experimentos, registry, deploy |
| **Calibração** | scikit-learn | 1.4.0 | IsotonicRegression por regime |
| **Backend** | FastAPI | 0.109.0 | Async, OpenAPI, validação Pydantic |
| **Orquestração** | Prefect | 2.16.3 | Workflows, retries, scheduling |
| **Telegram** | python-telegram-bot | 20.7 | Bot de sinais e comandos |
| **Email** | SendGrid API | v3 | Emails transacionais |
| **Monitorização** | Prometheus + Grafana | latest | Métricas, dashboards, alertas |
| **Infraestrutura** | Docker + Compose | latest | Containers, isolamento, CI/CD |
| **Deploy** | 1 VPS Linux | 4 vCPU, 8 GB | Batch síncrono, sem necessidade de cluster |
| **Segurança** | python-dotenv | 1.0+ | Variáveis de ambiente, zero hardcoded secrets |

**Custo mensal estimado:**
- VPS (Hetzner CPX31 — 4 vCPU, 8 GB RAM, 160 GB SSD): ~12€/mês
- APIs de dados premium (fase 5+): 0-100€
- The Odds API Standard (validação cruzada fecho, meses 4-6): 8€/mês
- Domínio + email: 2€
- **Total:** ~15-123€/mês (cresce com a escala)

---

## 3. ESTRUTURA DE CÓDIGO E FICHEIROS

```
vbq-system/
│
├── docker-compose.yml              # Serviços: app, postgres, redis, grafana, mlflow
├── Dockerfile                      # Imagem Python com dependências
├── requirements.txt                # Dependências Python
├── .env.example                    # Template de variáveis de ambiente
├── Makefile                        # Comandos: ingest, train, backtest, deploy
│
├── config/
│   ├── settings.py                 # Configuração central (DB, APIs, thresholds)
│   ├── thresholds.py               # edge_min, prob_meta_min, kelly_K, etc.
│   └── logging.yaml                # Configuração de logging
│
├── src/
│   ├── __init__.py
│   │
│   ├── ingestion/                  # Módulo 1: Ingestão de Dados
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseIngestor (abstract)
│   │   ├── nba_api.py              # NBA API → raw_nba_games
│   │   ├── nba_stats.py            # Basketball-Reference → raw_nba_stats
│   │   ├── betfair_odds.py         # Betfair API → raw_odds_betfair
│   │   ├── betfair_sp.py           # Betfair SP (fecho) → raw_odds_betfair_sp
│   │   ├── the_odds_api.py         # The Odds API (fecho) → raw_odds_the_odds_api
│   │   ├── injuries.py             # ESPN RSS + Twitter → raw_injuries
│   │   ├── schedule.py             # nba_api schedule → raw_schedules
│   │   └── orchestrator.py         # Pipeline completo, hora a hora
│   │
│   ├── cleaning/                   # Módulo 2: Limpeza (Bronze → Silver)
│   │   ├── __init__.py
│   │   ├── dedup.py                # Deduplicação de registos
│   │   ├── normalize.py            # Normalização de nomes, IDs
│   │   ├── validate.py             # Validação de ranges, tipos
│   │   └── orchestrator.py         # Pipeline de limpeza
│   │
│   ├── features/                   # Módulo 3: Feature Engineering (Silver → Gold)
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseFeatureBuilder
│   │   ├── form.py                 # Módulo A: forma recente (15 features)
│   │   ├── market.py               # Módulo B: métricas de mercado (12 features)
│   │   ├── context.py              # Módulo C: contexto de jogo (18 features)
│   │   ├── players.py              # Módulo D: On/Off jogadores (20 features)
│   │   ├── interactions.py         # Módulo E: interações não-lineares (15 features)
│   │   ├── lookahead.py            # Proteção contra look-ahead
│   │   └── orchestrator.py         # Pipeline de features
│   │
│   ├── models/                     # Módulo 4: Modelos ML
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseModel (train, predict, save, load)
│   │   ├── xgboost_model.py        # XGBoost wrapper
│   │   ├── lightgbm_model.py       # LightGBM wrapper
│   │   ├── catboost_model.py       # CatBoost wrapper
│   │   ├── ensemble.py             # Stacking ensemble (out-of-fold)
│   │   ├── meta_model.py           # Meta-labeling model
│   │   ├── calibration.py          # IsotonicRegression por regime
│   │   ├── online_learning.py      # EWA / Kalman para ratings online
│   │   └── registry.py             # MLflow model registry
│   │
│   ├── backtest/                   # Módulo 5: Backtesting
│   │   ├── __init__.py
│   │   ├── walk_forward.py         # Purged walk-forward CV
│   │   ├── embargo.py              # Cálculo de embargo periods
│   │   ├── metrics.py              # CLV, ROI, Sharpe, Brier, ECE
│   │   ├── monte_carlo.py          # Simulações de Monte Carlo
│   │   └── reports.py              # Relatórios de backtest
│   │
│   ├── engine/                     # Módulo 6: Motor de Decisão
│   │   ├── __init__.py
│   │   ├── edge.py                 # Cálculo de edge
│   │   ├── filters.py              # Filtros (edge, prob, liquidez, meta)
│   │   ├── signal.py               # Signal dataclass
│   │   └── orchestrator.py         # Motor completo, batch a cada 2h
│   │
│   ├── risk/                       # Módulo 7: Gestão de Risco
│   │   ├── __init__.py
│   │   ├── kelly.py                # Kelly fracionado + limites
│   │   ├── drawdown.py             # Monitorização de drawdown
│   │   ├── circuit_breakers.py     # Alpha, Beta, Gamma, Delta, Epsilon
│   │   ├── exposure.py             # Limites por aposta/jogo/dia
│   │   └── health.py               # AccountHealthTracker (multi-casa)
│   │
│   ├── execution/                  # Módulo 8: Execução de Apostas
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseExecutor (abstract)
│   │   ├── manual.py               # Fase 1: sinais Telegram, confirmação manual
│   │   ├── one_click.py            # Fase 2: deep links Betfair
│   │   ├── algorithmic.py          # Fase 3: Betfair API, limit orders
│   │   ├── reconciliation.py       # Reconciliação sinal vs execução
│   │   └── slippage.py             # Tracking de slippage real
│   │
│   ├── distribution/               # Módulo 9: Distribuição de Sinais
│   │   ├── __init__.py
│   │   ├── telegram_bot.py         # Bot Telegram (envio, comandos, subscrições)
│   │   ├── email_sender.py         # SendGrid emails transacionais
│   │   └── webhook.py              # Webhook para integrações externas
│   │
│   ├── monitoring/                 # Módulo 10: Monitorização
│   │   ├── __init__.py
│   │   ├── metrics.py              # Métricas Prometheus
│   │   ├── dashboards.py           # Configuração Grafana (JSON)
│   │   ├── alerts.py               # Regras de alerta (Telegram, email)
│   │   └── health_checks.py        # Health checks de todos os componentes
│   │
│   ├── business/                   # Módulo 11: Modelo de Negócio
│   │   ├── __init__.py
│   │   ├── subscriptions.py        # Gestão de subscritores
│   │   ├── payments.py             # Integração Stripe/Paddle
│   │   ├── analytics.py            # Métricas de negócio (CAC, LTV, churn)
│   │   └── tracking.py             # PnL tracking público
│   │
│   └── api/                        # Módulo 12: API FastAPI
│       ├── __init__.py
│       ├── main.py                 # FastAPI app
│       ├── routes/
│       │   ├── signals.py          # GET /signals, POST /signals/confirm
│       │   ├── predictions.py      # POST /predict
│       │   ├── health.py           # GET /health
│       │   ├── metrics.py          # GET /metrics (Prometheus)
│       │   └── admin.py            # Admin endpoints (protegidos)
│       └── middleware/
│           ├── auth.py             # Autenticação (API keys)
│           └── rate_limit.py       # Rate limiting
│
├── sql/
│   ├── 001_schema_raw.sql          # Tabelas Bronze (raw_*)
│   ├── 002_schema_clean.sql        # Tabelas Silver (clean_*)
│   ├── 003_schema_features.sql     # Tabelas Gold (feat_*)
│   ├── 004_schema_meta.sql         # Tabelas Meta/Audit
│   ├── 005_indexes.sql             # Índices para performance
│   └── 006_seed_data.sql           # Dados iniciais (equipas, épocas)
│
├── tests/
│   ├── test_ingestion.py
│   ├── test_features.py
│   ├── test_models.py
│   ├── test_backtest.py
│   ├── test_engine.py
│   ├── test_risk.py
│   └── test_execution.py
│
├── notebooks/                      # Jupyter notebooks (exploração)
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_analysis.ipynb
│   ├── 03_model_baseline.ipynb
│   └── 04_backtest_analysis.ipynb
│
├── scripts/                        # Scripts utilitários
│   ├── setup_db.sh                 # Criar base de dados e schema
│   ├── backfill_data.sh            # Backfill de dados históricos
│   └── deploy.sh                   # Deploy para produção
│
├── grafana/
│   └── dashboards/                 # Dashboards Grafana (JSON)
│       ├── business_overview.json
│       ├── risk_monitoring.json
│       ├── model_performance.json
│       └── system_health.json
│
└── docs/                           # Documentação (este ficheiro + Obsidian)
```

---

## 4. BASE DE DADOS — SCHEMA SQL COMPLETO

### 4.1 Camada Bronze (Raw)

```sql
-- ============================================================
-- BRONZE: Dados brutos, nunca modificados, append-only
-- ============================================================

CREATE SCHEMA IF NOT EXISTS bronze;

-- Jogos NBA (fonte: nba_api)
CREATE TABLE bronze.raw_nba_games (
    id              BIGSERIAL PRIMARY KEY,
    game_id         VARCHAR(20) NOT NULL,       -- ID natural: "0022300001"
    season          VARCHAR(9) NOT NULL,        -- "2023-24"
    game_date       DATE NOT NULL,
    home_team_id    INTEGER NOT NULL,
    away_team_id    INTEGER NOT NULL,
    home_score      INTEGER,
    away_score      INTEGER,
    status          VARCHAR(20) NOT NULL,       -- Scheduled, Live, Final
    raw_json        JSONB NOT NULL,             -- Dados originais completos
    ingested_at     TIMESTAMPTZ DEFAULT NOW(),
    source          VARCHAR(50) DEFAULT 'nba_api'
);

CREATE INDEX idx_raw_games_game_id ON bronze.raw_nba_games(game_id);
CREATE INDEX idx_raw_games_date ON bronze.raw_nba_games(game_date);
CREATE INDEX idx_raw_games_season ON bronze.raw_nba_games(season);

-- Odds Betfair (fonte: Betfair Exchange API)
CREATE TABLE bronze.raw_odds_betfair (
    id              BIGSERIAL PRIMARY KEY,
    game_id         VARCHAR(20) NOT NULL,
    market_type     VARCHAR(30) NOT NULL,       -- "MONEYLINE", "SPREAD"
    selection       VARCHAR(50) NOT NULL,       -- "Boston Celtics"
    odd             NUMERIC(8,3) NOT NULL,
    volume_matched  NUMERIC(12,2),              -- Volume transacionado em EUR
    timestamp       TIMESTAMPTZ NOT NULL,        -- Quando a odd foi capturada
    ingested_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_raw_odds_betfair_game ON bronze.raw_odds_betfair(game_id, market_type, timestamp);

-- Odds Betfair SP (Starting Price - proxy de closing line, gratuito via Betfair Exchange API)
CREATE TABLE bronze.raw_odds_betfair_sp (
    id              BIGSERIAL PRIMARY KEY,
    game_id         VARCHAR(20) NOT NULL,
    market_type     VARCHAR(30) NOT NULL,
    selection_id    VARCHAR(50) NOT NULL,
    selection_name  VARCHAR(100) NOT NULL,
    sp_odd          NUMERIC(8,3),               -- Starting Price
    timestamp       TIMESTAMPTZ NOT NULL,
    ingested_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Odds The Odds API (fecho, validação cruzada, plano Standard $9/mês)
CREATE TABLE bronze.raw_odds_the_odds_api (
    id              BIGSERIAL PRIMARY KEY,
    game_id         VARCHAR(20) NOT NULL,
    market_type     VARCHAR(30) NOT NULL,
    bookmaker       VARCHAR(50) NOT NULL,       -- "pinnacle", "betmgm", etc.
    home_odd        NUMERIC(8,3),
    away_odd        NUMERIC(8,3),
    draw_odd        NUMERIC(8,3),                -- NULL para NBA
    last_update     TIMESTAMPTZ NOT NULL,
    ingested_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Estatísticas (fonte: Basketball-Reference)
CREATE TABLE bronze.raw_nba_stats (
    id              BIGSERIAL PRIMARY KEY,
    game_id         VARCHAR(20) NOT NULL,
    team_id         INTEGER NOT NULL,
    stat_type       VARCHAR(30) NOT NULL,       -- "EFG_PCT", "TOV_PCT", etc.
    stat_value      NUMERIC(12,4) NOT NULL,
    ingested_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Lesões (fonte: ESPN RSS + Twitter)
CREATE TABLE bronze.raw_injuries (
    id              BIGSERIAL PRIMARY KEY,
    player_id       INTEGER NOT NULL,
    player_name     VARCHAR(100) NOT NULL,
    team_id         INTEGER NOT NULL,
    injury_status   VARCHAR(30) NOT NULL,       -- "OUT", "QUESTIONABLE", "PROBABLE"
    description     TEXT,
    reported_at     TIMESTAMPTZ NOT NULL,
    source          VARCHAR(50),                -- "ESPN", "Twitter"
    ingested_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Schedule / calendário
CREATE TABLE bronze.raw_schedules (
    id              BIGSERIAL PRIMARY KEY,
    team_id         INTEGER NOT NULL,
    game_date       DATE NOT NULL,
    game_id         VARCHAR(20),
    is_home         BOOLEAN,
    rest_days       INTEGER,
    travel_distance NUMERIC(8,1),               -- km desde último jogo
    ingested_at     TIMESTAMPTZ DEFAULT NOW()
);
```

### 4.2 Camada Silver (Clean)

```sql
-- ============================================================
-- SILVER: Dados limpos, deduplicados, validados
-- ============================================================

CREATE SCHEMA IF NOT EXISTS silver;

-- Jogos limpos (entidade única por game_id)
CREATE TABLE silver.clean_games (
    game_id         VARCHAR(20) PRIMARY KEY,
    season          VARCHAR(9) NOT NULL,
    game_date       DATE NOT NULL,
    home_team_id    INTEGER NOT NULL,
    away_team_id    INTEGER NOT NULL,
    home_score      INTEGER,
    away_score      INTEGER,
    status          VARCHAR(20) NOT NULL,
    processed_at    TIMESTAMPTZ DEFAULT NOW(),
    data_version    INTEGER DEFAULT 1
);

CREATE INDEX idx_clean_games_date ON silver.clean_games(game_date);

-- Equipas normalizadas
CREATE TABLE silver.clean_teams (
    team_id         INTEGER PRIMARY KEY,
    team_name       VARCHAR(100) NOT NULL,
    team_abbr       VARCHAR(5) NOT NULL,        -- "BOS", "LAL"
    conference      VARCHAR(10),                -- "East", "West"
    division        VARCHAR(20),
    city            VARCHAR(50),
    latitude        NUMERIC(9,6),
    longitude       NUMERIC(9,6)
);

-- Odds agregadas (melhor odd por jogo/mercado/seleção)
CREATE TABLE silver.clean_odds (
    id              BIGSERIAL PRIMARY KEY,
    game_id         VARCHAR(20) NOT NULL REFERENCES silver.clean_games(game_id),
    market_type     VARCHAR(30) NOT NULL,
    selection_id    INTEGER NOT NULL,
    selection_name  VARCHAR(50) NOT NULL,
    odd_betfair     NUMERIC(8,3),
    odd_betfair_sp  NUMERIC(8,3),              -- Betfair Starting Price (proxy closing)
    odd_the_odds_api NUMERIC(8,3),             -- The Odds API closing (validação cruzada)
    volume_matched  NUMERIC(12,2),
    captured_at     TIMESTAMPTZ NOT NULL,
    UNIQUE(game_id, market_type, selection_id, captured_at)
);

-- Lesões ativas por jogo
CREATE TABLE silver.clean_injuries_active (
    id              BIGSERIAL PRIMARY KEY,
    game_id         VARCHAR(20) NOT NULL REFERENCES silver.clean_games(game_id),
    player_id       INTEGER NOT NULL,
    player_name     VARCHAR(100) NOT NULL,
    team_id         INTEGER NOT NULL,
    injury_status   VARCHAR(30) NOT NULL,
    is_key_player   BOOLEAN DEFAULT FALSE,      -- Top 5 da equipa?
    processed_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Histórico de calendário por equipa
CREATE TABLE silver.clean_schedule_history (
    id              BIGSERIAL PRIMARY KEY,
    team_id         INTEGER NOT NULL,
    game_date       DATE NOT NULL,
    game_id         VARCHAR(20),
    rest_days       INTEGER NOT NULL DEFAULT 0,
    b2b_flag        BOOLEAN DEFAULT FALSE,       -- Back-to-back
    travel_distance NUMERIC(8,1) DEFAULT 0,
    games_last_5d   INTEGER DEFAULT 0,
    games_last_7d   INTEGER DEFAULT 0,
    games_last_10d  INTEGER DEFAULT 0,
    UNIQUE(team_id, game_date)
);
```

### 4.3 Camada Gold (Features)

```sql
-- ============================================================
-- GOLD: Features de ML pré-calculadas, otimizadas para query
-- ============================================================

CREATE SCHEMA IF NOT EXISTS gold;

-- Módulo A: Forma Recente (15 features)
CREATE TABLE gold.feat_team_form (
    id              BIGSERIAL PRIMARY KEY,
    team_id         INTEGER NOT NULL,
    game_date       DATE NOT NULL,
    -- Win rate ponderado (half-life 5 jogos)
    win_rate_weighted           NUMERIC(8,4),
    -- Four Factors com decaimento exponencial
    efg_pct_weighted            NUMERIC(8,4),
    tov_pct_weighted            NUMERIC(8,4),
    orb_pct_weighted            NUMERIC(8,4),
    ft_fga_weighted             NUMERIC(8,4),
    -- Net Rating
    net_rating_weighted         NUMERIC(8,4),
    off_rating_weighted         NUMERIC(8,4),
    def_rating_weighted         NUMERIC(8,4),
    -- Momentum (diferença últimos 3 jogos vs época)
    off_rating_momentum_3g      NUMERIC(8,4),
    def_rating_momentum_3g      NUMERIC(8,4),
    -- Forma bruta
    wins_last_5                 INTEGER,
    wins_last_10                INTEGER,
    avg_margin_last_5           NUMERIC(8,2),
    avg_margin_last_10          NUMERIC(8,2),
    -- Metadados
    calculated_at               TIMESTAMPTZ DEFAULT NOW(),
    data_version                INTEGER DEFAULT 1,
    UNIQUE(team_id, game_date, data_version)
);

-- Módulo B: Métricas de Mercado (12 features)
CREATE TABLE gold.feat_market_metrics (
    id              BIGSERIAL PRIMARY KEY,
    game_id         VARCHAR(20) NOT NULL,
    captured_at     TIMESTAMPTZ NOT NULL,
    -- CLV implícito
    clv_implied_home            NUMERIC(8,4),
    clv_implied_away            NUMERIC(8,4),
    -- Microestrutura de mercado
    odd_movement_1h_home        NUMERIC(8,4),
    odd_movement_1h_away        NUMERIC(8,4),
    odd_movement_6h_home        NUMERIC(8,4),
    odd_movement_6h_away        NUMERIC(8,4),
    odd_movement_24h_home       NUMERIC(8,4),
    odd_movement_24h_away       NUMERIC(8,4),
    odd_velocity_1h_home        NUMERIC(8,4),     -- Velocidade de movimento
    odd_velocity_1h_away        NUMERIC(8,4),
    volume_1h                   NUMERIC(12,2),
    volume_6h                   NUMERIC(12,2),
    -- Dispersão de odds
    odd_dispersion              NUMERIC(8,4),     -- Desvio padrão entre casas
    -- Sharp money indicator
    sharp_money_indicator       NUMERIC(8,4),     -- Movimento Betfair SP vs The Odds API
    calculated_at               TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(game_id, captured_at)
);

-- Módulo C: Contexto de Jogo (18 features)
CREATE TABLE gold.feat_game_context (
    id              BIGSERIAL PRIMARY KEY,
    game_id         VARCHAR(20) NOT NULL,
    -- Descanso assimétrico (CRÍTICO)
    rest_days_home              INTEGER NOT NULL,
    rest_days_away              INTEGER NOT NULL,
    rest_days_diff              INTEGER NOT NULL,   -- home_rest - away_rest
    rest_advantage_flag         BOOLEAN DEFAULT FALSE,  -- TRUE se diff >= 2
    -- Back-to-back detalhado
    b2b_home                    BOOLEAN DEFAULT FALSE,
    b2b_away                    BOOLEAN DEFAULT FALSE,
    b2b_advantage_flag          BOOLEAN DEFAULT FALSE,
    -- Viagens e fadiga (CRÍTICO)
    travel_distance_7d_home     NUMERIC(8,1) DEFAULT 0,
    travel_distance_7d_away     NUMERIC(8,1) DEFAULT 0,
    travel_advantage_flag       BOOLEAN DEFAULT FALSE,
    timezones_crossed_home      INTEGER DEFAULT 0,
    timezones_crossed_away      INTEGER DEFAULT 0,
    altitude_change_home        NUMERIC(8,1) DEFAULT 0,
    altitude_change_away        NUMERIC(8,1) DEFAULT 0,
    -- Jogos recentes
    games_last_5d_home          INTEGER DEFAULT 0,
    games_last_5d_away          INTEGER DEFAULT 0,
    games_last_7d_home          INTEGER DEFAULT 0,
    games_last_7d_away          INTEGER DEFAULT 0,
    -- Home court
    is_home_game_for            VARCHAR(5),         -- "HOME" or "AWAY" (perspetiva do home_team)
    calculated_at               TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(game_id)
);

-- Módulo D: On/Off Impact de Jogadores (20 features)
CREATE TABLE gold.feat_player_impact (
    id              BIGSERIAL PRIMARY KEY,
    game_id         VARCHAR(20) NOT NULL,
    team_id         INTEGER NOT NULL,
    -- Agregados por equipa
    total_injury_impact         NUMERIC(8,4),      -- Soma ponderada dos impactos
    num_players_out             INTEGER DEFAULT 0,
    num_players_questionable    INTEGER DEFAULT 0,
    num_key_players_out         INTEGER DEFAULT 0,
    -- Top 5 jogadores (individual)
    p1_on_off_net_rating        NUMERIC(8,4),
    p1_minutes_pct              NUMERIC(5,1),
    p1_injury_flag              BOOLEAN DEFAULT FALSE,
    p2_on_off_net_rating        NUMERIC(8,4),
    p2_minutes_pct              NUMERIC(5,1),
    p2_injury_flag              BOOLEAN DEFAULT FALSE,
    p3_on_off_net_rating        NUMERIC(8,4),
    p3_minutes_pct              NUMERIC(5,1),
    p3_injury_flag              BOOLEAN DEFAULT FALSE,
    p4_on_off_net_rating        NUMERIC(8,4),
    p4_minutes_pct              NUMERIC(5,1),
    p4_injury_flag              BOOLEAN DEFAULT FALSE,
    p5_on_off_net_rating        NUMERIC(8,4),
    p5_minutes_pct              NUMERIC(5,1),
    p5_injury_flag              BOOLEAN DEFAULT FALSE,
    calculated_at               TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(game_id, team_id)
);

-- Módulo E: Interações Não-Lineares (15 features)
CREATE TABLE gold.feat_interactions (
    id              BIGSERIAL PRIMARY KEY,
    game_id         VARCHAR(20) NOT NULL,
    -- Pace × Rating defensivo
    pace_off_x_def_rating_home  NUMERIC(8,4),
    pace_off_x_def_rating_away  NUMERIC(8,4),
    -- eFG% ofensivo × eFG% defensivo
    efg_off_x_efg_def_home      NUMERIC(8,4),
    efg_off_x_efg_def_away      NUMERIC(8,4),
    -- Back-to-back × idade média
    b2b_x_avg_age_home          NUMERIC(8,4),
    b2b_x_avg_age_away          NUMERIC(8,4),
    -- Descanso × viagem
    rest_advantage_x_travel_diff NUMERIC(8,4),
    -- Lesão × descanso
    injury_impact_x_rest_advantage NUMERIC(8,4),
    -- Pressão de mercado × momentum
    market_pressure_x_form_momentum NUMERIC(8,4),
    calculated_at               TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(game_id)
);
```

### 4.4 Camada Meta (Operacional)

```sql
-- ============================================================
-- META: Dados operacionais do sistema
-- ============================================================

CREATE SCHEMA IF NOT EXISTS meta;

-- Execuções de pipelines
CREATE TABLE meta.pipeline_runs (
    id              BIGSERIAL PRIMARY KEY,
    pipeline_name   VARCHAR(50) NOT NULL,        -- "ingestion_nba", "feature_engineering"
    status          VARCHAR(20) NOT NULL,        -- "RUNNING", "SUCCESS", "FAILED"
    started_at      TIMESTAMPTZ NOT NULL,
    finished_at     TIMESTAMPTZ,
    records_processed INTEGER,
    error_message   TEXT,
    run_id          UUID NOT NULL UNIQUE
);

-- Sinais gerados
CREATE TABLE meta.signals (
    signal_id       VARCHAR(30) PRIMARY KEY,     -- "SIG-20261015-001"
    game_id         VARCHAR(20) NOT NULL,
    market_type     VARCHAR(30) NOT NULL,
    selection       VARCHAR(50) NOT NULL,
    odd_recommended NUMERIC(8,3) NOT NULL,
    odd_minimum     NUMERIC(8,3) NOT NULL,
    edge_pct        NUMERIC(8,4) NOT NULL,
    prob_calibrated NUMERIC(8,4) NOT NULL,
    prob_meta       NUMERIC(8,4) NOT NULL,
    stake_euros     NUMERIC(10,2) NOT NULL,
    stake_pct       NUMERIC(5,2) NOT NULL,
    generated_at    TIMESTAMPTZ NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,         -- +5 min
    status          VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, EXECUTED, EXPIRED, SKIPPED
    executed_at     TIMESTAMPTZ,
    executed_odd    NUMERIC(8,3),
    executed_stake  NUMERIC(10,2),
    slippage_pct    NUMERIC(5,2),
    result          VARCHAR(20),                  -- WIN, LOSS, VOID, PENDING
    pnl_euros       NUMERIC(10,2)
);

CREATE INDEX idx_signals_date ON meta.signals(generated_at);
CREATE INDEX idx_signals_status ON meta.signals(status);

-- Circuit breakers
CREATE TABLE meta.circuit_breakers (
    id              BIGSERIAL PRIMARY KEY,
    breaker_name    VARCHAR(20) NOT NULL,         -- "ALPHA", "BETA", "GAMMA", "DELTA"
    status          VARCHAR(10) NOT NULL DEFAULT 'INACTIVE',
    trigger_reason  TEXT,
    triggered_at    TIMESTAMPTZ,
    resolved_at     TIMESTAMPTZ,
    current_value   NUMERIC(10,4),               -- Valor atual da métrica
    threshold_value NUMERIC(10,4)                -- Valor que ativa o breaker
);

-- Versões de modelos
CREATE TABLE meta.model_versions (
    id              BIGSERIAL PRIMARY KEY,
    model_name      VARCHAR(50) NOT NULL,         -- "xgboost_primary", "meta_labeling"
    version         VARCHAR(20) NOT NULL,         -- "v1.2.3"
    mlflow_run_id   VARCHAR(50),
    metrics_json    JSONB,                        -- {"clv": 0.032, "roi": 0.07, ...}
    is_production   BOOLEAN DEFAULT FALSE,
    deployed_at     TIMESTAMPTZ,
    UNIQUE(model_name, version)
);
```

---

## 5. PIPELINE DE DADOS

### 5.1 Diagrama de Ingestão

```
CRON (cada 30-60 min) → Prefect Flow → Ingestão Paralela
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
            nba_api.py               betfair_odds.py           injuries.py
            (jogos + stats)          (odds em tempo real)      (ESPN + Twitter)
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              ▼
                                     Validação (validate.py)
                                     ├─ Schema check
                                     ├─ Range check (odd > 1.0, odd < 100.0)
                                     └─ Duplicate check
                                              │
                                              ▼
                                     PostgreSQL (bronze.raw_*)
                                              │
                                     Limpeza (cleaning/)
                                     ├─ Dedup
                                     ├─ Normalize teams/IDs
                                     └─ silver.clean_*
                                              │
                                     Features (features/)
                                     ├─ Módulo A: forma (15)
                                     ├─ Módulo B: mercado (12)
                                     ├─ Módulo C: contexto (18)
                                     ├─ Módulo D: jogadores (20)
                                     └─ Módulo E: interações (15)
                                              │
                                              ▼
                                     gold.feat_* (80 features)
```

### 5.2 Código do Orquestrador de Ingestão

```python
# src/ingestion/orchestrator.py

from prefect import flow, task
from prefect.cache import cache
from datetime import datetime, timedelta

from src.ingestion.nba_api import NBAAPIIngestor
from src.ingestion.betfair_odds import BetfairOddsIngestor
from src.ingestion.betfair_sp import BetfairSPIngestor
from src.ingestion.the_odds_api import TheOddsAPIIngestor
from src.ingestion.injuries import InjuryIngestor
from src.cleaning.orchestrator import run_cleaning_pipeline
from src.features.orchestrator import run_feature_pipeline

@task(retries=3, retry_delay_seconds=30)
def ingest_nba_games(date: str):
    ingestor = NBAAPIIngestor()
    return ingestor.fetch_games_for_date(date)

@task(retries=2, retry_delay_seconds=10)
def ingest_betfair_odds(game_ids: list[str]):
    ingestor = BetfairOddsIngestor()
    return ingestor.fetch_current_odds(game_ids)

@task(retries=2, retry_delay_seconds=10)
def ingest_injuries():
    ingestor = InjuryIngestor()
    return ingestor.fetch_active_injuries()

@flow(name="Daily Ingestion Pipeline", log_prints=True)
def daily_ingestion_pipeline():
    """
    Pipeline de ingestão executado em batch a cada 2 horas em dias de jogo NBA (08:00, 10:00, 12:00, 14:00, 16:00 UTC).
    Ingestão contínua de odds via WebSocket/cache a cada 5 minutos para capturar movimentos intra-jogo.
    1. Recolhe dados NBA (jogos do dia, estatísticas)
    2. Recolhe odds em tempo real da Betfair
    3. Recolhe odds de fecho: Betfair SP (gratuito) + The Odds API Standard (validação cruzada)
    4. Recolhe lesões ativas
    5. Executa limpeza (Bronze → Silver)
    6. Executa feature engineering (Silver → Gold)
    """
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"[{datetime.now()}] Iniciando pipeline de ingestão para {today}")

    # 1. NBA Games
    games = ingest_nba_games(today)
    game_ids = [g["game_id"] for g in games]

    # 2. Betfair Odds
    odds = ingest_betfair_odds(game_ids)

    # 3. Injuries
    injuries = ingest_injuries()

    # 4. Cleaning pipeline
    cleaning_result = run_cleaning_pipeline()

    # 5. Feature pipeline (só se houver dados novos)
    if cleaning_result["records_processed"] > 0:
        feature_result = run_feature_pipeline()
        print(f"Features calculadas: {feature_result['features_generated']}")

    print(f"[{datetime.now()}] Pipeline concluído.")
    return {"games": len(games), "odds": len(odds), "injuries": len(injuries)}
```

---

## 6. FEATURE ENGINEERING

### 6.1 Estrutura Base

```python
# src/features/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
import pandas as pd

@dataclass
class FeatureConfig:
    """Configuração de feature engineering."""
    half_life_games: int = 5         # Decaimento exponencial (half-life)
    lookback_games: int = 20         # Janela máxima de jogos
    min_games_for_features: int = 5  # Mínimo para features confiáveis

class BaseFeatureBuilder(ABC):
    """Classe base para builders de features."""

    def __init__(self, config: FeatureConfig):
        self.config = config

    @abstractmethod
    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """Constrói features. Retorna DataFrame com colunas de features."""
        ...

    def exponential_decay(self, values: pd.Series) -> pd.Series:
        """
        Aplica decaimento exponencial com half-life configurável.
        Pesos: w[i] = 2^(-i / half_life)
        """
        n = len(values)
        weights = 2 ** (-pd.Series(range(n)) / self.config.half_life_games)
        weights = weights / weights.sum()  # Normalizar
        return (values * weights).sum()
```

### 6.2 Exemplo: Forma Recente

```python
# src/features/form.py

import pandas as pd
import numpy as np
from src.features.base import BaseFeatureBuilder, FeatureConfig

class FormFeatureBuilder(BaseFeatureBuilder):
    """
    Módulo A: Features de forma recente (15 features de output).
    Calcula métricas de desempenho recente com decaimento exponencial.
    """

    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Input: df com colunas [team_id, game_date, pts_scored, pts_allowed,
               efg_pct, tov_pct, orb_pct, ft_fga, off_rating, def_rating, result]
        Output: DataFrame com 15 colunas de features de forma
        """
        features = []

        for team_id in df['team_id'].unique():
            team_df = df[df['team_id'] == team_id].sort_values('game_date')

            for idx, row in team_df.iterrows():
                # Janela de jogos anteriores (sem look-ahead!)
                prior_games = team_df[team_df['game_date'] < row['game_date']].tail(
                    self.config.lookback_games
                )

                if len(prior_games) < self.config.min_games_for_features:
                    continue

                feat = {
                    'team_id': team_id,
                    'game_date': row['game_date'],
                    # Win rate ponderado (half-life)
                    'win_rate_weighted': self.exponential_decay(
                        (prior_games['result'] == 'W').astype(float)
                    ),
                    # Four Factors com decaimento
                    'efg_pct_weighted': self.exponential_decay(prior_games['efg_pct']),
                    'tov_pct_weighted': self.exponential_decay(prior_games['tov_pct']),
                    'orb_pct_weighted': self.exponential_decay(prior_games['orb_pct']),
                    'ft_fga_weighted': self.exponential_decay(prior_games['ft_fga']),
                    # Net Rating
                    'net_rating_weighted': self.exponential_decay(
                        prior_games['off_rating'] - prior_games['def_rating']
                    ),
                    'off_rating_weighted': self.exponential_decay(prior_games['off_rating']),
                    'def_rating_weighted': self.exponential_decay(prior_games['def_rating']),
                    # Momentum (últimos 3 vs época)
                    'off_rating_momentum_3g': (
                        prior_games['off_rating'].tail(3).mean()
                        - prior_games['off_rating'].mean()
                    ),
                    'def_rating_momentum_3g': (
                        prior_games['def_rating'].tail(3).mean()
                        - prior_games['def_rating'].mean()
                    ),
                    # Forma bruta
                    'wins_last_5': int((prior_games.tail(5)['result'] == 'W').sum()),
                    'wins_last_10': int((prior_games.tail(10)['result'] == 'W').sum()),
                    'avg_margin_last_5': (
                        prior_games.tail(5)['pts_scored'] - prior_games.tail(5)['pts_allowed']
                    ).mean(),
                    'avg_margin_last_10': (
                        prior_games.tail(10)['pts_scored'] - prior_games.tail(10)['pts_allowed']
                    ).mean(),
                }
                features.append(feat)

        return pd.DataFrame(features)
```

---

## 7. MODELAÇÃO — ENSEMBLE STACKING + META-LABELING

### 7.1 Arquitetura do Ensemble

```python
# src/models/ensemble.py

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic_regression import IsotonicRegression
import mlflow
import optuna

from src.models.xgboost_model import XGBoostModel
from src.models.lightgbm_model import LightGBMModel
from src.models.catboost_model import CatBoostModel

class StackingEnsemble:
    """
    Ensemble stacking com 3 modelos base + meta-modelo linear.
    Usa out-of-fold predictions para evitar overfitting.
    """

    def __init__(self):
        self.base_models = {
            'xgboost': XGBoostModel(),
            'lightgbm': LightGBMModel(),
            'catboost': CatBoostModel(),
        }
        self.meta_model = LogisticRegression(C=1.0, penalty='l2', solver='lbfgs')
        self.calibrators = {}  # IsotonicRegression por regime

    def train_with_oof(self, X: pd.DataFrame, y: pd.Series,
                       dates: pd.Series, n_splits: int = 5) -> dict:
        """
        Treina ensemble com out-of-fold predictions.
        Usa TimeSeriesSplit para respeitar ordem temporal.
        """
        tscv = TimeSeriesSplit(n_splits=n_splits)
        oof_predictions = np.zeros((len(X), len(self.base_models)))

        with mlflow.start_run(run_name="ensemble_training"):
            for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

                for i, (name, model) in enumerate(self.base_models.items()):
                    # Treinar modelo base
                    model.fit(X_train, y_train, X_val, y_val)

                    # Out-of-fold predictions
                    oof_predictions[val_idx, i] = model.predict_proba(X_val)

                    # Log metrics
                    auc = model.evaluate(X_val, y_val)
                    mlflow.log_metric(f"{name}_auc_fold{fold}", auc)

            # Treinar meta-modelo com OOF predictions
            self.meta_model.fit(oof_predictions, y)

            # Log meta-model
            mlflow.sklearn.log_model(self.meta_model, "meta_model")
            mlflow.log_param("n_base_models", len(self.base_models))

        return {
            'meta_model_coef': self.meta_model.coef_.tolist(),
            'meta_model_intercept': float(self.meta_model.intercept_[0]),
        }

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Faz predição: cada modelo base → stacking → probabilidade final.
        """
        base_preds = np.zeros((len(X), len(self.base_models)))

        for i, (name, model) in enumerate(self.base_models.items()):
            base_preds[:, i] = model.predict_proba(X)

        # Meta-modelo combina as previsões
        return self.meta_model.predict_proba(base_preds)[:, 1]

    def calibrate(self, probs: np.ndarray, y: np.ndarray,
                  regimes: np.ndarray) -> dict:
        """
        Calibração isotónica por regime.
        regimes: array com 'favorite', 'balanced', 'underdog'
        """
        for regime in ['favorite', 'balanced', 'underdog']:
            mask = regimes == regime
            if mask.sum() < 50:
                continue  # Dados insuficientes

            calibrator = IsotonicRegression(out_of_bounds='clip')
            calibrator.fit(probs[mask], y[mask])
            self.calibrators[regime] = calibrator

        return {r: len(self.calibrators) for r in self.calibrators}
```

### 7.2 Meta-Labeling Model

```python
# src/models/meta_model.py

import xgboost as xgb
import numpy as np
import pandas as pd

class MetaLabelingModel:
    """
    Modelo secundário que prevê se um sinal com edge > 4%
    terá realmente CLV positivo.

    Target: 1 se CLV_expost > 0 (odd_betfair_sp > odd_aposta)
            0 caso contrário
    """

    def __init__(self):
        self.model = xgb.XGBClassifier(
            objective='binary:logistic',
            max_depth=3,               # Mais simples que primário
            learning_rate=0.03,
            n_estimators=500,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=30,
            reg_alpha=0.5,             # Regularização mais forte
            reg_lambda=1.0,
            random_state=42,
        )

    def build_meta_features(self, primary_prob: float, edge: float,
                            regime: str, num_games_data: int,
                            odd_current: float) -> np.ndarray:
        """
        Constrói features para o meta-modelo.
        """
        # Entropia da probabilidade (medida de confiança)
        p = primary_prob
        entropy = -p * np.log2(max(p, 1e-10)) - (1-p) * np.log2(max(1-p, 1e-10))

        # Edge em percentagem
        edge_pct = edge * 100

        # Features
        features = np.array([
            primary_prob,              # P_modelo
            edge_pct,                  # Edge em %
            entropy,                   # Confiança da previsão
            1 if regime == 'favorite' else 0,
            1 if regime == 'underdog' else 0,
            num_games_data,            # Quantidade de dados usados
            odd_current,               # Odd atual
            1 / odd_current,           # Probabilidade implícita do mercado
            primary_prob - (1 / odd_current),  # Diferença modelo vs mercado
        ])
        return features.reshape(1, -1)

    def predict(self, primary_prob: float, edge: float,
                regime: str, num_games_data: int,
                odd_current: float) -> float:
        """
        Retorna P(CLV > 0 | edge).
        """
        X = self.build_meta_features(
            primary_prob, edge, regime, num_games_data, odd_current
        )
        return float(self.model.predict_proba(X)[0, 1])
```

### 7.3 Online Learning (EWA)

```python
# src/models/online_learning.py

from dataclasses import dataclass, field
from typing import Dict

@dataclass
class TeamRating:
    rating: float = 0.5
    uncertainty: float = 0.1  # Incerteza da estimativa

class EWATeamRatings:
    """
    Exponentially Weighted Average para ratings de equipas.
    Atualiza ratings após cada jogo.
    """

    def __init__(self, alpha: float = 0.1):
        self.alpha = alpha
        self.ratings: Dict[int, TeamRating] = {}

    def get_rating(self, team_id: int) -> float:
        """Obtém rating atual (ou default 0.5)."""
        if team_id not in self.ratings:
            self.ratings[team_id] = TeamRating(rating=0.5)
        return self.ratings[team_id].rating

    def update(self, team_id: int, observed: float, expected: float):
        """
        Atualiza rating com EWA.
        observed: performance real (ex: 1 para vitória, 0 para derrota)
        expected: performance esperada (ex: 0.55 probabilidade)
        """
        if team_id not in self.ratings:
            self.ratings[team_id] = TeamRating(rating=0.5)

        rating = self.ratings[team_id]
        error = observed - expected
        rating.rating += self.alpha * error

        # Clamp entre 0.05 e 0.95
        rating.rating = max(0.05, min(0.95, rating.rating))

    def get_all_ratings(self) -> Dict[int, float]:
        """Retorna todos os ratings como feature."""
        return {tid: r.rating for tid, r in self.ratings.items()}
```

---

## 8. VALIDAÇÃO E BACKTEST

### 8.1 Purged Walk-Forward CV

```python
# src/backtest/walk_forward.py

import pandas as pd
import numpy as np
from typing import List, Tuple
from datetime import timedelta

class PurgedWalkForward:
    """
    Implementa walk-forward cross-validation com purging e embargo.
    
    Evita leakage temporal:
    - Purge: remove eventos de treino que têm overlap temporal com validação
    - Embargo: remove eventos próximos temporalmente da fronteira treino/validação
    """

    def __init__(self, embargo_days: int = 2, purge_days: int = 1):
        self.embargo_days = embargo_days
        self.purge_days = purge_days

    def split(self, df: pd.DataFrame, date_col: str = 'game_date',
              n_splits: int = 12) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Divide dataset temporalmente para walk-forward CV.
        Retorna lista de (train_df, val_df).
        """
        df = df.sort_values(date_col).reset_index(drop=True)
        dates = df[date_col].unique()
        n_dates = len(dates)

        # Cada fold: treino = histórico até data_i, validação = data_i+1
        fold_size = n_dates // n_splits
        folds = []

        for i in range(1, n_splits):
            train_end_idx = i * fold_size
            val_start_idx = train_end_idx + 1
            val_end_idx = min((i + 1) * fold_size, n_dates - 1)

            # Datas de treino e validação
            train_dates = dates[:train_end_idx]
            val_dates = dates[val_start_idx:val_end_idx]

            # Aplicar embargo
            embargo_cutoff = dates[train_end_idx] + timedelta(days=self.embargo_days)
            train_dates = [d for d in train_dates if d < embargo_cutoff]

            # Filtrar DataFrames
            train_df = df[df[date_col].isin(train_dates)]
            val_df = df[df[date_col].isin(val_dates)]

            if len(train_df) > 100 and len(val_df) > 10:
                folds.append((train_df, val_df))

        return folds
```

### 8.2 Métricas de Backtest

```python
# src/backtest/metrics.py

import numpy as np
import pandas as pd
from scipy import stats

def calculate_clv(odds_used: np.ndarray, odds_closing: np.ndarray) -> float:
    """
    Closing Line Value: diferença média entre odd usada e odd de fecho (proxy Betfair SP).
    CLV > 0 indica edge positivo.
    """
    clv = np.mean((odds_used - odds_closing) / odds_closing)
    return float(clv)

def calculate_roi(stakes: np.ndarray, pnl: np.ndarray) -> float:
    """
    Return on Investment: PnL total / stakes totais.
    """
    total_staked = np.sum(stakes)
    total_pnl = np.sum(pnl)
    return float(total_pnl / total_staked) if total_staked > 0 else 0.0

def calculate_sharpe(returns: np.ndarray, risk_free_rate: float = 0.0) -> float:
    """
    Sharpe Ratio: retorno médio / desvio padrão dos retornos.
    Annualizado assumindo 250 dias de trading.
    """
    excess_returns = returns - risk_free_rate
    if np.std(excess_returns) == 0:
        return 0.0
    sharpe = np.mean(excess_returns) / np.std(excess_returns)
    return float(sharpe * np.sqrt(250))

def calculate_brier_score(probs: np.ndarray, outcomes: np.ndarray) -> float:
    """
    Brier Score: erro quadrático médio entre probabilidades e outcomes.
    Menor é melhor. Comparar com Brier do mercado.
    """
    return float(np.mean((probs - outcomes) ** 2))

def calculate_ece(probs: np.ndarray, outcomes: np.ndarray, n_bins: int = 10) -> float:
    """
    Expected Calibration Error.
    ECE < 0.05 é considerado bem calibrado.
    """
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(probs)

    for i in range(n_bins):
        mask = (probs >= bins[i]) & (probs < bins[i + 1])
        if mask.sum() > 0:
            bin_acc = np.mean(outcomes[mask])
            bin_conf = np.mean(probs[mask])
            ece += (mask.sum() / n) * abs(bin_acc - bin_conf)

    return float(ece)

def calculate_max_drawdown(cumulative_returns: np.ndarray) -> float:
    """
    Maximum Drawdown: maior queda do pico ao vale.
    """
    peak = np.maximum.accumulate(cumulative_returns)
    drawdown = (peak - cumulative_returns) / peak
    return float(np.max(drawdown))

def t_test_edge(clv_values: np.ndarray, alpha: float = 0.05) -> dict:
    """
    Teste t para verificar se CLV é estatisticamente > 0.
    """
    t_stat, p_value = stats.ttest_1samp(clv_values, 0.0)
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_value / 2),  # One-sided
        'significant': bool(p_value / 2 < alpha),
        'ci_95_lower': float(np.mean(clv_values) - 1.96 * stats.sem(clv_values)),
        'ci_95_upper': float(np.mean(clv_values) + 1.96 * stats.sem(clv_values)),
    }
```

---

## 9. MOTOR DE EDGE E GERAÇÃO DE SINAIS

```python
# src/engine/orchestrator.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List
import numpy as np
import redis

from src.models.ensemble import StackingEnsemble
from src.models.meta_model import MetaLabelingModel
from src.risk.kelly import KellyCalculator
from src.risk.circuit_breakers import CircuitBreakerManager
from config.settings import settings
from config.thresholds import THRESHOLDS

@dataclass
class Signal:
    signal_id: str
    game_id: str
    market_type: str          # "MONEYLINE", "SPREAD"
    selection_name: str       # "Boston Celtics"
    selection_id: int
    odd_recommended: float
    odd_minimum: float
    edge_pct: float
    prob_calibrated: float
    prob_meta: float
    stake_euros: float
    stake_pct: float
    generated_at: datetime
    expires_at: datetime

class ValueEngine:
    """
    Motor de decisão completo.
    Processa todos os jogos do dia e gera sinais aprovados.
    """

    def __init__(self):
        self.ensemble = self._load_production_ensemble()
        self.meta_model = self._load_meta_model()
        self.kelly = KellyCalculator(K=settings.KELLY_K)
        self.breakers = CircuitBreakerManager()
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self._signal_counter = 0

    def run(self, games: List[dict]) -> List[Signal]:
        """
        Processa todos os jogos e retorna sinais aprovados.
        Executado a cada 2 horas (10:00, 12:00, 14:00, 16:00).
        """
        # Verificar circuit breakers antes de começar
        if not self.breakers.can_generate_signals():
            print("Circuit breaker ativo. Nenhum sinal gerado.")
            return []

        approved_signals = []

        for game in games:
            signal = self._process_game(game)
            if signal is not None:
                approved_signals.append(signal)

        # Aplicar limites de exposição diária
        approved_signals = self._apply_exposure_limits(approved_signals)

        # Persistir sinais
        self._persist_signals(approved_signals)

        return approved_signals

    def _process_game(self, game: dict) -> Optional[Signal]:
        """
        Processa um jogo individual.
        1. Carregar features
        2. Inferência do ensemble → probabilidade
        3. Calibração por regime
        4. Cálculo de edge
        5. Meta-labeling
        6. Se aprovado, calcular stake
        """
        # 1. Features
        features = self._load_features(game['game_id'])
        if features is None:
            return None

        # 2. Ensemble prediction
        prob_raw = self.ensemble.predict_proba(features)

        # 3. Calibração por regime
        regime = self._get_regime(prob_raw)
        prob_cal = self.ensemble.calibrators.get(regime, lambda x: x)(prob_raw)

        # 4. Edge
        odd_current = game['odd_betfair']
        edge = prob_cal * odd_current - 1.0

        # 5. Filtros básicos
        if edge <= THRESHOLDS['edge_min']:
            return None
        if prob_cal < THRESHOLDS['prob_min'] or prob_cal > THRESHOLDS['prob_max']:
            return None
        if game.get('volume', 0) < THRESHOLDS['min_volume']:
            return None

        # 6. Meta-labeling
        prob_meta = self.meta_model.predict(
            primary_prob=prob_cal,
            edge=edge,
            regime=regime,
            num_games_data=features.shape[1],  # proxy de qualidade
            odd_current=odd_current,
        )
        if prob_meta < THRESHOLDS['prob_meta_min']:
            return None

        # 7. Calcular stake
        stake_pct, stake_euros = self.kelly.calculate(
            prob=prob_cal,
            odd=odd_current,
            bankroll=self._get_bankroll(),
            edge=edge,
        )

        # 8. Criar sinal
        self._signal_counter += 1
        signal_id = f"SIG-{datetime.now().strftime('%Y%m%d')}-{self._signal_counter:03d}"

        return Signal(
            signal_id=signal_id,
            game_id=game['game_id'],
            market_type=game['market_type'],
            selection_name=game['selection_name'],
            selection_id=game['selection_id'],
            odd_recommended=odd_current,
            odd_minimum=odd_current * 0.99,  # 1% slippage máximo
            edge_pct=edge * 100,
            prob_calibrated=prob_cal,
            prob_meta=prob_meta,
            stake_euros=stake_euros,
            stake_pct=stake_pct * 100,
            generated_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=5),
        )

    def _apply_exposure_limits(self, signals: List[Signal]) -> List[Signal]:
        """Aplica limites: 2%/aposta, 4%/jogo, 12%/dia."""
        bankroll = self._get_bankroll()
        daily_exposure = 0.0
        approved = []

        # Ordenar por edge * prob_meta (melhores primeiro)
        signals.sort(key=lambda s: s.edge_pct * s.prob_meta, reverse=True)

        for signal in signals:
            stake = signal.stake_euros

            # Limite diário
            if daily_exposure + stake > bankroll * THRESHOLDS['max_daily_exposure']:
                continue

            # Limite por jogo
            game_exposure = sum(
                s.stake_euros for s in approved if s.game_id == signal.game_id
            )
            if game_exposure + stake > bankroll * THRESHOLDS['max_game_exposure']:
                continue

            approved.append(signal)
            daily_exposure += stake

        return approved

    def _get_bankroll(self) -> float:
        return float(self.redis_client.get('bankroll') or 1000.0)

    def _get_regime(self, prob: float) -> str:
        if prob >= 0.65:
            return 'favorite'
        elif prob < 0.35:
            return 'underdog'
        return 'balanced'

    def _load_features(self, game_id: str) -> Optional[np.ndarray]:
        # Implementação real: query gold.feat_* e concatenar
        pass

    def _load_production_ensemble(self) -> StackingEnsemble:
        # Carregar do MLflow registry (versão em produção)
        pass

    def _load_meta_model(self) -> MetaLabelingModel:
        pass

    def _persist_signals(self, signals: List[Signal]):
        """Persiste sinais em PostgreSQL + cache Redis."""
        for signal in signals:
            # Cache para Telegram Bot
            self.redis_client.hset(
                f"signal:{signal.signal_id}",
                mapping={
                    'game_id': signal.game_id,
                    'market_type': signal.market_type,
                    'selection': signal.selection_name,
                    'odd': str(signal.odd_recommended),
                    'edge': str(signal.edge_pct),
                    'stake': str(signal.stake_euros),
                    'expires_at': signal.expires_at.isoformat(),
                }
            )
            self.redis_client.expire(f"signal:{signal.signal_id}", 300)  # 5 min
```

---

## 10. GESTÃO DE RISCO E SIZING

```python
# src/risk/kelly.py

import numpy as np

class KellyCalculator:
    """
    Calcula stake ótimo usando Kelly Criterion fracionado.
    Com limites absolutos (hard caps) e ajuste de drawdown.
    """

    def __init__(self, K: float = 0.5):
        """
        K: fator de conservadorismo.
        0.5 = meio Kelly (recomendado para sistemas reais)
        0.25 = quarter Kelly (drawdown alto)
        1.0 = Kelly completo (apenas teórico, NÃO USAR)
        """
        self.K = K
        self.max_stake_pct = 0.02    # 2% do bankroll
        self.max_game_pct = 0.04     # 4% por jogo
        self.max_daily_pct = 0.12    # 12% por dia

    def kelly_fraction(self, prob: float, odd: float) -> float:
        """
        Fração ótima de Kelly: f* = (p*b - q) / b
        onde b = odd - 1 (net odds), q = 1 - p
        """
        if prob * odd <= 1.0:
            return 0.0  # Sem edge positivo

        b = odd - 1.0  # Net odds
        q = 1.0 - prob
        f_kelly = (prob * b - q) / b
        return max(0.0, f_kelly)

    def calculate(self, prob: float, odd: float,
                  bankroll: float, edge: float,
                  current_drawdown: float = 0.0) -> tuple:
        """
        Calcula (stake_pct, stake_euros) para uma aposta.
        """
        # 1. Kelly fracionado
        f_kelly = self.kelly_fraction(prob, odd)
        f = self.K * f_kelly

        # 2. Ajuste de drawdown
        if current_drawdown > 0.15:
            f *= 0.5   # Reduzir 50% se drawdown > 15%
        elif current_drawdown > 0.10:
            f *= 0.75  # Reduzir 25% se drawdown > 10%

        # 3. Hard cap: 2% do bankroll
        stake_pct = min(f, self.max_stake_pct)
        stake_euros = stake_pct * bankroll

        return stake_pct, round(stake_euros, 2)


class CircuitBreakerManager:
    """
    Gere circuit breakers do sistema.
    Todos os breakers sao automaticos e requerem audit log para override manual.
    """

    BREAKERS = {
        'ALPHA': {
            'name': 'Drawdown Protection',
            'trigger': lambda m: m['drawdown'] > 0.15,
            'action': 'reduce_stakes_50pct',
            'recovery': lambda m: m['drawdown'] < 0.10,
        },
        'BETA': {
            'name': 'Consecutive Losses',
            'trigger': lambda m: m['consecutive_losses'] >= 5,
            'action': 'pause_1h_notify',
            'recovery': lambda m: True,
        },
        'GAMMA': {
            'name': 'CLV Negative 3-Day',
            'trigger': lambda m: m['clv_3d_avg'] < 0.0,
            'action': 'pause_new_signals',
            'recovery': lambda m: m['clv_3d_avg'] > 0.01,
        },
        'DELTA': {
            'name': 'Feed Offline',
            'trigger': lambda m: m['feed_offline_minutes'] > 5,
            'action': 'block_all_signals',
            'recovery': lambda m: m['feed_offline_minutes'] == 0,
        },
        'EPSILON': {
            'name': 'Execution Errors',
            'trigger': lambda m: m['execution_errors_today'] > 3,
            'action': 'full_stop',
            'recovery': lambda m: True,
        },
    }

    def can_generate_signals(self) -> bool:
        for breaker_id, breaker in self.BREAKERS.items():
            if self._is_active(breaker_id):
                return False
        return True

    def _is_active(self, breaker_id: str) -> bool:
        pass  # Verificar no Redis/PostgreSQL


# ============================================================
# EXECUCAO DE APOSTAS (Betfair API)
# ============================================================

from dataclasses import dataclass
from enum import Enum

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"

@dataclass
class ExecutionResult:
    signal_id: str
    order_id: str
    status: OrderStatus
    odd_requested: float
    odd_executed: float
    stake_requested: float
    stake_executed: float
    slippage_pct: float
    time_to_fill_seconds: float

class BetfairAlgorithmicExecutor:
    """
    Execucao automatica via Betfair Exchange API.
    Fase 3 - apenas apos 6 meses de lucro comprovado.
    """

    def __init__(self, app_key: str, username: str, password: str):
        self.app_key = app_key
        self.username = username
        self.password = password

    def execute_signal(self, signal) -> ExecutionResult:
        """
        Coloca limit order e monitoriza ate 30 segundos.
        Cancela se odd piorar > 2%.
        """
        # Colocar limit order
        limit_price = signal.odd_recommended
        # (integracao real com betfairlightweight)
        return ExecutionResult(
            signal_id=signal.signal_id,
            order_id="order-001",
            status=OrderStatus.FILLED,
            odd_requested=signal.odd_recommended,
            odd_executed=signal.odd_recommended,
            stake_requested=signal.stake_euros,
            stake_executed=signal.stake_euros,
            slippage_pct=0.0,
            time_to_fill_seconds=5,
        )


# ============================================================
# ROTINA DIARIA (RESUMO)
# ============================================================

"""
HORARIO    ACAO                          RESPONSAVEL
--------   ----------------------------  -------------------
07:45      Verificar infraestrutura      Operador (dashboard)
08:00      Pipeline de ingestao          Automatico (Prefect)
08:15      Verificar banca Betfair       Operador
10:00      Motor de decisao (batch 1)    Automatico (cron)
12:00      Motor de decisao (batch 2)    Automatico
14:00      Motor de decisao (batch 3)    Automatico
16:00      Motor de decisao (batch 4)    Automatico
Conforme   Executar apostas              Operador / Automatico
23:00      Reconciliacao do dia          Automatico
23:30      Relatorio diario              Automatico (email)
"""


# ============================================================
# MONITORIZACAO E ALERTAS
# ============================================================

"""
DASHBOARDS GRAFANA:

1. Business Overview:
   - ROI acumulado (linha)
   - CLV medio (ultimas 50, 100 apostas)
   - Numero de apostas/dia
   - Drawdown atual vs maximo

2. Risk Monitoring:
   - Exposicao diaria (% da banca)
   - Circuit breakers status (todos)
   - Heatmap: win rate por dia da semana, regime

3. Model Performance:
   - CLV por regime (favorite, balanced, underdog)
   - Brier Score vs mercado
   - ECE (calibration error)
   - Data drift (PSI das features principais)

4. System Health:
   - CPU, RAM, Disco (VPS)
   - PostgreSQL connections, query latency
   - Pipeline runs (ultimas 24h, status)

ALERTAS (TELEGRAM):
   Nivel    Gatilho                              Canal
   ------   -----------------------------------  ----------
   P0       Sistema offline > 5 min              @ops_critical
   P1       Drawdown > 15%                       @ops_critical
   P1       Feed odds offline > 5 min            @ops_critical
   P2       CLV 3d < 0%                          @ops_warning
   P2       5 perdas consecutivas                @ops_warning
   P3       Modelo nao atualizado > 7 dias       @ops_info
"""


# ============================================================
# MLOPS - TREINO, DEPLOY E DRIFT
# ============================================================

"""
CICLO DE VIDA DO MODELO:

1. TREINO (semanal, segunda-feira)
   - Recolher dados da ultima semana
   - Walk-forward CV com nova janela
   - Otimizar hiperparametros (Optuna, apenas se drift detetado)
   - Gerar metricas: CLV, ROI, Sharpe, Brier, ECE

2. VALIDACAO (automatica)
   - Comparar metricas com modelo em producao
   - Se CLV > atual + 1%: promover para staging
   - Se nao: descartar

3. STAGING (24 horas)
   - Modelo em staging recebe 20% do trafego (A/B test)
   - Metricas monitorizadas em tempo real
   - Se performance superior confirmada: promover para producao

4. PRODUCAO
   - Modelo principal (80% do trafego)
   - Retreino programado semanalmente

5. DATA DRIFT (diario)
   - Calcular PSI para top 10 features
   - Se PSI > 0.2 em 3+ features: ALERTA
   - Se PSI > 0.3: RETREINO IMEDIATO obrigatorio

6. ROLLBACK
   - Se CLV producao < 1% por 3 dias consecutivos
   - Rollback automatico para versao anterior
"""


# ============================================================
# MODELO DE NEGOCIO
# ============================================================

"""
FONTES DE RECEITA:

1. OPERACAO PROPRIA (banca propria)
   - Capital inicial: 500-1000 EUR (Fase 4)
   - Crescimento composto via Kelly fracionado
   - Reinvestimento de 80% dos lucros

2. TIPSTER AS A SERVICE (subscricoes Telegram)
   - Preco unico: 29 EUR/mes (1 tier apenas - principio MVP)
   - Entrega: sinais via Telegram + email
   - Limite inicial: 100 subscritores (garante qualidade e exclusividade)
   - Pagamentos: Stripe
   - Receita alvo mes 6: 2.900 EUR/mes

3. EXPANSAO FUTURA (apenas apos 12 meses de track record validado)
   - Tiers adicionais (movidos para 41_Future_Expansion/INDEX.md)
   - API access para institucionais
   - Licenciamento do software
   - Investidores externos

METRICAS DE NEGOCIO:
   - CAC (Customer Acquisition Cost): < 40 EUR
   - LTV (Lifetime Value): > 348 EUR (12 meses)
   - LTV:CAC ratio: > 40x
   - Churn rate: < 5% ao mes
   - MRR: crescer 20%/mes
"""


# ============================================================
# ROADMAP DE EXECUCAO (12 MESES)
# ============================================================

"""
================================================================
              ROADMAP VBQ-UNIFIED — 12 MESES
================================================================

FASE 1: FUNDACOES COM RIGOR CIENTIFICO [MES 1]
  Semana 1-2:
    - Configurar VPS, PostgreSQL, Redis, Git
    - Recolher 5 epocas de dados historicos NBA
    - Implementar Purged Walk-Forward CV com embargo de 2 dias
    - Testes ADF e KPSS em features candidatas
  Semana 3-4:
    - Pipeline de feature engineering (80 features, 4 modulos)
    - Modulo A: Forma recente com half-life decay
    - Modulo B: Metricas de mercado + microestrutura
    - Modulo C: Contexto de jogo (descanso assimetrico, viagens)
    - Modulo D: On/Off impacto de jogadores
    - Modulo E: Interacoes nao-lineares
  MILESTONE: Features prontas, CV implementado, dados validados

FASE 2: MODELO COM META-LABELING [MES 2]
  Semana 1-3:
    - Treinar XGBoost primario + LightGBM + CatBoost
    - Implementar stacking ensemble com meta-modelo linear
    - Treinar meta-modelo de meta-labeling
    - Calibracao isotonica por regime (3 regimes)
  Semana 4:
    - Backtest walk-forward completo com comissoes (5%) e slippage (0.5%)
    - Simulacoes de Monte Carlo (10.000 runs)
    - Reliability diagrams + Brier Score + ECE
  MILESTONE: CLV > 2%, ROI > 5%, Sharpe > 0.5 no teste final

FASE 3: SHADOW MODE E TIPSTER BETA [MES 3]
  Semana 1-3:
    - Simular apostas em 3 fontes (Betfair, The Odds API casas, Bet365)
    - Registar True CLV para cada sinal (usando Betfair SP como proxy)
    - Afinar thresholds sem tocar no modelo
  Semana 4:
    - Criar canal Telegram privado (5-10 beta testers)
    - Documentos legais: Termos de Servico, Disclaimer de Risco
    - Pagina web de tracking publico (CLV, ROI, nº apostas)
  MILESTONE: Sinais gerados automaticamente, shadow mode validado

FASE 4: MICRO BANCA E VALIDACAO REAL [MES 4]
  Semana 1-4:
    - Depositar 500-1000 EUR na Betfair Exchange
    - Apostar manualmente todos os sinais
    - Registar: odd obtida vs sinalizada, tempo execucao, slippage real
    - Meta-avaliacao diaria: comparar performance real vs shadow mode
  MILESTONE: ROI real positivo e alinhado com backtest

FASE 5: ESTABILIZACAO E LANCAMENTO COMERCIAL [MES 5]
  Semana 1-2:
    - Automatizar relatorios diarios (CLV, ROI, drawdown)
    - Ajustar thresholds com dados reais (sem reotimizar modelo)
    - Implementar alertas Telegram (drawdown, falhas feed)
  Semana 3-4:
    - Abrir subscricoes ao publico: 29 EUR/mes
    - Limite inicial: 100 subscritores (maximo)
    - Continuar a apostar banca propria com mesmos sinais
  MILESTONE: 100 subscritores, receita cobre custos operacionais

FASE 6: EXPANSAO E ONE-CLICK [MES 6]
  Semana 1-2:
    - Adicionar Player Props NBA (pontos, ressaltos, assistencias)
    - Pipeline dedicado: backtest + shadow mode + micro banca
  Semana 3-4:
    - Implementar one-click betting (deep links Betfair)
    - Preparar documentacao para parceiros/investidores
  MILESTONE: Sistema multi-mercado, receita > custos

FASE 7: EXPANSAO MULTI-DESPORTO [MES 7-9]
  Mes 7:
    - Iniciar backtest Football (Asian Handicap ligas secundarias)
    - Iniciar recolha dados UFC/MMA
  Mes 8:
    - Shadow mode Football (3 casas)
    - Modelo Bayesiano para UFC Moneyline + Method of Victory
  Mes 9:
    - Micro banca Football 500 EUR, UFC 300 EUR
    - Motor de decisao unificado (NBA + Football + UFC)
  MILESTONE: 3 desportos operacionais, ROI total > 8%

FASE 8: AUTOMACAO E ESCALA [MES 10-12]
  Mes 10:
    - Execucao automatica completa (Betfair API, limit orders)
    - Escalar bancas: NBA 5000, Football 2000, UFC 1000 EUR
    - Tipster: avaliar expansao para 200+ subscritores (ver 41_Future_Expansion/INDEX.md)
  Mes 11:
    - Otimizar ensemble dos 3 desportos
    - Ajustar calibracao por regime com dados reais
    - Consolidar operacao multi-desporto
  Mes 12:
    - Automacao completa dos 3 desportos
    - Relatorio anual de performance
    - Planos para fase seguinte (mes 13-18: surebets, market making, investidores)
  MILESTONE: ROI total > 15%, operacao multi-desporto estavel e automatizada
"""


# ============================================================
# CIRCUIT BREAKERS E KILL CRITERIA
# ============================================================

"""
CIRCUIT BREAKERS (automaticos, sem override manual sem audit log):

  BREAKER    TRIGGER                        ACAO
  -------    ----------------------------   -------------------------
  ALPHA      Drawdown > 15%                 Reduzir stakes 50%
  BETA       5 perdas consecutivas          Pausa 1h + alerta ops
  GAMMA      CLV 3 dias < 0%                Pausa novas apostas
  DELTA      Feed odds offline > 5 min      Bloquear todos os sinais
  EPSILON    Erro execucao > 3x/dia         Paragem total do sistema

KILL CRITERIA POR DESPORTO:

  NBA:
    - 200 apostas: CLV < 1% E ROI < 0% com 95% confianca -> DESLIGAR
    - Drawdown > 25% durante 30 dias -> pausa e revisao
  
  Football:
    - 150 apostas: CLV < 1% E ROI < 0% com 95% confianca -> DESLIGAR
    - Drawdown > 20% durante 30 dias -> pausa e revisao
  
  MMA/UFC:
    - 100 apostas: CLV < 0.5% E ROI < 0% com 95% confianca -> DESLIGAR
    - Drawdown > 30% durante 20 dias -> DESLIGAR (MMA mais volatil)

PROCEDIMENTO DE DESLIGAMENTO:
  1. Reduzir stakes a zero imediatamente
  2. Manter recolha de dados para reavaliacao futura
  3. Comunicar aos subscritores: "Desporto X pausado para revisao"
  4. Analise de root cause em 7 dias
  5. Decisao: reativar com ajustes OU desligar permanentemente
"""


# ============================================================
# PLANOS DE CONTINGENCIA
# ============================================================

"""
CENARIOS DE STRESS TESTADOS:

  Cenario 1: Drawdown de 25%
    - Probabilidade: ~5% ao ano
    - Tempo medio de recuperacao: 45-60 dias
    - Acao: Nenhuma intervencao manual. Circuit breakers automaticos.
    - Comunicacao: "Drawdown de 25%. Sistema a funcionar como desenhado."

  Cenario 2: 15 Perdas Consecutivas
    - Probabilidade: ~0.1% ao ano
    - Impacto na banca: -15% a -30%
    - Acao: Sistema pausa automaticamente 24h. Revisao manual obrigatoria.

  Cenario 3: CLV Negativo por Mes Inteiro
    - Probabilidade: ~15% ao ano (variacao normal)
    - Acao: Continuar operacao se drawdown < 10%

  Cenario 4: Black Swan (COVID, cancelamento de ligas)
    - Liquidar posicoes abertas imediatamente
    - Pausa total ate normalizacao
    - Reserva de capital para cobertura

REGRA DE OURO PARA O OPERADOR:
  O operador NAO DEVE intervir manualmente durante drawdowns.
  A intervencao humana e o maior risco de ruina.
  O sistema foi desenhado para sobreviver a drawdowns de 25%.
"""


# ============================================================
# COMPLIANCE E LEGAL
# ============================================================

"""
DISCLAIMERS OBRIGATORIOS (em todas as comunicacoes):

  - "Apostas desportivas implicam risco de perda total do capital."
  - "Resultados passados nao garantem lucros futuros."
  - "Nao prestamos consultoria financeira."
  - "Aposte apenas o que pode perder."

DOCUMENTOS NECESSARIOS:
  - Termos de Servico (claros, sem promessas de lucro)
  - Politica de Privacidade (GDPR compliant)
  - Disclaimer visivel em TODAS as comunicacoes

REGULAMENTACAO:
  - Portugal (SRIJ): Licenca de jogo online NAO necessaria para tipster
  - GDPR: Consentimento explicito para dados pessoais
  - Consumidor EU: Direito de cancelamento em 14 dias
  - Stripe gere IVA automaticamente (MOSS)
"""


# ============================================================
# GLOSSARIO E REFERENCIAS
# ============================================================

"""
TERMOS CHAVE:

  CLV (Closing Line Value): Diferenca entre a odd apostada e a odd
      de fecho (proxy Betfair SP + validacao The Odds API). CLV > 0 indica edge. Metrica principal de sucesso.
  
  Edge: Vantagem matematica. edge = P_modelo * odd_mercado - 1.
      Edge > 4% necessario para gerar sinal.
  
  Kelly Criterion: Formula matematica para sizing otimo de apostas.
      Usamos meio Kelly (K=0.5) para conservadorismo.
  
  Purged CV: Cross-validation temporal que remove eventos com
      overlap entre treino e validacao para evitar look-ahead.
  
  Embargo: Periodo de exclusao entre dados de treino e validacao
      (2 dias) para evitar leakage de eventos proximos.
  
  Meta-Labeling: Modelo secundario que preve se um sinal do modelo
      primario e genuino ou falso positivo.
  
  PSI (Population Stability Index): Metrica de drift que compara
      distribuicoes de features entre periodos.
  
  ECE (Expected Calibration Error): Mede o quao bem calibradas
      estao as probabilidades do modelo.
  
  Sharpe Ratio: Retorno / volatilidade. > 0.5 e considerado bom
      para estrategias de betting.
  
  Drawdown: Queda percentual do pico da banca ao vale.
  
  Circuit Breaker: Mecanismo automatico que pausa ou reduz
      operacoes quando metricas de risco sao violadas.

REFERENCIAS:
  - Benter, W. (2008). Computer Based Horse Race Handicapping
  - Bailey, M., & Clarke, S. (2010). "An Investigation of the
    Efficiency of the Betting Market for NBA Games"
  - Snowberg, E., & Wolfers, J. (2010). "Explaining the Favorite-
    Longshot Bias"
  - Dixon, M.J., & Coles, S.G. (1997). "Modelling Association
    Football Scores and Inefficiencies in the Football Betting Market"
  - Betfair Developer Program: https://docs.developer.betfair.com/
  - NBA API: https://github.com/swar/nba_api
"""


# ============================================================
# FIM DO DOCUMENTO
# ============================================================
#
# Este plano unificado e a referencia definitiva para o sistema.
# Qualquer alteracao deve ser registada neste documento.
#
# PROXIMO PASSO: Iniciar Fase 1 — Infraestrutura e Dados.
#
# ID: VBQ-UNIFIED v4.0.0-FINAL
# DATA: 2026-05-13
# ESTADO: PRONTO PARA EXECUCAO
# ============================================================