# 10_Monitoring — INDEX

**ID:** `SEC-10` | **Fase:** #phase/1-15 | **Owner:** MLOps Engineer + Operations Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Verificar continuamente a saúde do sistema: saúde técnica (infraestrutura, pipelines, APIs), saúde do modelo (CLV, calibração, drift), e saúde de negócio (PnL, churn, operacionalidade). **O que não é medido não é gerido.**

---

## 2. NOTAS FUNDAMENTAIS

- [[ARQUITETURA_MONITORIZACAO]] — Arquitetura completa: Prometheus, Grafana, coleta de métricas
- [[METRICAS_DETALHADAS]] — Definições formais de todas as métricas: financeiro, modelo, operacional, infraestrutura
- [[DASHBOARD_TECNICO]] — Prometheus + Grafana: uptime, latência, erros
- [[DASHBOARD_NEGOCIO]] — PnL, ROI, CLV, drawdown, turnover
- [[DASHBOARD_MODELO]] — Calibração, drift, feature importance, predições
- [[ALERTING_TELEGRAM]] — Thresholds, escalada, routing
- [[LOGGING_ESTRUTURADO]] — JSON logs, correlation IDs, audit trail
- [[HEALTH_CHECKS]] — Endpoints de health, readiness, liveness

---

## 3. PILARES DE MONITORIZAÇÃO

### Pilar 1: Infraestrutura (Técnico)
```
Métricas:
  ├── VPS CPU / Memory / Disk
  ├── PostgreSQL: connections, query time, replication lag
  ├── Redis: memory, hit rate, evictions
  ├── FastAPI: request rate, latency p50/p99, error rate
  └── Prefect: flow runs, failures, duration

Dashboards: Grafana default + custom
Alertas: CPU > 80%, Disk > 85%, API errors > 1%
```

### Pilar 2: Dados (Qualidade)
```
Métricas:
  ├── Última ingestão de dados NBA (horas desde update)
  ├── Jogos missing vs esperados
  ├── Features com valores nulos (%)
  ├── Odds desatualizadas (minutos desde último update)
  └── Schema violations (contagem)

Alertas: Dados > 2h sem update, nulls > 5%, odds > 10 min
```

### Pilar 3: Modelo (Performance)
```
Métricas:
  ├── CLV médio (rolling 50, 100, 500 apostas)
  ├── Brier Score (últimos 30 dias)
  ├── ECE por regime (semanal)
  ├── Feature drift (KS test, PSI)
  ├── Predição distribution (média, variância)
  └── Latência de inferência (ms)

Alertas: CLV 3d < 0%, ECE > 0.10, drift > 0.20
```

### Pilar 4: Negócio (Financeiro)
```
Métricas:
  ├── PnL diário/mensal/acumulado
  ├── ROI real vs simulado
  ├── Drawdown atual e máximo
  ├── Turnover e número de apostas
  ├── Sharpe Ratio (rolling 100 apostas)
  └── Stake média e distribuição

Alertas: Drawdown > 10%, ROI 7d < 0%, 5 perdas seguidas
```

### Pilar 5: Execução (Operacional)
```
Métricas:
  ├── Sinais gerados vs executados (% fill)
  ├── Slippage médio e máximo
  ├── Tempo médio sinal → execução
  ├── Erros de execução (contagem/tipo)
  └── Uptime do Telegram Bot

Alertas: Fill rate < 80%, slippage > 2%, exec errors > 3/dia
```

---

## 4. STACK DE MONITORIZAÇÃO

| Componente | Uso | Justificação |
|------------|-----|--------------|
| Prometheus | Métricas time-series | Standard de indústria, query language poderoso |
| Grafana | Visualização | Flexível, alertas integrados |
| Loki (opcional) | Logs | Se logs crescerem demais para ficheiros |
| Telegram Bot | Alertas móveis | Instantâneo, zero custo |
| JSON logs | Audit trail | Programático, parseável |

---

## 5. ALERTAS CRÍTICOS E ROTAS

| Alerta | Severidade | Rota | Tempo de Resposta |
|--------|------------|------|-------------------|
| Circuit breaker ativado | CRITICAL | Telegram + Email + SMS | Imediato |
| Drawdown > 15% | CRITICAL | Telegram + Email | Imediato |
| CLV 3d < 0% | HIGH | Telegram | < 1h |
| Feed de dados falha | HIGH | Telegram | < 15 min |
| API errors > 5% | HIGH | Telegram + Email | < 30 min |
| Disco > 90% | MEDIUM | Email | < 4h |
| ECE > 0.10 | MEDIUM | Telegram (resumo diário) | < 24h |

---

## 6. BACKLOG TÉCNICO

- [ ] Configurar Prometheus para scrape de métricas
- [ ] Criar dashboards Grafana para cada pilar
- [ ] Implementar logging estruturado JSON em todos os serviços
- [ ] Criar health check endpoints no FastAPI
- [ ] Implementar alertas Telegram para thresholds críticos
- [ ] Criar correlation ID para tracing de requests
- [ ] Documentar runbook de resposta a cada tipo de alerta

---

## 7. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[20_Dashboarding/INDEX]] → Dashboards detalhados
- [[33_Alerting/INDEX]] → Sistema de alertas e escalada
- [[11_MLOps/INDEX]] → Monitorização de modelos
- [[48_Data_Drift/INDEX]] → Deteção de drift
- [[29_Experiment_Tracking/INDEX]] → Métricas de experimentos
