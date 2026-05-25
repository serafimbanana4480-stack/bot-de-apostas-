# MONITORIZACAO_FEATURES — Monitorização de Qualidade e Drift

**ID:** `FEAT-005` | **Fase:** #phase/1-6 | **Owner:** Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar um sistema abrangente de monitorização para detectar problemas de qualidade em features, incluindo data drift, concept drift, missing values, outliers e anomalias. O sistema deve alertar automaticamente quando a qualidade das features degrada, prevenindo decisões baseadas em dados corrompidos.

---

## 2. CONTEXTO

Em value betting, a qualidade das features é crítica. Features com problemas podem levar a:

- **Previsões incorretas** → Perdas financeiras
- **Data leakage** → Overfitting em backtests
- **Missing values** → Falhas em inferência
- **Drift** → Modelos desatualizados
- **Outliers** → Previsões extremas erradas

Sem monitorização, problemas podem persistir por semanas ou meses antes de serem detectados manualmente. Monitorização proativa permite:
- Detecção precoce de problemas
- Alertas automáticos para engenheiros
- Análise de root cause
- Prevenção de perdas financeiras

---

## 3. TIPOS DE PROBLEMAS A MONITORIZAR

### 3.1 Data Drift

**Definição:** Mudança na distribuição de uma feature ao longo do tempo.

**Exemplos:**
- Win rate médio aumenta de 0.50 para 0.65
- eFG% diminui devido a mudança de regras
- Odds de mercado mudam de padrão

**Causas:**
- Mudanças no jogo (regras, estratégias)
- Mudanças na coleta de dados
- Mudanças de época (pre-season, playoffs)
- Problemas no pipeline de dados

### 3.2 Concept Drift

**Definição:** Mudança na relação entre features e target.

**Exemplos:**
- Win rate deixa de prever vitórias tão bem
- Features defensivas tornam-se mais importantes
- Padrões de mercado mudam

**Causas:**
- Mudanças no ambiente de apostas
- Novas estratégias de equipas
- Adaptação de bookmakers
- Mudanças sazonais

### 3.3 Missing Values

**Definição:** Aumento na taxa de valores nulos ou ausentes.

**Exemplos:**
- Taxa de missing de 0% para 15%
- Features específicas ficam nulas
- Padrões de missing mudam

**Causas:**
- Fontes de dados indisponíveis
- Mudanças no schema
- Problemas de parsing
- Falhas no pipeline

### 3.4 Outliers

**Definição:** Valores fora do range esperado.

**Exemplos:**
- Win rate de 1.5 (impossível)
- eFG% negativo
- Odds de 0 (impossível)

**Causas:**
- Erros de cálculo
- Dados corrompidos
- Unidades erradas
- Bugs no código

### 3.5 Freshness

**Definição:** Features não são atualizadas em tempo hábil.

**Exemplos:**
- Features com 24 horas de atraso
- Última atualização há 3 dias
- Features de jogos recentes ausentes

**Causas:**
- Pipeline falhando
- Fontes de dados indisponíveis
- Problemas de scheduling
- Backlogs de processamento

---

## 4. MÉTRICAS DE MONITORIZAÇÃO

### 4.1 Métricas Estatísticas

```python
import numpy as np
from scipy import stats
from datetime import datetime, timedelta

class FeatureMetrics:
    @staticmethod
    def calculate_distribution_metrics(values: np.ndarray) -> dict:
        """Calcula métricas de distribuição."""
        return {
            "mean": float(np.mean(values)),
            "median": float(np.median(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "q25": float(np.percentile(values, 25)),
            "q75": float(np.percentile(values, 75)),
            "skewness": float(stats.skew(values)),
            "kurtosis": float(stats.kurtosis(values))
        }
    
    @staticmethod
    def calculate_missing_rate(values: np.ndarray) -> float:
        """Calcula taxa de valores missing."""
        return float(np.isnan(values).sum() / len(values))
    
    @staticmethod
    def calculate_outlier_rate(values: np.ndarray, method: str = "iqr") -> float:
        """Calcula taxa de outliers."""
        if method == "iqr":
            q25, q75 = np.percentile(values, [25, 75])
            iqr = q75 - q25
            lower_bound = q25 - 1.5 * iqr
            upper_bound = q75 + 1.5 * iqr
            outliers = (values < lower_bound) | (values > upper_bound)
        elif method == "zscore":
            z_scores = np.abs(stats.zscore(values))
            outliers = z_scores > 3
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return float(outliers.sum() / len(values))
```

