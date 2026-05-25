# MONITORIZAÇÃO DETALHADA — MLOPS LEVES

**ID:** `OPS-002` | **Fase:** #phase/4-6 | **Owner:** MLOps Engineer + DevOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Implementar sistema de monitorização abrangente que cobre métricas de sistema, de negócio e de modelo, com alertas automáticos e dashboard em tempo real.

---

## 2. ARQUITETURA DE MONITORIZAÇÃO

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA DE MONITORIZAÇÃO                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Prometheus   │    │  Grafana     │    │   Alertas    │  │
│  │  (Metrics)   │───→│  (Dashboard) │───→│  (Telegram)  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         ↑                   ↑                   ↑             │
│         │                   │                   │             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Python     │    │   PostgreSQL │    │   Redis      │  │
│  │  (Exporter)  │    │   (Queries)  │    │   (Cache)    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         ↑                   ↑                   ↑             │
│         │                   │                   │             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Aplicação   │    │   Betfair    │    │    NBA       │  │
│  │  (FastAPI)   │    │    API       │    │    API       │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. MÉTRICAS DO SISTEMA

### 3.1 Métricas de CPU e Memória

**Exporter:** `prometheus_python_client`

```python
from prometheus_client import Counter, Gauge, Histogram

# CPU
cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')

# Processos
process_cpu = Gauge('process_cpu_usage', 'Process CPU usage')
process_memory = Gauge('process_memory_bytes', 'Process memory usage')
```

**Alertas:**
- CPU > 80% sustained por 5 min → Alerta
- Memory > 85% → Alerta
- Disk usage > 90% → Alerta crítico

### 3.2 Métricas de Aplicação

```python
# Requests
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request latency')

# Database
db_query_duration = Histogram('db_query_duration_seconds', 'Database query latency')
db_connections = Gauge('db_connections_active', 'Active database connections')

# Cache
cache_hits = Counter('cache_hits_total', 'Cache hits', ['key'])
cache_misses = Counter('cache_misses_total', 'Cache misses', ['key'])

# Background jobs
job_duration = Histogram('job_duration_seconds', 'Background job duration', ['job_name'])
job_success = Counter('job_success_total', 'Successful jobs', ['job_name'])
job_failure = Counter('job_failure_total', 'Failed jobs', ['job_name'])
```

**Alertas:**
- HTTP requests 5xx > 5/min → Alerta
- DB query duration > 1s (p95) → Alerta
- Cache hit rate < 80% → Alerta
- Job failure rate > 10% → Alerta

### 3.3 Métricas de APIs Externas

```python
# Betfair API
betfair_api_latency = Histogram('betfair_api_latency_seconds', 'Betfair API latency')
betfair_api_errors = Counter('betfair_api_errors_total', 'Betfair API errors', ['error_type'])
betfair_rate_limit = Counter('betfair_rate_limit_hits_total', 'Rate limit hits')

# NBA API
nba_api_latency = Histogram('nba_api_latency_seconds', 'NBA API latency')
nba_api_errors = Counter('nba_api_errors_total', 'NBA API errors')

# ESPN API
espn_api_latency = Histogram('espn_api_latency_seconds', 'ESPN API latency')
espn_api_errors = Counter('espn_api_errors_total', 'ESPN API errors')
```

**Alertas:**
- API latency > 5s → Alerta
- API error rate > 5% → Alerta
- Rate limit hits > 10/min → Alerta crítico

---

## 4. MÉTRICAS DE NEGÓCIO

### 4.1 Métricas de Performance

```python
# ROI
roi_cumulative = Gauge('business_roi_cumulative', 'Cumulative ROI')
roi_rolling_7d = Gauge('business_roi_rolling_7d', 'ROI rolling 7 days')
roi_rolling_30d = Gauge('business_roi_rolling_30d', 'ROI rolling 30 days')

# CLV
clv_avg = Gauge('business_clv_avg', 'Average CLV')
clv_rolling_50 = Gauge('business_clv_rolling_50', 'CLV last 50 bets')
clv_rolling_100 = Gauge('business_clv_rolling_100', 'CLV last 100 bets')

# Bankroll
bankroll_current = Gauge('business_bankroll_eur', 'Current bankroll in EUR')
bankroll_peak = Gauge('business_bankroll_peak_eur', 'Peak bankroll in EUR')
bankroll_drawdown = Gauge('business_bankroll_drawdown_percent', 'Current drawdown %')

# Sinais
signals_generated = Counter('business_signals_generated_total', 'Signals generated')
signals_sent = Counter('business_signals_sent_total', 'Signals sent')
signals_executed = Counter('business_signals_executed_total', 'Signals executed')
```

