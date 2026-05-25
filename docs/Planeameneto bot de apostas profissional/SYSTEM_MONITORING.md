# SYSTEM_MONITORING — Monitorização Multi-Desporto

**ID:** `OP-012` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active | **Versão:** `2.0.0-MULTISPORT`

---

## 1. OBJETIVO

Monitorizar sistema em tempo real para detetar problemas e garantir operacionalidade.

---

## 2. COMPONENTES MONITORIZADOS

| Componente | Métricas | Frequência |
|------------|----------|------------|
| Sistema | Health status, uptime | 1 min |
| Performance | Latência, throughput | 1 min |
| Banco de dados | Conexões, queries lentas | 5 min |
| ML Models (NBA) | Versão, predictions/min, CLV | 5 min |
| ML Models (Football) | Versão, predictions/min, CLV | 5 min |
| ML Models (MMA) | Versão, predictions/min, CLV | 5 min |
| Apostas NBA | Volume, PnL, CLV, drawdown | 1 min |
| Apostas Football | Volume, PnL, CLV, drawdown | 1 min |
| Apostas MMA | Volume, PnL, CLV, drawdown | 1 min |
| Global | Total exposure, global drawdown, loss streak | 1 min |

---

## 3. DASHBOARD MULTI-DESPORTO

```python
def build_monitoring_dashboard():
    """
    Constrói dashboard de monitorização em Grafana para multi-desporto.
    
    Painéis:
    1. Status do sistema global
    2. Performance (latência, throughput)
    3. Métricas por desporto (NBA, Football, MMA)
    4. Métricas globais (exposure, drawdown)
    5. Health de componentes
    """
    panels = [
        # Status global do sistema
        {
            'title': 'Global System Status',
            'query': 'global_system_health_status',
            'type': 'stat'
        },
        
        # Performance
        {
            'title': 'Inference Latency',
            'query': 'inference_latency_ms',
            'type': 'graph'
        },
        
        # Métricas por desporto - NBA
        {
            'title': 'NBA: Bets per Hour',
            'query': 'nba_bets_per_hour',
            'type': 'graph'
        },
        {
            'title': 'NBA: Daily PnL',
            'query': 'nba_daily_pnl_eur',
            'type': 'graph'
        },
        {
            'title': 'NBA: CLV Trend',
            'query': 'nba_clv_trend',
            'type': 'graph'
        },
        {
            'title': 'NBA: Drawdown',
            'query': 'nba_drawdown_pct',
            'type': 'graph'
        },
        
        # Métricas por desporto - Football
        {
            'title': 'Football: Bets per Hour',
            'query': 'football_bets_per_hour',
            'type': 'graph'
        },
        {
            'title': 'Football: Daily PnL',
            'query': 'football_daily_pnl_eur',
            'type': 'graph'
        },
        {
            'title': 'Football: CLV Trend',
            'query': 'football_clv_trend',
            'type': 'graph'
        },
        {
            'title': 'Football: Drawdown',
            'query': 'football_drawdown_pct',
            'type': 'graph'
        },
        
        # Métricas por desporto - MMA
        {
            'title': 'MMA: Bets per Hour',
            'query': 'mma_bets_per_hour',
            'type': 'graph'
        },
        {
            'title': 'MMA: Daily PnL',
            'query': 'mma_daily_pnl_eur',
            'type': 'graph'
        },
        {
            'title': 'MMA: CLV Trend',
            'query': 'mma_clv_trend',
            'type': 'graph'
        },
        {
            'title': 'MMA: Drawdown',
            'query': 'mma_drawdown_pct',
            'type': 'graph'
        },
        
        # Métricas globais
        {
            'title': 'Global: Total Exposure',
            'query': 'global_total_exposure_eur',
            'type': 'graph'
        },
        {
            'title': 'Global: Drawdown',
            'query': 'global_drawdown_pct',
            'type': 'graph'
        },
        {
            'title': 'Global: Loss Streak',
            'query': 'global_loss_streak',
            'type': 'stat'
        },
        
        # Health de componentes
        {
            'title': 'Component Health',
            'query': 'component_health_status',
            'type': 'table'
        }
    ]
    
    return panels
```

