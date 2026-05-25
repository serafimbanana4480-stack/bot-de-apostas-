# Monitoring Automation

**ID:** AUTO-006 | **Fase:** #phase/6-12 | **Owner:** DevOps + Operations Lead | **Status:** #status/draft

---

## 1. RESUMO EXECUTIVO

Sistema de monitorização automatizado para métricas de sistema, performance de pipelines, e health checks. Monitorização contínua garante deteção rápida de problemas.

| Campo | Descrição |
|-------|-----------|
| **Objetivo** | Monitorização automatizada do sistema |
| **Stack** | Prometheus, Grafana, Health Checks |
| **Custo** | 0€ (open source) |

---

## 2. ARQUITETURA DE MONITORIZAÇÃO

### 2.1 Estrutura de Monitorização

```
┌─────────────────────────────────────────────────────────────┐
│ SISTEMA DE MONITORIZAÇÃO                                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. MÉTRICAS DE SISTEMA                               │   │
│  │    - CPU, Memória, Disco                              │   │
│  │    - Latência de API                                 │   │
│  │    - Throughput                                      │   │
│  │    - Errors por minuto                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 2. MÉTRICAS DE PIPELINE                              │   │
│  │    - Tempo de execução                               │   │
│  │    - Taxa de sucesso                                 │   │
│  │    - Volume de dados processado                      │   │
│  │    - Retries                                         │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 3. MÉTRICAS DE NEGÓCIO                              │   │
│  │    - CLV médio                                       │   │
│  │    - ROI                                             │   │
│  │    - Número de sinais                                │   │
│  │    - PnL                                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 4. HEALTH CHECKS                                    │   │
│  │    - Database connection                            │   │
│  │    - API endpoints                                  │   │
│  │    - External services                              │   │
│  │    - Disk space                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. CONFIGURAÇÃO DO PROMETHEUS

### 3.1 Instalação

```bash
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus_data:
  grafana_data:
```

### 3.2 Configuração Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'valuebetting'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

---

## 4. MÉTRICAS DO SISTEMA

### 4.1 Métricas de Sistema

```python
# vbq/monitoring/system_metrics.py
from prometheus_client import Counter, Gauge, Histogram
import psutil
import time

# Métricas de CPU
cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percent')
memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percent')
disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percent')

# Métricas de API
api_latency = Histogram('api_latency_seconds', 'API latency')
api_requests_total = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
api_errors_total = Counter('api_errors_total', 'Total API errors', ['method', 'endpoint'])

def collect_system_metrics():
    """Coleta métricas de sistema"""
    cpu_usage.set(psutil.cpu_percent())
    memory_usage.set(psutil.virtual_memory().percent)
    disk_usage.set(psutil.disk_usage('/').percent)
