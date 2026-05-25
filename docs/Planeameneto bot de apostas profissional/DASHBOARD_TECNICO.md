# DASHBOARD_TECNICO — Dashboard Técnico

**ID:** `DB-006` | **Fase:** #phase/3 | **Owner:** Data Analyst | **Status:** #status/active

---

## 1. OBJETIVO

Definir dashboard técnico para monitorização de sistema.

---

## 2. COMPONENTES

| Componente | Métricas | Atualização |
|------------|----------|-------------|
| System Health | Status de componentes | Minuto |
| Performance | CPU, memória, latência | Minuto |
| Errors | Erros por tipo | Hora |
| Pipeline | Status ETL | Hora |
| Model | Performance do modelo | Dia |

---

## 3. IMPLEMENTAÇÃO GRAFANA

```python
def setup_grafana_dashboard():
    """Configura dashboard Grafana."""
    panels = [
        {
            'title': 'System Health',
            'type': 'stat',
            'targets': ['system_health_overall'],
            'refresh': '1m'
        },
        {
            'title': 'CPU Usage',
            'type': 'graph',
            'targets': ['cpu_usage_percent'],
            'refresh': '1m'
        },
        {
            'title': 'Execution Latency',
            'type': 'graph',
            'targets': ['execution_latency_ms'],
            'refresh': '1m'
        },
        {
            'title': 'Error Rate',
            'type': 'graph',
            'targets': ['error_rate_per_hour'],
            'refresh': '1h'
        }
    ]
    
    dashboard = {
        'title': 'Betting System Technical Dashboard',
        'panels': panels,
        'refresh': '1m'
    }
    
    return dashboard
```

---

## 4. ALERTAS

```python
def setup_alerts():
    """Configura alertas do dashboard."""
    alerts = [
        {
            'name': 'System Down',
            'condition': 'system_health_overall == 0',
            'severity': 'critical'
        },
        {
            'name': 'High CPU',
            'condition': 'cpu_usage_percent > 80',
            'severity': 'warning'
        },
        {
            'name': 'High Latency',
            'condition': 'execution_latency_ms > 300',
            'severity': 'warning'
        }
    ]
    
    return alerts
```

---

## 5. CRITÉRIOS

- **Atualização minuto** para métricas críticas
- **Alertas críticos** via Telegram
- **Acesso restrito** a equipa técnica

---

## 6. LINKS CRUZADOS

- [[09_Monitoring/INDEX]]
- [[SYSTEM_MONITORING]]