**Alertas:**
- CLV rolling 3d < 0% → Alerta crítico
- Drawdown > 15% → Alerta crítico
- ROI rolling 7d < -5% → Alerta
- Bankroll < 50% do inicial → Alerta crítico

### 4.2 Métricas de Qualidade

```python
# Win rate
win_rate_total = Gauge('business_win_rate_total', 'Total win rate')
win_rate_home = Gauge('business_win_rate_home', 'Win rate home games')
win_rate_away = Gauge('business_win_rate_away', 'Win rate away games')
win_rate_b2b = Gauge('business_win_rate_b2b', 'Win rate back-to-back')

# Slippage
slippage_avg = Gauge('business_slippage_avg_percent', 'Average slippage %')
slippage_max = Gauge('business_slippage_max_percent', 'Maximum slippage %')

# Fill rate
fill_rate = Gauge('business_fill_rate_percent', 'Signal execution fill rate %')
```

**Alertas:**
- Win rate < 40% → Alerta
- Slippage avg > 2% → Alerta
- Fill rate < 80% → Alerta

---

## 5. MÉTRICAS DE MODELO

### 5.1 Métricas de Performance do Modelo

```python
# AUC
model_auc = Gauge('model_auc', 'Model AUC score')
model_auc_regime = Gauge('model_auc_regime', 'Model AUC by regime', ['regime'])

# Brier Score
brier_score = Gauge('model_brier_score', 'Model Brier score')
brier_score_regime = Gauge('model_brier_score_regime', 'Brier score by regime', ['regime'])

# ECE
ece = Gauge('model_ece', 'Expected Calibration Error')
ece_regime = Gauge('model_ece_regime', 'ECE by regime', ['regime'])
```

**Alertas:**
- AUC < 0.52 → Alerta
- Brier > Brier mercado → Alerta
- ECE > 0.05 → Alerta

### 5.2 Métricas de Meta-Modelo

```python
meta_auc = Gauge('meta_model_auc', 'Meta-model AUC')
meta_precision = Gauge('meta_model_precision', 'Meta-model precision @ 0.6')
meta_recall = Gauge('meta_model_recall', 'Meta-model recall @ 0.6')
meta_filter_rate = Gauge('meta_model_filter_rate', 'Meta-model filter rate %')
```

**Alertas:**
- Meta AUC < 0.52 → Alerta
- Filter rate < 20% ou > 80% → Alerta

### 5.3 Métricas de Drift

```python
# PSI (Population Stability Index)
psi_feature = Gauge('model_psi_feature', 'PSI for feature', ['feature'])
psi_max = Gauge('model_psi_max', 'Maximum PSI across features')

# Feature drift detected
drift_detected = Gauge('model_drift_detected', 'Drift detected flag')
```

**Alertas:**
- PSI > 0.2 em ≥ 3 features → Alerta crítico
- PSI > 0.5 em qualquer feature → Alerta crítico

---

## 6. DASHBOARD GRAFANA

### 6.1 Painel Principal (Overview)

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  ROI Cumulado          Bankroll Evolution              │
│  [Line Chart]          [Line Chart]                     │
├─────────────────────────────────────────────────────────┤
│  CLV Rolling 7d        Drawdown Current                │
│  [Gauge]               [Gauge]                          │
├─────────────────────────────────────────────────────────┤
│  Win Rate por Regime   Signals Last 24h               │
│  [Bar Chart]           [Stat Panel]                     │
└─────────────────────────────────────────────────────────┘
```

### 6.2 Painel de Sistema

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  CPU Usage              Memory Usage                     │
│  [Gauge]               [Gauge]                          │
├─────────────────────────────────────────────────────────┤
│  API Latency            DB Query Latency                │
│  [Heatmap]             [Heatmap]                        │
├─────────────────────────────────────────────────────────┤
│  Job Success Rate       Cache Hit Rate                  │
│  [Stat Panel]           [Stat Panel]                     │
└─────────────────────────────────────────────────────────┘
```

