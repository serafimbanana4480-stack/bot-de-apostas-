# FASE 1 — CHECKLIST DE IMPLEMENTAÇÃO

**ID:** `IMPL-F1` | **Duração Estimada:** 4 semanas | **Owner:** Developer | **Status:** #status/pending

---

## 1. VISÃO GERAL

Fase 1 estabelece as fundações: infraestrutura containerizada, ingestão de dados NBA históricos, pipeline de feature engineering com 80 features, e validação rigorosa com Purged Walk-Forward CV.

**Pré-requisitos:**
- Python 3.11+ instalado
- Docker + Docker Compose v2
- Git configurado
- Conta Betfair (demo OK para testes)
- Bot Telegram criado (@BotFather)

---

## 2. ORDEM DE IMPLEMENTAÇÃO (Dependências)

```
Semana 1: Infra + Ingestão
  ├─ [1.1] PostgreSQL + Schema Bronze/Silver/Gold
  ├─ [1.2] Redis + Docker Compose
  ├─ [1.3] Ingestão NBA (5 épocas históricas)
  └─ [1.4] Validação de dados

Semana 2: Features + CV
  ├─ [2.1] Pipeline de features (80 total)
  ├─ [2.2] Testes ADF/KPSS
  ├─ [2.3] Purged Walk-Forward CV
  └─ [2.4] Métricas de baseline

Semana 3: Modelo Baseline
  ├─ [3.1] XGBoost baseline
  ├─ [3.2] Calibração isotónica
  ├─ [3.3] Meta-modelo
  └─ [3.4] Registo em MLflow

Semana 4: API + Bot
  ├─ [4.1] FastAPI + endpoints
  ├─ [4.2] Telegram Bot
  ├─ [4.3] Grafana dashboards
  └─ [4.4] Testes E2E
```

---

## 3. CHECKLIST DETALHADO

### Semana 1 — Infraestrutura e Dados

#### [1.1] PostgreSQL + Schema
- [ ] Criar `docker-compose.yml` com postgres:15-alpine, redis:7.2, api, mlflow, grafana, prometheus
- [ ] Implementar schema Bronze: `bronze.raw_games`, `bronze.raw_odds`, `bronze.raw_players`
- [ ] Implementar schema Silver: `silver.games_clean`, `silver.odds_clean`, `silver.player_stats`
- [ ] Implementar schema Gold: `gold.features`, `gold.predictions`, `gold.signals`
- [ ] Implementar schema Meta: `meta.model_runs`, `meta.subscriber_limits`, `meta.circuit_breaker_log`
- [ ] Configurar Alembic para migrations
- [ ] **Critério:** `docker compose up -d` funciona, psql conecta, schema vazio existe

#### [1.2] Redis
- [ ] Configurar Redis com password
- [ ] Implementar wrapper Python para cache
- [ ] Testar: set/get, TTL, expiração
- [ ] **Critério:** `redis-cli ping` retorna PONG

#### [1.3] Ingestão NBA
- [ ] Implementar `nba_api` wrapper com rate limiting
- [ ] Ingerir 5 épocas: 2019-20 a 2023-24
- [ ] Ingerir dados: games, box scores, play-by-play, player stats
- [ ] Implementar deduplicação (game_id como chave)
- [ ] Validar: contagem de jogos por época (1230 regulares + playoffs)
- [ ] **Critério:** `SELECT COUNT(*) FROM bronze.raw_games` >= 6000

#### [1.4] Validação de Dados
- [ ] Implementar checks: NULLs, ranges, duplicados
- [ ] Documentar qualidade dos dados (% missing por coluna)
- [ ] Criar `scripts/verify_data_quality.py`
- [ ] **Critério:** < 5% missing em colunas críticas, 0 duplicados em game_id

### Semana 2 — Feature Engineering

#### [2.1] Pipeline de Features
- [ ] Módulo A — Forma Recente (15 features): win rate ponderado, Four Factors decay, Net Rating
- [ ] Módulo B — Mercado (12 features): odds implícitas, overround, movimento de odds
- [ ] Módulo C — Contexto (18 features): back-to-back, distância viagem, rest days
- [ ] Módulo D — Jogadores (20 features): lesões, minutos projetados, matchup
- [ ] Módulo E — Interações (15 features): forma vs contexto, momentum × mercado
- [ ] **Critério:** `gold.features` tem 80 colunas + game_id + target

#### [2.2] Testes de Estacionariedade
- [ ] Rodar ADF test em top 20 features
- [ ] Rodar KPSS test em top 20 features
- [ ] Documentar quais são estacionárias vs não-estacionárias
- [ ] **Critério:** > 70% das features passam ADF (p < 0.05) ou são justificáveis

#### [2.3] Purged Walk-Forward CV
- [ ] Implementar função `purged_cv_splits(dates, n_folds=12, embargo_days=2)`
- [ ] Validar: nenhum jogo de teste ocorre < 2 dias após último jogo de treino
- [ ] Validar: folds são sequenciais temporais (não randomizados)
- [ ] **Critério:** Script de teste demonstra 0 leakage em dataset sintético

#### [2.4] Métricas de Baseline
- [ ] Calcular Brier Score de baseline (prob implícita como preditor)
- [ ] Calcular ROC-AUC de baseline
- [ ] Documentar: baseline é o mercado (prob implícita)
- [ ] **Critério:** Baseline Brier < 0.25 (mercado NBA é relativamente eficiente)

### Semana 3 — Modelo ML

#### [3.1] XGBoost Baseline
- [ ] Treinar XGBoost com Purged CV
- [ ] Hiperparâmetros: max_depth=6, learning_rate=0.05, n_estimators=500, subsample=0.8
- [ ] Métricas: ROC-AUC, Brier, Log-loss por fold
- [ ] **Critério:** ROC-AUC > 0.55 (melhor que baseline de 0.50)

