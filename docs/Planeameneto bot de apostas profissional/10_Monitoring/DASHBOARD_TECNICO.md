# DASHBOARD_TECNICO — Grafana

**ID:** `MON-001` | **Fase:** #phase/1 | **Owner:** MLOps Engineer | **Status:** #status/pending

---

## 1. STACK

| Componente | Versao | Porta |
|------------|--------|-------|
| Prometheus | Latest | 9090 |
| Grafana | Latest | 3000 |
| Node Exporter | Latest | 9100 |

---

## 2. DASHBOARD: INFRAESTRUTURA

### 2.1 Queries Prometheus

| Painel | Query | Alerta |
|--------|-------|--------|
| CPU Usage | `100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)` | > 80% por 5 min |
| Memory Usage | `100 * (1 - ((node_memory_MemAvailable_bytes) / (node_memory_MemTotal_bytes)))` | > 85% por 5 min |
| Disk Usage | `100 - ((node_filesystem_avail_bytes{mountpoint="/"} * 100) / node_filesystem_size_bytes{mountpoint="/"})` | > 80% |
| Network I/O | `rate(node_network_receive_bytes_total[5m])` | > 100 MB/s |
| Uptime | `node_time_seconds - node_boot_time_seconds` | < 95% (24h) |
| Load Average | `node_load1 / count(node_cpu_seconds_total) by (instance)` | > 2.0 |

**Explicação:** Load average > 2.0 em VPS com 2 vCPUs significa que há mais processos prontos para executar que CPUs disponíveis. Isto causa latência em todo o pipeline, desde ingestão de dados até geração de sinais.

---

## 3. DASHBOARD: APLICACAO (FastAPI)

### 3.1 Métricas de API

| Painel | Query | Threshold |
|--------|-------|-----------|
| Request Rate | `rate(fastapi_requests_total[5m])` | > 100 req/min |
| Latência p50 | `histogram_quantile(0.50, rate(fastapi_request_duration_seconds_bucket[5m]))` | < 200ms |
| Latência p99 | `histogram_quantile(0.99, rate(fastapi_request_duration_seconds_bucket[5m]))` | < 2000ms |
| Error Rate 5xx | `rate(fastapi_requests_total{status_code=~"5.."}[5m])` | < 1% |
| Error Rate 4xx | `rate(fastapi_requests_total{status_code=~"4.."}[5m])` | < 5% |
| Active Connections | `fastapi_active_connections` | < 50 |

**Explicação:** Latência p99 < 2s é aceitável para um sistema de apostas pré-jogo. Se p99 > 5s, o operador pode perder o timing ideal para execução. Latência p50 deve ser < 200ms para operações de leitura (consultar sinais, métricas).

### 3.2 Métricas de Modelo

| Painel | Query | Threshold |
|--------|-------|-----------|
| Predições/hora | `rate(model_predictions_total[1h])` | > 0 (se há jogos) |
| Tempo de inferência | `histogram_quantile(0.99, rate(model_inference_duration_seconds_bucket[5m]))` | < 500ms |
| Cache hit rate | `redis_keyspace_hits / (redis_keyspace_hits + redis_keyspace_misses)` | > 90% |

---

## 4. DASHBOARD: BASE DE DADOS

### 4.1 PostgreSQL

| Painel | Query | Alerta |
|--------|-------|--------|
| Conexões ativas | `pg_stat_activity_count{state="active"}` | > 80% do pool |
| Conexões idle | `pg_stat_activity_count{state="idle"}` | > 20% do pool |
| Query time avg | `rate(pg_stat_statements_total_time[5m])` | > 100ms |
| Deadlocks | `rate(pg_stat_database_deadlocks[5m])` | > 0 |
| Cache hit ratio | `pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read)` | < 99% |
| Transaction rate | `rate(pg_stat_database_xact_commit[5m])` | — |
| Replication lag | `pg_replication_lag_seconds` (se replica) | > 1s |