### 4.2 Métricas de Drift

```python
class DriftMetrics:
    @staticmethod
    def population_stability_index(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
        """
        Calcula PSI (Population Stability Index).
        
        PSI < 0.1: Sem drift
        0.1 <= PSI < 0.25: Drift leve
        PSI >= 0.25: Drift significativo
        """
        # Criar bins baseados na distribuição de referência
        _, bin_edges = np.histogram(reference, bins=bins)
        
        # Calcular distribuições
        ref_dist, _ = np.histogram(reference, bins=bin_edges, density=True)
        curr_dist, _ = np.histogram(current, bins=bin_edges, density=True)
        
        # Evitar divisão por zero
        ref_dist = np.where(ref_dist == 0, 0.0001, ref_dist)
        curr_dist = np.where(curr_dist == 0, 0.0001, curr_dist)
        
        # Calcular PSI
        psi = np.sum((curr_dist - ref_dist) * np.log(curr_dist / ref_dist))
        
        return float(psi)
    
    @staticmethod
    def kl_divergence(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
        """Calcula Divergência de KL entre duas distribuições."""
        # Criar histogramas
        ref_hist, bin_edges = np.histogram(reference, bins=bins, density=True)
        curr_hist, _ = np.histogram(current, bins=bin_edges, density=True)
        
        # Evitar zeros
        ref_hist = np.where(ref_hist == 0, 0.0001, ref_hist)
        curr_hist = np.where(curr_hist == 0, 0.0001, curr_hist)
        
        # Calcular KL divergence
        kl = np.sum(ref_hist * np.log(ref_hist / curr_hist))
        
        return float(kl)
    
    @staticmethod
    def wasserstein_distance(reference: np.ndarray, current: np.ndarray) -> float:
        """Calcula distância de Wasserstein (Earth Mover's Distance)."""
        from scipy.stats import wasserstein_distance
        return float(wasserstein_distance(reference, current))
    
    @staticmethod
    def ks_test(reference: np.ndarray, current: np.ndarray) -> dict:
        """Teste de Kolmogorov-Smirnov para comparar distribuições."""
        statistic, p_value = stats.ks_2samp(reference, current)
        return {
            "statistic": float(statistic),
            "p_value": float(p_value),
            "is_different": p_value < 0.05
        }
```

### 4.3 Métricas de Freshness

```python
class FreshnessMetrics:
    @staticmethod
    def calculate_age(timestamp: datetime, reference: datetime = None) -> timedelta:
        """Calcula idade de um timestamp."""
        reference = reference or datetime.now()
        return reference - timestamp
    
    @staticmethod
    def calculate_freshness_score(timestamps: list) -> dict:
        """Calcula métricas de freshness para múltiplos timestamps."""
        now = datetime.now()
        ages = [(now - ts).total_seconds() for ts in timestamps]
        
        return {
            "mean_age_seconds": float(np.mean(ages)),
            "max_age_seconds": float(np.max(ages)),
            "min_age_seconds": float(np.min(ages)),
            "stale_count": sum(1 for age in ages if age > 3600)  # >1 hora
        }
```

---

## 5. SISTEMA DE MONITORIZAÇÃO

### 5.1 Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│              FEATURE MONITORING SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Feature    │───→│  Metrics    │───→│  Drift      │    │
│  │  Store      │    │  Calculator │    │  Detector  │    │
│  └─────────────┘    └─────────────┘    └──────┬──────┘    │
│                                            │               │
│                                            ▼               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Quality    │←───│  Threshold  │←───│  Anomaly    │    │
│  │  Checker    │    │  Engine     │    │  Detector  │    │
│  └──────┬──────┘    └─────────────┘    └─────────────┘    │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Alert      │    │  Dashboard  │    │  Report     │    │
│  │  Generator  │    │  (Grafana)  │    │  Generator │    │
│  └──────┬──────┘    └─────────────┘    └─────────────┘    │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Slack      │    │  Email      │    │  PagerDuty  │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Implementação