### 6.3 Painel de Modelo

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Model AUC             Brier Score                      │
│  [Time Series]          [Time Series]                    │
├─────────────────────────────────────────────────────────┤
│  ECE by Regime         Meta-Model AUC                   │
│  [Bar Chart]           [Time Series]                    │
├─────────────────────────────────────────────────────────┤
│  PSI Top Features      Drift Detected                   │
│  [Bar Chart]           [Alert Panel]                    │
└─────────────────────────────────────────────────────────┘
```

---

## 7. SISTEMA DE ALERTAS

### 7.1 Canais de Notificação

**Primário:** Telegram Bot
- Canal técnico para equipe
- Canal comercial para stakeholders (opcional)

**Secundário:** Email (SendGrid)
- Para alertas críticos

### 7.2 Níveis de Alerta

| Nível | Cor | Frequência | Destinatários |
|-------|-----|------------|---------------|
| Info | 🟢 | Diário (resumo) | Todos |
| Warning | 🟡 | Imediato | Equipe técnica |
| Critical | 🔴 | Imediato + SMS | Equipe técnica + stakeholders |

### 7.3 Regras de Alerta

```python
# Alerta de CLV negativo
def check_clv_alert():
    clv_3d = get_clv_rolling(3)
    
    if clv_3d < 0:
        send_alert(
            level="CRITICAL",
            message=f"CLV 3d negativo: {clv_3d*100:.1f}%",
            recipients=["technical_team"]
        )

# Alerta de Drawdown
def check_drawdown_alert():
    drawdown = get_current_drawdown()
    
    if drawdown > 0.15:
        send_alert(
            level="CRITICAL",
            message=f"Drawdown crítico: {drawdown*100:.1f}%",
            recipients=["technical_team", "stakeholders"]
        )
    elif drawdown > 0.10:
        send_alert(
            level="WARNING",
            message=f"Drawdown elevado: {drawdown*100:.1f}%",
            recipients=["technical_team"]
        )

# Alerta de Feed Offline
def check_feed_alert():
    last_update = get_last_odds_update()
    time_diff = datetime.now() - last_update
    
    if time_diff > timedelta(minutes=5):
        send_alert(
            level="CRITICAL",
            message=f"Feed offline há {time_diff}",
            recipients=["technical_team"]
        )

# Alerta de Modelo Desatualizado
def check_model_update_alert():
    last_update = get_last_model_update()
    days_since = (datetime.now() - last_update).days
    
    if days_since > 7:
        send_alert(
            level="WARNING",
            message=f"Modelo não atualizado há {days_since} dias",
            recipients=["technical_team"]
        )

# Alerta de Drift
def check_drift_alert():
    psi_values = get_psi_for_top_features()
    high_psi = [f for f, psi in psi_values if psi > 0.2]
    
    if len(high_psi) >= 3:
        send_alert(
            level="CRITICAL",
            message=f"Drift detectado em {len(high_psi)} features",
            recipients=["technical_team"]
        )
```

---

## 8. RETREINO DO MODELO

### 8.1 Pipeline de Retreino Semanal

```python
def weekly_retraining_pipeline():
    # 1. Recolher dados da última semana
    new_data = collect_data_last_week()
    
    # 2. Adicionar ao dataset de treino
    training_data = update_training_dataset(new_data)
    
    # 3. Treinar novo modelo com walk-forward
    new_model = train_model_with_walkforward(training_data)
    
    # 4. Avaliar modelo atual em dados recentes
    current_model_performance = evaluate_model_on_recent_data(current_model)
    
    # 5. Avaliar novo modelo em dados recentes
    new_model_performance = evaluate_model_on_recent_data(new_model)
    
    # 6. Comparar performance
    clv_improvement = new_model_performance['CLV'] - current_model_performance['CLV']
    
    # 7. Decisão de promoção
    if clv_improvement > 0.01:  # 1% de melhoria
        promote_model_to_production(new_model)
        send_alert(
            level="INFO",
            message=f"Novo modelo promovido: +{clv_improvement*100:.1f}% CLV"
        )
    else:
        send_alert(
            level="INFO",
            message=f"Modelo atual mantido: +{clv_improvement*100:.1f}% não suficiente"
        )
    
    # 8. Registar experimento
    log_experiment({
        'date': datetime.now(),
        'clv_improvement': clv_improvement,
        'promoted': clv_improvement > 0.01
    })
