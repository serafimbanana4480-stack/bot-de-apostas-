# MONITORIZACAO_INFRA — Monitorização de Infraestrutura (Gratuita)

**ID:** `INF-008` | **Versão:** v1.0 | **Data:** 2026-05-17  
**Status:** #status/pending | **Owner:** DevOps Engineer  
**Custo:** **0€** (Prometheus + Grafana OSS)

---

## 1. OVERVIEW

Monitorização completa da infraestrutura usando stack open source gratuita: Prometheus + Grafana.

---

## 2. STACK DE MONITORIZAÇÃO

```
┌─────────────────────────────────────────────────────────────┐
│                    STACK DE MONITORIZAÇÃO                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 GRAFANA (UI)                                             │
│  ├── Dashboards de infraestrutura                          │
│  ├── Dashboards de aplicação                                 │
│  └── Alertas visuais                                         │
│                                                              │
│  📈 PROMETHEUS (TSDB)                                        │
│  ├── Métricas de sistema                                     │
│  ├── Métricas de Docker                                      │
│  └── Métricas de aplicação                                   │
│                                                              │
│  🔍 EXPORTERS                                                │
│  ├── Node Exporter (métricas do host)                       │
│  ├── cAdvisor (métricas de containers)                      │
│  └── Postgres Exporter (métricas de BD)                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. PROMETHEUS

### 3.1 Instalação (Docker)

```yaml
# docker-compose.yml (adicionar)
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: vb-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    ports:
      - "9090:9090"
    volumes:
      - prometheus_data:/prometheus
      - ./configs/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - vb-network
```

### 3.2 Configuração (prometheus.yml)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # API da aplicação
  - job_name: 'api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: /metrics

  # Node Exporter (host)
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  # cAdvisor (Docker containers)
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  # PostgreSQL
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### 3.3 Custo Prometheus

| Recurso | Uso | Custo |
|---------|-----|-------|
| CPU | ~0.1 cores | **0€** |
| RAM | ~500MB | **0€** |
| Storage | ~5GB (30d) | **0€** |
| **Total** | | **0€** |

---

## 4. GRAFANA

### 4.1 Instalação (Docker)

```yaml
# docker-compose.yml (adicionar)
  grafana:
    image: grafana/grafana:10.2.2
    container_name: vb-grafana
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_USER}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./configs/grafana/provisioning:/etc/grafana/provisioning
      - ./configs/grafana/dashboards:/var/lib/grafana/dashboards
    networks:
      - vb-network
```

### 4.2 Data Source Configuration

```yaml
# configs/grafana/provisioning/datasources/datasources.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

### 4.3 Dashboards Principais

| Dashboard | ID | Uso |
|-----------|-----|-----|
| Node Exporter Full | 1860 | Métricas do host (CPU, RAM, Disk) |
| Docker & Host Monitoring | 179 | Métricas de containers |
| PostgreSQL Database | 9628 | Métricas de BD |
| API Performance | Custom | Latência, throughput, erros |

### 4.4 Custo Grafana

| Recurso | Uso | Custo |
|---------|-----|-------|
| CPU | ~0.05 cores | **0€** |
| RAM | ~300MB | **0€** |
| **Total** | | **0€** |

---

## 5. ALERTAS

### 5.1 Alertmanager (Opcional)

Para notificações via Telegram:

```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alertmanager@example.com'

route:
  receiver: 'telegram'

receivers:
  - name: 'telegram'
    telegram_configs:
      - bot_token: '${TELEGRAM_BOT_TOKEN}'
        chat_id: '${TELEGRAM_CHAT_ID}'
        message: '🔥 {{ .GroupLabels.alertname }}: {{ .Annotations.summary }}'
```

### 5.2 Alert Rules

```yaml
# prometheus/alert_rules.yml
groups:
  - name: infrastructure
    rules:
      # CPU > 80%
      - alert: HighCPUUsage
        expr: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU usage > 80%"
          
      # RAM > 90%
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Memory usage > 90%"
          
      # Disk > 85%
      - alert: LowDiskSpace
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 15
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disk space < 15%"
          
      # API Down
      - alert: APIDown
        expr: up{job="api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API is down"
```

---

## 6. MÉTRICAS CHAVE

### 6.1 Infraestrutura (Node Exporter)

| Métrica | Query | Threshold |
|---------|-------|-----------|
| CPU Usage | `100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)` | > 80% |
| Memory Usage | `(node_memory_MemTotal - node_memory_MemAvailable) / node_memory_MemTotal * 100` | > 90% |
| Disk Usage | `(node_filesystem_size - node_filesystem_avail) / node_filesys_filesystem_size * 100` | > 85% |
| Load Average | `node_load1` | > 4 (para 4 cores) |

### 6.2 Aplicação

| Métrica | Query | Threshold |
|---------|-------|-----------|
| Request Rate | `rate(http_requests_total[5m])` | Baseline |
| Error Rate | `rate(http_requests_total{status=~"5.."}[5m])` | > 1% |
| Latency P95 | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` | > 500ms |
| Active Connections | `process_open_fds{job="api"}` | > 1000 |

### 6.3 Banco de Dados

| Métrica | Query | Threshold |
|---------|-------|-----------|
| Connections | `pg_stat_activity_count` | > 80 |
| Query Rate | `rate(pg_stat_database_xact_commit[1m])` | Baseline |
| Cache Hit Ratio | `pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read)` | < 95% |

---

## 7. CUSTO TOTAL

| Componente | CPU | RAM | Storage | Custo |
|------------|-----|-----|---------|-------|
| Prometheus | 0.1 | 500MB | 5GB | **0€** |
| Grafana | 0.05 | 300MB | 1GB | **0€** |
| Node Exporter | 0.01 | 20MB | - | **0€** |
| cAdvisor | 0.02 | 100MB | - | **0€** |
| **TOTAL** | **0.18** | **0.9GB** | **6GB** | **0€** |

---

## 8. CHECKLIST

- [ ] Prometheus configurado e rodando
- [ ] Grafana configurado e acessível
- [ ] Node Exporter instalado no host
- [ ] cAdvisor configurado para Docker
- [ ] Dashboards importados
- [ ] Alert rules configurados
- [ ] Alertmanager configurado (opcional)
- [ ] Testes de alertas realizados
- [ ] Documentação de métricas criada

---

## 9. ACESSO

| Serviço | URL | Login |
|---------|-----|-------|
| Prometheus | http://localhost:9090 | N/A |
| Grafana | http://localhost:3000 | admin/admin (mudar) |

---

## 10. LINKS

- [[VPS_CONFIGURACAO]] → Configuração de VPS
- [[10_Infrastructure/INDEX]] ← Secção mãe
- [[20_Dashboarding/INDEX]] → Dashboards de negócio

---

**Monitorização 100% Gratuita — Visibilidade Total**