```python
from typing import Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class FeatureMonitor:
    def __init__(self, feature_store_client, alert_manager):
        self.feature_store = feature_store_client
        self.alert_manager = alert_manager
        self.thresholds = self._load_thresholds()
    
    def _load_thresholds(self) -> Dict:
        """Carrega thresholds de configuração."""
        return {
            "psi_threshold": 0.25,
            "missing_rate_threshold": 0.05,
            "outlier_rate_threshold": 0.01,
            "freshness_threshold_hours": 24,
            "kl_divergence_threshold": 0.1
        }
    
    async def monitor_feature(self, feature_id: str) -> Dict:
        """Monitoriza uma única feature."""
        # Obter dados recentes
        current_data = await self.feature_store.get_recent_values(
            feature_id=feature_id,
            days=7
        )
        
        # Obter dados de referência (histórico)
        reference_data = await self.feature_store.get_historical_values(
            feature_id=feature_id,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now() - timedelta(days=7)
        )
        
        # Calcular métricas
        metrics = {
            "feature_id": feature_id,
            "timestamp": datetime.now().isoformat(),
            "current_metrics": FeatureMetrics.calculate_distribution_metrics(current_data),
            "missing_rate": FeatureMetrics.calculate_missing_rate(current_data),
            "outlier_rate": FeatureMetrics.calculate_outlier_rate(current_data),
            "drift_metrics": {
                "psi": DriftMetrics.population_stability_index(reference_data, current_data),
                "kl_divergence": DriftMetrics.kl_divergence(reference_data, current_data),
                "wasserstein": DriftMetrics.wasserstein_distance(reference_data, current_data),
                "ks_test": DriftMetrics.ks_test(reference_data, current_data)
            },
            "freshness": self._check_freshness(feature_id)
        }
        
        # Verificar thresholds
        alerts = self._check_thresholds(metrics)
        
        # Gerar alertas se necessário
        if alerts:
            await self.alert_manager.send_alerts(alerts)
        
        # Guardar métricas
        await self._save_metrics(metrics)
        
        return metrics
    
    def _check_thresholds(self, metrics: Dict) -> List[Dict]:
        """Verifica se métricas excedem thresholds."""
        alerts = []
        
        # Verificar PSI
        psi = metrics["drift_metrics"]["psi"]
        if psi > self.thresholds["psi_threshold"]:
            alerts.append({
                "severity": "HIGH" if psi > 0.5 else "MEDIUM",
                "type": "data_drift",
                "feature_id": metrics["feature_id"],
                "metric": "psi",
                "value": psi,
                "threshold": self.thresholds["psi_threshold"],
                "message": f"PSI de {psi:.3f} excede threshold de {self.thresholds['psi_threshold']}"
            })
        
        # Verificar missing rate
        missing_rate = metrics["missing_rate"]
        if missing_rate > self.thresholds["missing_rate_threshold"]:
            alerts.append({
                "severity": "HIGH",
                "type": "missing_values",
                "feature_id": metrics["feature_id"],
                "metric": "missing_rate",
                "value": missing_rate,
                "threshold": self.thresholds["missing_rate_threshold"],
                "message": f"Missing rate de {missing_rate:.2%} excede threshold de {self.thresholds['missing_rate_threshold']:.2%}"
            })
        
        # Verificar outlier rate
        outlier_rate = metrics["outlier_rate"]
        if outlier_rate > self.thresholds["outlier_rate_threshold"]:
            alerts.append({
                "severity": "MEDIUM",
                "type": "outliers",
                "feature_id": metrics["feature_id"],
                "metric": "outlier_rate",
                "value": outlier_rate,
                "threshold": self.thresholds["outlier_rate_threshold"],
                "message": f"Outlier rate de {outlier_rate:.2%} excede threshold de {self.thresholds['outlier_rate_threshold']:.2%}"
            })
        
        return alerts
    
    def _check_freshness(self, feature_id: str) -> Dict:
        """Verifica freshness de uma feature."""
        last_update = self.feature_store.get_last_update_timestamp(feature_id)
        age = FreshnessMetrics.calculate_age(last_update)
        
        return {
            "last_update": last_update.isoformat(),
            "age_hours": age.total_seconds() / 3600,
            "is_stale": age.total_seconds() > self.thresholds["freshness_threshold_hours"] * 3600
        }
    
    async def _save_metrics(self, metrics: Dict):
        """Guarda métricas no banco de dados."""
        await self.feature_store.save_monitoring_metrics(metrics)
```

---

## 6. SISTEMA DE ALERTAS

### 6.1 Tipos de Alertas