```

### 4.2 Métricas de Pipeline

```python
# vbq/monitoring/pipeline_metrics.py
pipeline_duration = Histogram('pipeline_duration_seconds', 'Pipeline duration', ['pipeline_name'])
pipeline_success_total = Counter('pipeline_success_total', 'Total pipeline successes', ['pipeline_name'])
pipeline_failure_total = Counter('pipeline_failure_total', 'Total pipeline failures', ['pipeline_name'])
data_processed = Gauge('data_processed_bytes', 'Data processed bytes', ['pipeline_name'])
```

### 4.3 Métricas de Negócio

```python
# vbq/monitoring/business_metrics.py
clv_average = Gauge('clv_average_percent', 'Average CLV percent')
roi_daily = Gauge('roi_daily_percent', 'Daily ROI percent')
signals_generated = Counter('signals_generated_total', 'Total signals generated')
pnl_total = Gauge('pnl_total_eur', 'Total PnL in EUR')
```

---

## 5. HEALTH CHECKS

### 5.1 Health Check Endpoint

```python
# vbq/monitoring/health_checks.py
from fastapi import FastAPI
import psycopg2
import redis

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    checks = {
        'database': check_database(),
        'redis': check_redis(),
        'disk': check_disk(),
        'api': check_api()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return {
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks
    }, status_code

def check_database():
    """Verifica conexão com PostgreSQL"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return True
    except:
        return False

def check_redis():
    """Verifica conexão com Redis"""
    try:
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        return True
    except:
        return False

def check_disk():
    """Verifica espaço em disco"""
    disk = psutil.disk_usage('/')
    return disk.percent < 90  # Alerta se > 90%

def check_api():
    """Verifica se API está respondendo"""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        return response.status_code == 200
    except:
        return False
```

### 5.2 Health Check Automatizado

```python
# vbq/monitoring/automated_health_checks.py
from apscheduler.schedulers.background import BackgroundScheduler
from vbq.monitoring.health_checks import health_check
from vbq.alerts.telegram_client import TelegramClient

scheduler = BackgroundScheduler()
telegram = TelegramClient(
    token=TELEGRAM_BOT_TOKEN,
    chat_id=TELEGRAM_CHAT_ID
)

def automated_health_check():
    """Health check automatizado"""
    result, status_code = health_check()
    
    if status_code != 200:
        telegram.send_alert(
            level="CRITICAL",
            title="Health Check Falhou",
            message=f"Status: {result['status']}\n\nChecks: {result['checks']}"
        )

scheduler.add_job(
    func=automated_health_check,
    trigger="interval",
    minutes=5
)
scheduler.start()
```

---

## 6. DASHBOARDS GRAFANA

### 6.1 Dashboard de Sistema

```json
{
  "dashboard": {
    "title": "Value Betting - System Metrics",
    "panels": [
      {
        "title": "CPU Usage",
        "targets": [
          {
            "expr": "system_cpu_usage_percent"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "targets": [
          {
            "expr": "system_memory_usage_percent"
          }
        ]
      },
      {
        "title": "Disk Usage",
        "targets": [
          {
            "expr": "system_disk_usage_percent"
          }
        ]
      }
    ]
  }
}
```

### 6.2 Dashboard de Pipeline

```json
{
  "dashboard": {
    "title": "Value Betting - Pipeline Metrics",
    "panels": [
      {
        "title": "Pipeline Duration",
        "targets": [
          {
            "expr": "pipeline_duration_seconds"
          }
        ]
      },
      {
        "title": "Pipeline Success Rate",
        "targets": [
          {
            "expr": "pipeline_success_total / (pipeline_success_total + pipeline_failure_total)"
          }
        ]
      }
    ]
  }
}
```

### 6.3 Dashboard de Negócio

```json
{
  "dashboard": {
    "title": "Value Betting - Business Metrics",
    "panels": [
      {
        "title": "CLV Average",
        "targets": [
          {
            "expr": "clv_average_percent"
          }
        ]
      },
      {
        "title": "Daily ROI",
        "targets": [
          {
            "expr": "roi_daily_percent"
          }
        ]
      },
      {
        "title": "Total PnL",
        "targets": [
          {
            "expr": "pnl_total_eur"
          }
        ]
      }
    ]
  }
}
```

---

## 7. ALERTAS DE MONITORIZAÇÃO

### 7.1 Alertas de Prometheus

```yaml
# alert_rules.yml
groups:
  - name: valuebetting_alerts
    rules:
      - alert: HighCPUUsage
        expr: system_cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU usage is high"
          description: "CPU usage is {{ $value }}% for more than 5 minutes"
      
      - alert: HighMemoryUsage
        expr: system_memory_usage_percent > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage is high"
          description: "Memory usage is {{ $value }}% for more than 5 minutes"
      
      - alert: PipelineFailure
        expr: rate(pipeline_failure_total[5m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "Pipeline is failing"
          description: "Pipeline {{ $labels.pipeline_name }} has failures"
      
      - alert: LowCLV
        expr: clv_average_percent < 0.5
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "CLV is low"
          description: "Average CLV is {{ $value }}% for more than 1 hour"
```

### 7.2 Integração com Telegram

```python
# vbq/monitoring/prometheus_alerts.py
from prometheus_client import start_http_server
from prometheus_client.bridge.prometheus import PrometheusBridge

# Iniciar servidor Prometheus
start_http_server(8000)

# Configurar bridge para alertas
bridge = PrometheusBridge()
bridge.start()
```

---

## 8. MONITORIZAÇÃO CONTÍNUA

### 8.1 Coleta de Métricas

```python
# vbq/monitoring/metrics_collector.py
import time
from vbq.monitoring.system_metrics import collect_system_metrics
from vbq.monitoring.business_metrics import collect_business_metrics

def continuous_metrics_collection():
    """Coleta métricas continuamente"""
    while True:
        collect_system_metrics()
        collect_business_metrics()
        time.sleep(60)  # Coleta a cada 60 segundos
```

### 8.2 Agendamento

```python
# vbq/monitoring/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

scheduler.add_job(
    func=continuous_metrics_collection,
    trigger="interval",
    seconds=60
)

scheduler.start()
```

---

## 9. TESTES

### 9.1 Teste de Health Check

```python
# vbq/monitoring/tests/test_health_checks.py
def test_health_check():
    """Teste de health check"""
    result, status_code = health_check()
    assert status_code in [200, 503]
    assert 'status' in result
    assert 'checks' in result
```

---

## 10. LINKS CRUZADOS

- [[39_Automation/INDEX]] ← Secção mãe
- [[10_Monitoring/INDEX]] → Sistema de monitorização
- [[33_Alerting/INDEX]] → Sistema de alertas
- [[11_MLOps/INDEX]] → MLOps e monitorização

---

**Custo de implementação:** 0€ (open source)  
**Tempo estimado de implementação:** 1 semana  
**Prioridade:** ALTA (fundamental para visibilidade do sistema)