#### [3.2] Calibração Isotónica
- [ ] Implementar `IsotonicRegression` por regime (favorito/equilibrado/underdog)
- [ ] Calcular ECE antes e depois da calibração
- [ ] **Critério:** ECE < 0.05 após calibração

#### [3.3] Meta-Modelo
- [ ] Treinar meta-XGBoost com target = CLV > 0
- [ ] Threshold: prob_meta > 0.60 para aprovar aposta
- [ ] **Critério:** Meta-modelo reduz falsos positivos em > 20% vs modelo primário

#### [3.4] MLflow Tracking
- [ ] Configurar MLflow server (porta 5000)
- [ ] Logar hiperparâmetros, métricas, artefatos
- [ ] Guardar modelo calibrado com `mlflow.xgboost.log_model`
- [ ] **Critério:** Modelo visível em MLflow UI com todas as métricas

### Semana 4 — API, Bot e Monitorização

#### [4.1] FastAPI
- [ ] `GET /health` — healthcheck
- [ ] `GET /signals` — lista sinais ativos (autenticado)
- [ ] `POST /predict` — predição para game_id (autenticado)
- [ ] `GET /metrics` — métricas Prometheus
- [ ] Implementar rate limiting (100 req/min)
- [ ] **Critério:** Todos os endpoints respondem, testes passam

#### [4.2] Telegram Bot
- [ ] `/start` — boas-vindas
- [ ] `/signals` — últimos sinais gerados
- [ ] `/status` — estado do sistema
- [ ] Formatação: game, edge%, odd recomendada, stake (unidades)
- [ ] **Critério:** Bot envia mensagem de teste para canal

#### [4.3] Grafana
- [ ] Dashboard: Métricas de modelo (ROC-AUC, Brier, ECE)
- [ ] Dashboard: Métricas de negócio (PnL, CLV, drawdown)
- [ ] Dashboard: Métricas técnicas (CPU, RAM, disk, API latency)
- [ ] **Critério:** Dashboards carregam dados reais do Prometheus/PostgreSQL

#### [4.4] Testes E2E
- [ ] Teste: ingestão → features → modelo → sinal → Telegram
- [ ] Teste: circuit breaker ativa e para o sistema
- [ ] Teste: backup e restore da BD
- [ ] **Critério:** Pipeline completo corre sem erros

---

## 4. CRITÉRIOS DE PASSAGEM DE FASE

Para avançar para Fase 2, TODOS os seguintes devem ser verdade:

1. [ ] Dados históricos: 5 épocas NBA completas na BD
2. [ ] Features: 80 features calculáveis em < 5s por jogo
3. [ ] Modelo: ROC-AUC > 0.55 em Purged CV
4. [ ] Calibração: ECE < 0.05
5. [ ] API: Endpoints funcionais com testes
6. [ ] Bot: Envia sinais formatados para Telegram
7. [ ] Dashboard: Grafana com métricas reais
8. [ ] SOPs: Rotinas de abertura/fecho documentadas
9. [ ] Backup: Restore testado e funcional
10. [ ] Documentação: README atualizado com instruções de setup

---

## 5. RISCOS E MITIGAÇÕES

| Risco | Mitigação |
|-------|-----------|
| NBA API indisponível | Cache de dados + Basketball-Reference fallback |
| Dados incompletos | Validação + imputação com média por equipa |
| Modelo overfitting | Purged CV obrigatório + regularização |
| Latência alta | Otimizar queries + índices PostgreSQL |
| Docker não funciona em Windows | Documentar WSL2 setup |

---

## 6. RECURSOS NECESSÁRIOS (TUDO GRATUITO)

| Recurso | Custo | Quando | Alternativa Gratuita |
|---------|-------|--------|---------------------|
| VPS | **0€** | Semana 4 | Oracle Cloud Free Tier (4 CPUs, 24GB RAM, 200GB) |
| Domínio | **0€** | Semana 4 | DuckDNS (subdomínio gratuito) |
| PostgreSQL | **0€** | Semana 1 | Self-hosted no VPS gratuito |
| Redis | **0€** | Semana 1 | Self-hosted no VPS gratuito |
| MLflow | **0€** | Semana 3 | Self-hosted (sqlite backend) |
| Grafana + Prometheus | **0€** | Semana 4 | OSS self-hosted |
| Dados NBA API | **0€** | Desde o início | NBA API oficial (free) |
| Betfair API | **0€** | Semana 3+ | Demo API (gratuita) |
| Telegram Bot | **0€** | Semana 4 | Bot API gratuita |
| GitHub Actions | **0€** | CI/CD | Free tier (2000 min/mês) |

### Stack 100% Gratuita Fase 1

```
Oracle Cloud Free Tier (VPS)
├── Ubuntu 22.04 LTS
├── Docker + Docker Compose
├── PostgreSQL 15 (container)
├── Redis 7 (container)
├── MLflow (container, sqlite)
├── Grafana OSS (container)
├── Prometheus (container)
└── FastAPI App (container)
```

**Nota:** Oracle Cloud Free Tier não requer cartão de crédito. Limites: 4 ARM CPUs, 24GB RAM, 200GB storage - suficiente para Fase 1-4.

---

## 7. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[00_Master_Index/MASTER_PLAN_UNIFICADO]] → Arquitetura completa
- [[00_Master_Index/GETTING_STARTED]] → Setup local detalhado
- [[06_Backtesting/INDEX]] → Metodologia de validação
- [[05_Machine_Learning/INDEX]] → ML e modelos