```python
class AlertSeverity:
    CRITICAL = "CRITICAL"  # Ação imediata necessária
    HIGH = "HIGH"          # Investigar dentro de 1 hora
    MEDIUM = "MEDIUM"      # Investigar dentro de 24 horas
    LOW = "LOW"            # Investigar na próxima sprint

class AlertType:
    DATA_DRIFT = "data_drift"
    CONCEPT_DRIFT = "concept_drift"
    MISSING_VALUES = "missing_values"
    OUTLIERS = "outliers"
    STALE_FEATURE = "stale_feature"
    PIPELINE_FAILURE = "pipeline_failure"
    VALIDATION_FAILURE = "validation_failure"
```

### 6.2 Implementação de Alertas

```python
import requests
from typing import List

class AlertManager:
    def __init__(self, config: Dict):
        self.slack_webhook = config.get("slack_webhook")
        self.email_recipients = config.get("email_recipients", [])
        self.pagerduty_key = config.get("pagerduty_key")
    
    async def send_alerts(self, alerts: List[Dict]):
        """Envia alertas através de múltiplos canais."""
        for alert in alerts:
            # Enviar para Slack
            await self._send_slack_alert(alert)
            
            # Enviar email para alertas HIGH/CRITICAL
            if alert["severity"] in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
                await self._send_email_alert(alert)
            
            # Enviar para PagerDuty para alertas CRITICAL
            if alert["severity"] == AlertSeverity.CRITICAL:
                await self._send_pagerduty_alert(alert)
    
    async def _send_slack_alert(self, alert: Dict):
        """Envia alerta para Slack."""
        if not self.slack_webhook:
            return
        
        color = {
            AlertSeverity.CRITICAL: "danger",
            AlertSeverity.HIGH: "danger",
            AlertSeverity.MEDIUM: "warning",
            AlertSeverity.LOW: "good"
        }.get(alert["severity"], "good")
        
        message = {
            "attachments": [
                {
                    "color": color,
                    "title": f"🚨 Feature Alert: {alert['type'].upper()}",
                    "fields": [
                        {"title": "Feature ID", "value": alert["feature_id"], "short": True},
                        {"title": "Severity", "value": alert["severity"], "short": True},
                        {"title": "Metric", "value": alert["metric"], "short": True},
                        {"title": "Value", "value": f"{alert['value']:.4f}", "short": True},
                        {"title": "Threshold", "value": f"{alert['threshold']:.4f}", "short": True}
                    ],
                    "text": alert["message"],
                    "footer": "Feature Store Monitoring",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        requests.post(self.slack_webhook, json=message)
    
    async def _send_email_alert(self, alert: Dict):
        """Envia alerta por email."""
        # Implementação com SendGrid, SES, etc.
        pass
    
    async def _send_pagerduty_alert(self, alert: Dict):
        """Envia alerta para PagerDuty."""
        if not self.pagerduty_key:
            return
        
        message = {
            "routing_key": self.pagerduty_key,
            "event_action": "trigger",
            "payload": {
                "summary": alert["message"],
                "severity": alert["severity"].lower(),
                "source": "feature-store",
                "custom_details": alert
            }
        }
        
        requests.post(
            "https://events.pagerduty.com/v2/enqueue",
            json=message
        )
```

---

## 7. SCHEDULING DE MONITORIZAÇÃO

### 7.1 Frequência de Monitorização

| Tipo de Monitorização | Frequência | Justificação |
|----------------------|------------|--------------|
| Freshness | A cada 15 minutos | Detecção rápida de falhas de pipeline |
| Missing values | A cada hora | Detecção de problemas de dados |
| Outliers | A cada hora | Detecção de anomalias |
| Data drift | Diário | Distribuições mudam gradualmente |
| Concept drift | Semanal | Relações mudam mais lentamente |
| Relatório completo | Mensal | Análise profunda |

### 7.2 Implementação com Prefect

