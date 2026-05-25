# Grafana Dashboards Setup

**ID:** `MON-001` | **Fase:** #phase/1 | **Owner:** DevOps Lead | **Status:** #status/active

---

## 1. CONFIGURAÇÃO DO PROMETHEUS

### 1.1 Prometheus Config

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # API Metrics
  - job_name: 'value-betting-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  # PostgreSQL Exporter
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis Exporter
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Node Exporter (System Metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Prefect
  - job_name: 'prefect'
    static_configs:
      - targets: ['prefect-api:4200']
```

---

## 2. DASHBOARD PRINCIPAL (Business Overview)

### 2.1 JSON Configuration

```json
{
  "dashboard": {
    "title": "Value Betting System - Business Overview",
    "uid": "vb-business-overview",
    "panels": [
      {
        "id": 1,
        "title": "Total PnL (€)",
        "type": "stat",
        "targets": [
          {
            "expr": "vb_pnl_total_eur",
            "legendFormat": "PnL"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "red", "value": null},
                {"color": "yellow", "value": 0},
                {"color": "green", "value": 1000}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "Average CLV (%)",
        "type": "stat",
        "targets": [
          {
            "expr": "vb_clv_average_percent * 100",
            "legendFormat": "CLV"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "red", "value": null},
                {"color": "yellow", "value": 0},
                {"color": "green", "value": 2}
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "title": "Signals Generated (Last 24h)",
        "type": "stat",
        "targets": [
          {
            "expr": "increase(vb_signals_generated_total[24h])",
            "legendFormat": "Signals"
          }
        ]
      },
      {
        "id": 4,
        "title": "Bets Placed (Last 24h)",
        "type": "stat",
        "targets": [
          {
            "expr": "increase(vb_bets_placed_total[24h])",
            "legendFormat": "Bets"
          }
        ]
      },
      {
        "id": 5,
        "title": "PnL Over Time",
        "type": "timeseries",
        "targets": [
          {
            "expr": "vb_pnl_total_eur",
            "legendFormat": "PnL"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "currencyEUR"
          }
        }
      },
      {
        "id": 6,
        "title": "CLV Trend",
        "type": "timeseries",
        "targets": [
          {
            "expr": "vb_clv_average_percent * 100",
            "legendFormat": "CLV %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent"
          }
        }
      },
      {
        "id": 7,
        "title": "Signals by Status",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (status) (vb_signals_generated_total)",
            "legendFormat": "{{status}}"
          }
        ]
      }
    ]
  }
}
```

### 2.2 Import Dashboard

```bash
# Via Grafana UI
1. Login to Grafana (http://localhost:3000)
2. Navigate to Dashboards → Import
3. Upload JSON file or paste JSON
4. Select Prometheus as data source
5. Click Import

# Via API
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana/dashboards/business-overview.json \
  -u admin:admin
```

---

## 3. DASHBOARD TÉCNICO (System Health)

### 3.1 Panels Configuração

```json
{
  "dashboard": {
    "title": "Value Betting System - System Health",
    "uid": "vb-system-health",
    "panels": [
      {
        "id": 1,
        "title": "API Response Time (p95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, vb_api_request_duration_seconds)",
            "legendFormat": "p95"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s"
          }
        }
      },
      {
        "id": 2,
        "title": "API Requests Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(vb_api_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "id": 3,
        "title": "Database Connections",
        "type": "stat",
        "targets": [
          {
            "expr": "vb_db_connections_active",
            "legendFormat": "Connections"
          }
        ]
      },
      {
        "id": 4,
        "title": "Redis Operations Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(vb_redis_operations_total[1m])",
            "legendFormat": "{{operation}}"
          }
        ]
      },
      {
        "id": 5,
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "{{instance}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent"
          }
        }
      },
      {
        "id": 6,
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "legendFormat": "{{instance}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent"
          }
        }
      },
      {
        "id": 7,
        "title": "Disk Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(node_filesystem_size_bytes{fstype!=\"tmpfs\"} - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100",
            "legendFormat": "{{mountpoint}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent"
          }
        }
      }
    ]
  }
}
```

---

## 4. DASHBOARD DE RISK MANAGEMENT

### 4.1 Configuração

```json
{
  "dashboard": {
    "title": "Value Betting System - Risk Management",
    "uid": "vb-risk-management",
    "panels": [
      {
        "id": 1,
        "title": "Current Drawdown",
        "type": "gauge",
        "targets": [
          {
            "expr": "vb_drawdown_current_percent",
            "legendFormat": "Drawdown"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 50,
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "yellow", "value": 10},
                {"color": "red", "value": 20}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "Max Drawdown (All Time)",
        "type": "stat",
        "targets": [
          {
            "expr": "vb_drawdown_max_percent",
            "legendFormat": "Max DD"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent"
          }
        }
      },
      {
        "id": 3,
        "title": "Bankroll",
        "type": "stat",
        "targets": [
          {
            "expr": "vb_bankroll_current_eur",
            "legendFormat": "Bankroll"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "currencyEUR"
          }
        }
      },
      {
        "id": 4,
        "title": "Exposure by Market",
        "type": "bargauge",
        "targets": [
          {
            "expr": "vb_exposure_by_market",
            "legendFormat": "{{market}}"
          }
        ]
      },
      {
        "id": 5,
        "title": "Circuit Breaker Status",
        "type": "stat",
        "targets": [
          {
            "expr": "vb_circuit_breaker_active",
            "legendFormat": "Active"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {
                "type": "value",
                "options": {
                  "0": {"text": "Inactive", "color": "green"},
                  "1": {"text": "Active", "color": "red"}
                }
              }
            ]
          }
        }
      }
    ]
  }
}
```

---

## 5. CONFIGURAÇÃO DE ALERTAS

### 5.1 Alert Rules (Prometheus)

```yaml
# monitoring/prometheus/alerts.yml
groups:
  - name: business_alerts
    rules:
      - alert: HighDrawdown
        expr: vb_drawdown_current_percent > 20
        for: 5m
        labels:
          severity: critical
          team: operations
        annotations:
          summary: "Drawdown exceeded 20%"
          description: "Current drawdown: {{ $value }}%"

      - alert: NegativeCLV
        expr: vb_clv_average_percent < 0
        for: 1h
        labels:
          severity: warning
          team: quant
        annotations:
          summary: "CLV is negative"
          description: "Average CLV: {{ $value }}%"

      - alert: NoSignalsGenerated
        expr: increase(vb_signals_generated_total[1h]) == 0
        for: 2h
        labels:
          severity: warning
          team: operations
        annotations:
          summary: "No signals generated in 2 hours"
          description: "Check data feeds and model"

  - name: system_alerts
    rules:
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, vb_api_request_duration_seconds) > 5
        for: 5m
        labels:
          severity: warning
          team: devops
        annotations:
          summary: "API latency high"
          description: "p95 latency: {{ $value }}s"

      - alert: DatabaseConnectionPoolExhausted
        expr: vb_db_connections_active > 80
        for: 5m
        labels:
          severity: critical
          team: devops
        annotations:
          summary: "Database connections exhausted"
          description: "Active connections: {{ $value }}"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
          team: devops
        annotations:
          summary: "High memory usage"
          description: "Memory usage: {{ $value }}%"

      - alert: HighDiskUsage
        expr: (node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100 > 80
        for: 5m
        labels:
          severity: warning
          team: devops
        annotations:
          summary: "High disk usage"
          description: "Disk usage: {{ $value }}%"
```

### 5.2 Alertmanager Config

```yaml
# monitoring/alertmanager/alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'telegram'

receivers:
  - name: 'telegram'
    telegram_configs:
      - bot_token: 'YOUR_BOT_TOKEN'
        chat_id: 'YOUR_CHAT_ID'
        send_resolved: true
        parse_mode: 'HTML'

  - name: 'email'
    email_configs:
      - to: 'alerts@yourdomain.com'
        from: 'grafana@yourdomain.com'
        smarthost: 'smtp.sendgrid.net:587'
        auth_username: 'apikey'
        auth_password: 'YOUR_SENDGRID_API_KEY'
```

---

## 6. SETUP AUTOMATIZADO

### 6.1 Script de Configuração

```bash
#!/bin/bash
# monitoring/setup_monitoring.sh

echo "Setting up Grafana dashboards..."

# Import business dashboard
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @grafana/dashboards/business-overview.json \
  -u admin:$GRAFANA_PASSWORD

# Import system health dashboard
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @grafana/dashboards/system-health.json \
  -u admin:$GRAFANA_PASSWORD

# Import risk management dashboard
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @grafana/dashboards/risk-management.json \
  -u admin:$GRAFANA_PASSWORD

echo "Dashboards imported successfully"

# Reload Prometheus
docker exec vb-prometheus kill -HUP 1

echo "Monitoring setup complete"
```

---

## 7. VERIFICAÇÃO

### 7.1 Checklist

- [ ] Prometheus a recolher métricas
- [ ] Grafana dashboards importados
- [ ] Alertas configurados no Alertmanager
- [ ] Teste de alerta funcionando
- [ ] Telegram notifications funcionando

### 7.2 Testar Alertas

```bash
# Testar envio de alerta manual
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[
    {
      "labels": {
        "alertname": "TestAlert",
        "severity": "warning"
      },
      "annotations": {
        "description": "This is a test alert"
      }
    }
  ]'
```

---

## 8. LINKS CRUZADOS

- [[00_Master_Index/INTEGRATION_GUIDE]] ← Integração
- [[10_Monitoring/ARQUITETURA_MONITORIZACAO]] → Arquitetura detalhada
- [[33_Alerting/INDEX]] → Sistema de alertas
- [[08_Risk_Management/INDEX]] → Gestão de risco