---

## 4. ALERTAS MULTI-DESPORTO

```python
def setup_monitoring_alerts():
    """Configura alertas de monitorização para multi-desporto."""
    alerts = [
        # Alertas globais
        {
            'name': 'System Down',
            'condition': 'global_system_health_status == 0',
            'severity': 'critical'
        },
        {
            'name': 'High Latency',
            'condition': 'inference_latency_ms > 500',
            'severity': 'warning'
        },
        {
            'name': 'Global Drawdown Critical',
            'condition': 'global_drawdown_pct > 15',
            'severity': 'critical'
        },
        {
            'name': 'Global Loss Streak',
            'condition': 'global_loss_streak > 10',
            'severity': 'warning'
        },
        
        # Alertas NBA
        {
            'name': 'NBA: No Bets',
            'condition': 'nba_bets_last_hour == 0',
            'severity': 'warning'
        },
        {
            'name': 'NBA: Negative PnL',
            'condition': 'nba_daily_pnl_eur < -100',
            'severity': 'warning'
        },
        {
            'name': 'NBA: Drawdown Exceeded',
            'condition': 'nba_drawdown_pct > 15',
            'severity': 'critical'
        },
        {
            'name': 'NBA: CLV Negative Streak',
            'condition': 'nba_clv_negative_streak > 50',
            'severity': 'warning'
        },
        
        # Alertas Football
        {
            'name': 'Football: No Bets',
            'condition': 'football_bets_last_hour == 0',
            'severity': 'warning'
        },
        {
            'name': 'Football: Negative PnL',
            'condition': 'football_daily_pnl_eur < -100',
            'severity': 'warning'
        },
        {
            'name': 'Football: Drawdown Exceeded',
            'condition': 'football_drawdown_pct > 18',
            'severity': 'critical'
        },
        {
            'name': 'Football: CLV Negative Streak',
            'condition': 'football_clv_negative_streak > 40',
            'severity': 'warning'
        },
        
        # Alertas MMA
        {
            'name': 'MMA: No Bets',
            'condition': 'mma_bets_last_hour == 0',
            'severity': 'warning'
        },
        {
            'name': 'MMA: Negative PnL',
            'condition': 'mma_daily_pnl_eur < -100',
            'severity': 'warning'
        },
        {
            'name': 'MMA: Drawdown Exceeded',
            'condition': 'mma_drawdown_pct > 20',
            'severity': 'critical'
        },
        {
            'name': 'MMA: CLV Negative Streak',
            'condition': 'mma_clv_negative_streak > 30',
            'severity': 'warning'
        },
        
        # Alertas de modelo
        {
            'name': 'NBA Model Degraded',
            'condition': 'nba_validation_clv < 0.02',
            'severity': 'warning'
        },
        {
            'name': 'Football Model Degraded',
            'condition': 'football_validation_clv < 0.04',
            'severity': 'warning'
        },
        {
            'name': 'MMA Model Degraded',
            'condition': 'mma_validation_clv < 0.05',
            'severity': 'warning'
        }
    ]
    
    return alerts
```

---

## 5. MLOPS MULTI-DESPORTO

### 5.1 MLflow Tracking

```python
def setup_mlflow():
    """
    Configura MLflow para tracking de modelos multi-desporto.
    """
    mlflow.set_tracking_uri("mlflow_server")
    
    # Track cada modelo base e ensemble
    experiments = {
        "nba_ensemble": {"nba_xgb", "nba_lgb", "nba_cat", "nba_meta"},
        "football_model": {"football_poisson", "football_xgb"},
        "mma_model": {"mma_bayesian"}
    }
    
    for sport, models in experiments.items():
        mlflow.set_experiment(sport)
        for model in models:
            with mlflow.start_run(run_name=model):
                # Registrar hiperparâmetros
                mlflow.log_params(model_config[model])
                # Registrar métricas
                mlflow.log_metrics(validation_metrics[model])
                # Logar modelo
                mlflow.sklearn.log_model(model_object, "model")
```

