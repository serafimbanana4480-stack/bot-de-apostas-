# OBSERVABILIDADE DE PIPELINES DE DADOS

**ID:** `SEC-04-04` | **Fase:** #phase/1 | **Owner:** Data Engineer | **Status:** #status/pending  
**Última Atualização:** `2026-05-13`

---

## 1. PILARES DA OBSERVABILIDADE

| Pilar | Responde a | Stack |
|-------|-----------|-------|
| **Logs** | O que aconteceu? | Python `logging` + JSON estruturado → ficheiro + stdout |
| **Métricas** | Qual é o estado atual? | Prometheus + Grafana |
| **Tracing** | Qual foi o caminho da execução? | OpenTelemetry (Fase 6+) |
| **Alertas** | O que requer ação imediata? | Alertmanager + Telegram |

**MVP (Fases 1-3):** Logs JSON + Prometheus básico + Alertas Telegram. OpenTelemetry para fases posteriores.

---

## 2. ARQUITETURA

```
Pipelines de dados (Python workers)
        │
        ├─► Logs JSON (stdout + ficheiro rotativo)
        │       └── Centralizado no servidor VPS
        │
        ├─► Métricas Prometheus
        │       └── Scraping a cada 15s pelo Prometheus server
        │       └── Visualização: Grafana dashboards
        │
        └─► Alertas
                └── Prometheus Alertmanager → Telegram Bot
```

---

## 3. ESTRUTURA DE LOGS

### 3.1 Formato JSON Obrigatório
```python
import logging
import json
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "pipeline": getattr(record, "pipeline", None),
            "step": getattr(record, "step", None),
            "records_processed": getattr(record, "records_processed", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "error": str(record.exc_info[1]) if record.exc_info else None,
        }
        return json.dumps({k: v for k, v in log_entry.items() if v is not None})
```

### 3.2 Categorias de Log
| Categoria | Logger | Nível | Exemplo |
|-----------|--------|-------|---------|
| Negócio | `pipeline.business` | INFO | "Ingestão concluída: 45 odds para 3 jogos" |
| Performance | `pipeline.perf` | DEBUG | "Transform step: 234ms, 1250 records" |
| Qualidade | `pipeline.quality` | WARNING | "5 odds fora do range válido descartadas" |
| Sistema | `pipeline.system` | ERROR | "PostgreSQL connection timeout após 3 retries" |

---

## 4. MÉTRICAS PROMETHEUS

### 4.1 Métricas de Ingestão
```python
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Ingestão
records_ingested = Counter(
    'pipeline_records_ingested_total',
    'Total records ingested',
    ['pipeline', 'source', 'layer']
)

ingestion_duration = Histogram(
    'pipeline_ingestion_duration_seconds',
    'Duration of ingestion steps',
    ['pipeline', 'step'],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0]
)

last_successful_run = Gauge(
    'pipeline_last_successful_run_timestamp',
    'Unix timestamp of last successful pipeline run',
    ['pipeline']
)

pipeline_errors_total = Counter(
    'pipeline_errors_total',
    'Total pipeline errors',
    ['pipeline', 'step', 'error_type']
)
```

### 4.2 Métricas de Qualidade
```python
data_quality_score = Gauge(
    'pipeline_data_quality_score',
    'Percentage of records passing validation (0-1)',
    ['pipeline', 'layer']
)

validation_failures = Counter(
    'pipeline_validation_failures_total',
    'Count of validation failures',
    ['pipeline', 'rule', 'severity']
)
```

### 4.3 Métricas de Base de Dados
```python
db_query_duration = Histogram(
    'pipeline_db_query_duration_seconds',
    'PostgreSQL query duration',
    ['query_type']
)

db_active_connections = Gauge(
    'pipeline_db_active_connections',
    'Current active PostgreSQL connections'
)
```

---

## 5. REGRAS DE ALERTA