**Explicação:** Cache hit ratio < 99% em PostgreSQL indica que o shared_buffers está mal dimensionado ou queries estão a fazer sequential scans em tabelas grandes. Para o nosso volume (~1000 jogos/época), deveria ser > 99.5%.

### 4.2 Redis

| Painel | Query | Alerta |
|--------|-------|--------|
| Memory usage | `redis_memory_used_bytes / redis_memory_max_bytes` | > 80% |
| Connected clients | `redis_connected_clients` | > 50 |
| Ops/sec | `rate(redis_commands_processed_total[5m])` | > 10.000 |
| Keyspace hits | `redis_keyspace_hits / (redis_keyspace_hits + redis_keyspace_misses)` | < 95% |
| Evicted keys | `rate(redis_evicted_keys_total[5m])` | > 0 |

---

## 5. DASHBOARD: MODELO ML (MLflow)

| Painel | Fonte | Threshold |
|--------|-------|-----------|
| ROC-AUC (último CV) | MLflow API | > 0.55 |
| Brier Score | MLflow API | < 0.25 |
| ECE | MLflow API | < 0.05 |
| Nº de features | MLflow API | = 80 |
| Tempo de treino | MLflow API | < 300s |
| Versão do modelo | MLflow API | atual |

**Explicação:** O dashboard de ML deve ser o primeiro a ser verificado todas as manhãs. Se ROC-AUC caiu abaixo de 0.55, o modelo degradou e não deve gerar sinais até ser re-treinado. Brier score < 0.25 indica que as probabilidades estão bem calibradas.

---

## 6. DASHBOARD: PIPELINE DE DADOS

| Painel | Query | Alerta |
|--------|-------|--------|
| Odds ingested/min | `rate(odds_ingested_total[5m])` | = 0 em dias de jogo |
| Pipeline latency | `histogram_quantile(0.99, rate(pipeline_duration_seconds_bucket[5m]))` | > 300s |
| Failed validations | `rate(validation_failures_total[5m])` | > 0 |
| Last ingestion | `odds_last_ingestion_timestamp` | > 45 min |
| Games missing data | `games_without_data_total` | > 0 |

---

## 7. CONFIGURACAO PROMETHEUS

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'fastapi'
    static_configs:
      - targets: ['api:8000']
    metrics_path: /metrics

  - job_name: 'mlflow'
    static_configs:
      - targets: ['mlflow:5000']
```

---

## 8. ALERTAS (Alertmanager)

```yaml
# alertmanager.yml
groups:
  - name: betting_alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU usage above 80%"

      - alert: PipelineStalled
        expr: odds_last_ingestion_timestamp < (time() - 2700)  # 45 min
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Pipeline stalled - no odds ingested for 45 minutes"

      - alert: ModelDegraded
        expr: model_roc_auc < 0.55
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Model ROC-AUC dropped below 0.55"

      - alert: HighErrorRate
        expr: rate(fastapi_requests_total{status_code=~"5.."}[5m]) / rate(fastapi_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "API error rate above 5%"
```

---

## 9. BACKLOG

- [x] Queries Prometheus para infraestrutura
- [x] Queries para aplicação FastAPI
- [x] Queries para PostgreSQL e Redis
- [x] Dashboard MLflow
- [x] Configuração Prometheus
- [x] Regras de alerta Alertmanager
- [ ] Criar dashboards Grafana com estas queries
- [ ] Configurar notificações Telegram para alertas críticos
- [ ] Dashboard de latência de execução (paper vs real)

---

## 10. LINKS CRUZADOS

- [[10_Monitoring/INDEX]] ← Secção mãe
- [[10_Monitoring/DASHBOARD_NEGOCIO]] → Dashboard de negócio (PnL, ROI)
- [[33_Alerting/INDEX]] → Alertas e escalada
- [[12_DevOps/CI_CD_SETUP]] → CI/CD e deploy de dashboards