```

### 8.2 Agendamento

**Crontab:**
```
0 2 * * 1 /path/to/weekly_retraining.sh  # Segunda-feira 02:00
```

### 8.3 Rollback Automático

```python
def check_model_performance_rollback():
    # Se performance cai drasticamente após promoção
    current_clv = get_clv_last_7_days()
    previous_clv = get_clv_before_promotion()
    
    if current_clv < previous_clv * 0.95:  # Queda de 5%+
        rollback_to_previous_model()
        send_alert(
            level="CRITICAL",
            message=f"Rollback executado: CLV caiu {(1-current_clv/previous_clv)*100:.1f}%"
        )
```

---

## 9. DETECÇÃO DE DRIFT

### 9.1 PSI (Population Stability Index)

```python
def calculate_psi(reference, current, bins=10):
    """
    reference: distribuição de referência (treino)
    current: distribuição atual (produção)
    bins: número de bins para discretização
    """
    # Discretizar distribuições
    ref_counts, _ = np.histogram(reference, bins=bins)
    cur_counts, _ = np.histogram(current, bins=bins)
    
    # Calcular proporções
    ref_props = ref_counts / len(reference)
    cur_props = cur_counts / len(current)
    
    # Adicionar epsilon para evitar divisão por zero
    ref_props = np.clip(ref_props, 1e-10, 1)
    cur_props = np.clip(cur_props, 1e-10, 1)
    
    # Calcular PSI
    psi = np.sum((cur_props - ref_props) * np.log(cur_props / ref_props))
    
    return psi
```

### 9.2 Interpretação de PSI

| PSI | Interpretação | Ação |
|-----|---------------|------|
| < 0.1 | Sem drift | Nenhuma |
| 0.1 - 0.2 | Leve drift | Monitorizar |
| > 0.2 | Drift significativo | Alerta + investigar |
| > 0.5 | Drift severo | Retreinar modelo |

### 9.3 Pipeline de Detecção de Drift

```python
def weekly_drift_detection():
    # 1. Obter distribuição de referência (último mês de treino)
    reference_dist = get_reference_distribution()
    
    # 2. Obter distribuição atual (última semana de produção)
    current_dist = get_current_distribution()
    
    # 3. Calcular PSI para top 10 features
    top_features = get_top_10_features()
    
    drift_detected = False
    for feature in top_features:
        psi = calculate_psi(
            reference_dist[feature],
            current_dist[feature]
        )
        
        # Registar PSI
        log_psi_feature(feature, psi)
        
        if psi > 0.2:
            drift_detected = True
    
    # 4. Ação se drift detectado
    if drift_detected:
        send_alert(
            level="CRITICAL",
            message="Drift detectado em múltiplas features",
            recipients=["technical_team"]
        )
        
        # 5. Retreinar modelo com peso em dados recentes
        retrain_with_recent_data_weight()
```

---

## 10. BACKLOG

- [ ] Instalar e configurar Prometheus
- [ ] Instalar e configurar Grafana
- [ ] Implementar exporters Python
- [ ] Criar dashboards Grafana
- [ ] Configurar alertas Prometheus
- [ ] Integrar alertas com Telegram Bot
- [ ] Implementar pipeline de retreino semanal
- [ ] Implementar detecção de drift PSI
- [ ] Implementar rollback automático
- [ ] Criar runbooks de resposta a alertas

---

## 11. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[11_MLOps/INDEX]] → MLOps avançado
- [[33_Alerting/INDEX]] → Sistema de alertas detalhado
- [[48_Data_Drift/INDEX]] → Detecção de drift avançada