### 5.2 Retreino Automático

```python
def setup_retraining_schedule():
    """
    Configura schedule de retreino para multi-desporto.
    """
    schedules = {
        # Ensemble NBA: Semanal
        "nba_ensemble": {"frequency": "weekly", "day": "sunday"},
        
        # Online learning NBA: Diário
        "nba_online_learning": {"frequency": "daily"},
        
        # Football: Semanal
        "football_model": {"frequency": "weekly", "day": "monday"},
        
        # MMA: Pós-evento (após cada card UFC) - CRÍTICO
        "mma_model": {"frequency": "event_trigger", "event": "ufc_card_end"}
    }
    
    return schedules

def auto_promote_if_improved():
    """
    Promoção automática se melhoria > 1%.
    """
    current_clv = get_current_model_clv()
    new_clv = get_new_model_clv()
    
    if new_clv > current_clv * 1.01:  # +1% improvement
        promote_to_production(new_model)
        log_promotion(old=current_clv, new=new_clv)
```

### 5.3 Model Versioning

```python
def version_models():
    """
    Versionamento automático de modelos.
    """
    versioning = {
        "nba": {
            "current": "v2.1.0",
            "ensemble": ["xgb_v2.1.0", "lgb_v2.1.0", "cat_v2.1.0", "meta_v2.1.0"],
            "online_ratings": "ratings_v2.1.0"
        },
        "football": {
            "current": "v1.0.0",
            "poisson": "poisson_v1.0.0",
            "xgb": "xgb_v1.0.0"
        },
        "mma": {
            "current": "v1.0.0",
            "bayesian": "bayesian_v1.0.0",
            "last_event": "ufc_300"
        }
    }
    return versioning
```

---

## 6. COMPLIANCE MULTI-JURISDIÇÃO

### 6.1 Documentação Regulamentar

```python
def setup_compliance_docs():
    """
    Documenta regulamentação por país.
    """
    regulations = {
        "PT": {
            "authority": "SRIJ",
            "license_required": True,
            "disclaimer_required": True,
            "tax_reporting": True
        },
        "UK": {
            "authority": "UKGC",
            "license_required": True,
            "disclaimer_required": True,
            "tax_reporting": False
        },
        "US": {
            "authority": "State Gaming Commissions",
            "license_required": True,
            "disclaimer_required": True,
            "tax_reporting": True
        }
    }
    return regulations
```

### 6.2 Transparência

```python
def publish_transparency_report():
    """
    Publica CLV por desporto e mercado.
    """
    report = {
        "nba": {
            "moneyline_clv": 0.035,
            "spread_clv": 0.028,
            "total_clv": 0.032
        },
        "football": {
            "ah_clv": 0.042,
            "ou25_clv": 0.038
        },
        "mma": {
            "moneyline_clv": 0.055,
            "mov_clv": 0.048
        }
    }
    return report
```

---

## 7. LOGGING

```python
def setup_logging():
    """Configura logging estruturado."""
    logger.configure(
        handlers=[
            {
                'sink': 'logs/system.log',
                'rotation': '1 day',
                'retention': '30 days'
            },
            {
                'sink': lambda msg: send_to_prometheus(msg),
                'serialize': True
            }
        ]
    )
```

---

## 8. CRITÉRIOS

- **Dashboard em tempo real** atualizado a cada minuto
- **Alertas imediatos** para eventos críticos
- **Logs retidos** por 30 dias
- **Métricas exportadas** para Prometheus
- **Monitorização por desporto** separada
- **Alertas específicos** por desporto e global
- **Circuit breaker automático** em drawdown > 15% global

---

## 9. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[09_Monitoring/INDEX]]