```python
from prefect import flow, task
from prefect.schedulers import IntervalScheduler

@task
def monitor_freshness():
    """Monitoriza freshness de todas as features."""
    monitor = FeatureMonitor(feature_store_client, alert_manager)
    features = feature_store_client.list_features()
    
    for feature_id in features:
        freshness = monitor._check_freshness(feature_id)
        if freshness["is_stale"]:
            alert_manager.send_alert({
                "severity": AlertSeverity.HIGH,
                "type": AlertType.STALE_FEATURE,
                "feature_id": feature_id,
                "message": f"Feature {feature_id} está stale ({freshness['age_hours']:.1f}h)"
            })

@task
def monitor_data_drift():
    """Monitoriza data drift de todas as features."""
    monitor = FeatureMonitor(feature_store_client, alert_manager)
    features = feature_store_client.list_features()
    
    for feature_id in features:
        await monitor.monitor_feature(feature_id)

@flow(name="feature_monitoring_daily")
def daily_monitoring_flow():
    """Flow diário de monitorização."""
    monitor_data_drift()

@flow(name="feature_monitoring_hourly")
def hourly_monitoring_flow():
    """Flow horário de monitorização."""
    monitor_freshness()

# Scheduling
daily_monitoring_flow.schedule = IntervalScheduler(
    interval=timedelta(days=1),
    start_date=datetime.now()
)

hourly_monitoring_flow.schedule = IntervalScheduler(
    interval=timedelta(hours=1),
    start_date=datetime.now()
)
```

---

## 8. DASHBOARD E VISUALIZAÇÃO

### 8.1 Grafana Dashboard

**Panels sugeridos:**

1. **Feature Freshness**
   - Gauge: Idade média das features
   - Table: Features stale por ordem de idade
   - Time series: Idade das features ao longo do tempo

2. **Missing Values**
   - Gauge: Taxa média de missing
   - Bar chart: Missing rate por feature
   - Time series: Missing rate ao longo do tempo

3. **Data Drift**
   - Heatmap: PSI por feature ao longo do tempo
   - Bar chart: Features com PSI alto
   - Time series: PSI médio

4. **Outliers**
   - Gauge: Taxa média de outliers
   - Bar chart: Outlier rate por feature
   - Scatter plot: Valores vs distribuição esperada

5. **Alerts**
   - Stat: Total de alertas nas últimas 24h
   - Table: Alertas recentes
   - Pie chart: Alertas por severidade

### 8.2 Queries Prometheus

```promql
# Taxa de alertas por severidade
rate(feature_alerts_total{severity="HIGH"}[5m])

# PSI médio por feature
avg_over_time(feature_psi{feature_id="home_win_rate_decay5"}[1d])

# Missing rate por feature
feature_missing_rate{feature_id="home_win_rate_decay5"}

# Idade das features
feature_age_hours{feature_id="home_win_rate_decay5"}
```

---

## 9. BOAS PRÁTICAS

### 9.1 Thresholds

- **Baseline inicial:** Usar dados históricos para definir thresholds
- **Ajuste dinâmico:** Atualizar thresholds periodicamente
- **Contexto:** Thresholds diferentes por feature (ex: odds vs stats)
- **Sazonalidade:** Considerar padrões sazonais (playoffs vs regular season)

### 9.2 Alertas

- **Não spam:** Limitar frequência de alertas (ex: máximo 1/hora por feature)
- **Contexto:** Incluir informações suficientes para debugging
- **Ação clara:** Sugerir ações a tomar
- **Escalonamento:** Alertas mais severos para mais canais

### 9.3 Investigações

- **Root cause analysis:** Documentar causa raiz de cada alerta
- **Follow-up:** Criar tickets para investigação
- **Knowledge base:** Adicionar lições aprendidas
- **Prevenção:** Implementar checks para prevenir recorrência

---

## 10. BACKLOG TÉCNICO

- [ ] Implementar sistema de métricas estatísticas
- [ ] Implementar detectores de drift (PSI, KL, KS)
- [ ] Criar sistema de alertas (Slack, Email, PagerDuty)
- [ ] Implementar scheduling de monitorização
- [ ] Criar dashboard Grafana
- [ ] Implementar detecção de concept drift
- [ ] Adicionar monitorização de freshness
- [ ] Criar sistema de relatórios mensais
- [ ] Implementar auto-tuning de thresholds
- [ ] Adicionar integração com ML models (model drift)

---

## 11. LINKS CRUZADOS

- [[32_Feature_Store/INDEX]] ← Secção mãe
- [[32_Feature_Store/ARQUITETURA_FEATURE_STORE]] → Arquitetura geral
- [[32_Feature_Store/COMPUTACAO_FEATURES]] → Computação de features
- [[32_Feature_Store/SERVICO_FEATURES]] → API de serviço
- [[32_Feature_Store/INTEGRACAO_ML]] → Integração com ML models
- [[31_Data_Validation/INDEX]] → Validação de dados
- [[48_Data_Drift/INDEX]] → Monitorização de drift de dados
- [[05_Machine_Learning/INDEX]] → Modelos que usam features