### 5.1 Alertas Críticos (Telegram imediato)
```yaml
# prometheus/alerts.yml
groups:
  - name: pipeline_critical
    rules:
      - alert: PipelineNotRunning
        expr: time() - pipeline_last_successful_run_timestamp{pipeline="odds_ingestion"} > 3600
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pipeline de ingestão de odds parado há > 1 hora"

      - alert: HighErrorRate
        expr: rate(pipeline_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Taxa de erros no pipeline > 10%"

      - alert: DataQualityDegraded
        expr: pipeline_data_quality_score < 0.90
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Qualidade de dados abaixo de 90%"
```

### 5.2 Alertas Warning (Telegram + log)
```yaml
      - alert: SlowIngestion
        expr: pipeline_ingestion_duration_seconds{quantile="0.99"} > 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Ingestão lenta (p99 > 30s)"

      - alert: LowDataVolume
        expr: rate(pipeline_records_ingested_total[1h]) < 10
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Volume de dados baixo em dia de jogo"
```

---

## 6. DASHBOARDS GRAFANA

### 6.1 Dashboard Principal — Pipeline Health
| Painel | Query | Tipo |
|--------|-------|------|
| Última execução | `time() - pipeline_last_successful_run_timestamp` | Stat |
| Records ingeridos (24h) | `increase(pipeline_records_ingested_total[24h])` | Stat |
| Taxa de erros | `rate(pipeline_errors_total[5m])` | Time series |
| Qualidade de dados | `pipeline_data_quality_score` | Gauge |
| Duração p50/p99 | `histogram_quantile(0.99, ...)` | Time series |

### 6.2 Dashboard Ingestão de Odds
| Painel | Query |
|--------|-------|
| Odds por hora | `increase(pipeline_records_ingested_total{layer="bronze"}[1h])` |
| Falhas de validação por regra | `pipeline_validation_failures_total` |
| Overround médio | Query SQL custom via PostgreSQL datasource |

---

## 7. INTEGRAÇÃO COM PIPELINE

```python
import time
from contextlib import contextmanager

@contextmanager
def pipeline_step(pipeline_name: str, step_name: str):
    """Context manager para instrumentar automaticamente cada step do pipeline."""
    start = time.time()
    try:
        yield
        duration = time.time() - start
        ingestion_duration.labels(
            pipeline=pipeline_name,
            step=step_name
        ).observe(duration)
        last_successful_run.labels(pipeline=pipeline_name).set(time.time())
        logger.info(
            f"Step concluído: {step_name}",
            extra={"pipeline": pipeline_name, "step": step_name, "duration_ms": int(duration * 1000)}
        )
    except Exception as e:
        pipeline_errors_total.labels(
            pipeline=pipeline_name,
            step=step_name,
            error_type=type(e).__name__
        ).inc()
        logger.error(
            f"Step falhou: {step_name} — {e}",
            extra={"pipeline": pipeline_name, "step": step_name},
            exc_info=True
        )
        raise


# Uso:
with pipeline_step("odds_ingestion", "fetch_betfair"):
    odds = betfair_client.list_market_book(market_ids)

with pipeline_step("odds_ingestion", "validate_bronze"):
    results = ge_checkpoint.run()
```

---

## 8. BACKLOG

- [ ] Configurar JsonFormatter em todos os workers (Fase 1, Semana 1)
- [ ] Instalar Prometheus + exportar métricas (Fase 1, Semana 2)
- [ ] Configurar Grafana com dashboards base (Fase 1, Semana 2)
- [ ] Criar regras de alerta Alertmanager + Telegram (Fase 1, Semana 2)
- [ ] Integrar `pipeline_step` context manager em todos os pipelines
- [ ] Implementar centralização de logs (Fase 6: ELK stack ou similar)

---

## 9. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]] ← Secção mãe
- [[10_Monitoring/INDEX]] → Prometheus/Grafana setup completo
- [[33_Alerting/INDEX]] → Regras de alertas e escalada
- [[12_DevOps/INDEX]] → Docker Compose com stack de observabilidade
