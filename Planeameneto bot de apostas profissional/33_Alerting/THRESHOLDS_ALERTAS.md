# THRESHOLDS_ALERTAS — Definição Técnica de Thresholds

**ID:** `AL-001` | **Fase:** Todas | **Owner:** DevOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir os thresholds técnicos que disparam cada alerta do sistema.

---

## 2. THRESHOLDS POR MÉTRICA

### 2.1 Métricas de Sistema

| Métrica | Warning | Critical | Ação |
|---------|---------|----------|------|
| CPU Usage | > 70% | > 90% | Escalar verticalmente |
| Memory Usage | > 80% | > 95% | Escalar verticalmente |
| Disk Usage | > 80% | > 90% | Limpar logs/expandir disco |
| Network I/O | > 80% bandwidth | > 95% bandwidth | Escalar largura de banda |

### 2.2 Métricas de Aplicação

| Métrica | Warning | Critical | Ação |
|---------|---------|----------|------|
| API Latency (p95) | > 500ms | > 2000ms | Investigar bottlenecks |
| API Error Rate | > 1% | > 5% | Investigar erros |
| Database Connections | > 80% max | > 95% max | Escalar connection pool |
| Queue Length | > 1000 | > 5000 | Escalar workers |

### 2.3 Métricas de Negócio

| Métrica | Warning | Critical | Ação |
|---------|---------|----------|------|
| CLV Negativo (3d) | < -2% | < -5% | Pausar apostas, investigar |
| Drawdown Diário | > 5% | > 10% | Circuit breaker |
| ROI Semanal | < 0% | < -5% | Revisar modelo |
| Taxa de Rejeição | > 10% | > 20% | Investigar execução |

---

## 3. THRESHOLDS DE DRIFT

| Tipo de Drift | PSI | Ação |
|---------------|-----|------|
| Feature Drift | > 0.2 | Monitorizar |
| Feature Drift | > 0.5 | Alertar |
| Feature Drift | > 1.0 | Retraining |
| Prediction Drift | > 0.2 | Monitorizar |
| Prediction Drift | > 0.5 | Alertar |
| Prediction Drift | > 1.0 | Retraining |
| Concept Drift | Accuracy drop > 5% | Retraining |
| Concept Drift | Accuracy drop > 10% | Pausar produção |

---

## 4. CONFIGURAÇÃO

### Prometheus Alertmanager
```yaml
groups:
  - name: system
    rules:
      - alert: HighCPU
        expr: cpu_usage > 0.9
        for: 5m
        labels:
          severity: critical
```

### Telegram Bot
```python
THRESHOLDS = {
    'cpu_warning': 0.7,
    'cpu_critical': 0.9,
    'memory_warning': 0.8,
    'memory_critical': 0.95,
    'clv_negative_warning': -0.02,
    'clv_negative_critical': -0.05,
}
```

---

## 5. THRESHOLDS DE MODELO ML

| Métrica | Warning | Critical | Ação |
|---------|---------|----------|------|
| ROC-AUC (último CV) | < 0.57 | < 0.55 | Retreino urgente |
| Brier Score | > 0.25 | > 0.30 | Recalibração |
| ECE (Expected Calibration Error) | > 0.05 | > 0.10 | Recalibração |
| PSI (Feature Drift) | > 0.10 | > 0.25 | Investigar features |
| Prediction Drift | > 0.20 | > 0.50 | Retreino |
| Model Age | > 14 dias | > 30 dias | Retreino |

---

## 6. THRESHOLDS DE PIPELINE DE DADOS

| Métrica | Warning | Critical | Ação |
|---------|---------|----------|------|
| Odds não ingeridas (em dia de jogo) | > 30 min | > 60 min | Investigar feed |
| Pipeline latency | > 5 min | > 15 min | Verificar performance |
| Falhas de validação | > 5/dia | > 20/dia | Investigar dados |
| Jogos sem dados | > 2 | > 5 | Verificar fontes |
| Dados históricos missing | > 10% | > 25% | Re-ingestão |

---

## 7. CONFIGURACAO COMPLETA PROMETHEUS

### 7.1 System Alerts

```yaml
groups:
  - name: system
    rules:
      - alert: HighCPU
        expr: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "CPU usage above 90%"
          runbook_url: "https://wiki.internal/RB-CPU"

      - alert: HighMemory
        expr: 100 * (1 - ((node_memory_MemAvailable_bytes) / (node_memory_MemTotal_bytes))) > 95
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Memory usage above 95%"

      - alert: DiskFull
        expr: 100 - ((node_filesystem_avail_bytes{mountpoint="/"} * 100) / node_filesystem_size_bytes{mountpoint="/"}) > 90
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Disk usage above 90%"
```

### 7.2 Business Alerts

```yaml
groups:
  - name: business
    rules:
      - alert: NegativeCLV3D
        expr: avg_over_time(clv_3d[3d]) < -0.05
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "CLV 3-day average below -5%"
          runbook_url: "https://wiki.internal/RB-009"

      - alert: DrawdownAccelerating
        expr: (bankroll_hwm - current_bankroll) / bankroll_hwm > 0.10
        for: 5m
        labels:
          severity: high
        annotations:
          summary: "Drawdown exceeded 10%"
          runbook_url: "https://wiki.internal/RB-008"

      - alert: ModelDegraded
        expr: model_roc_auc < 0.55
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Model ROC-AUC dropped below 0.55"

      - alert: PipelineStalled
        expr: odds_last_ingestion_timestamp < (time() - 3600)
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "No odds ingested for 1 hour"
```

### 7.3 Python Thresholds Config

```python
# thresholds.py
from dataclasses import dataclass

@dataclass
class AlertThresholds:
    """Thresholds centralizados para todo o sistema."""
    
    # Sistema
    cpu_warning: float = 0.70
    cpu_critical: float = 0.90
    memory_warning: float = 0.80
    memory_critical: float = 0.95
    disk_warning: float = 0.80
    disk_critical: float = 0.90
    
    # API
    latency_p95_warning: float = 0.5  # 500ms
    latency_p95_critical: float = 2.0  # 2s
    error_rate_warning: float = 0.01
    error_rate_critical: float = 0.05
    
    # Negócio
    clv_negative_warning: float = -0.02
    clv_negative_critical: float = -0.05
    drawdown_daily_warning: float = 0.05
    drawdown_daily_critical: float = 0.10
    roi_weekly_warning: float = 0.0
    roi_weekly_critical: float = -0.05
    
    # Modelo
    roc_auc_warning: float = 0.57
    roc_auc_critical: float = 0.55
    brier_warning: float = 0.25
    brier_critical: float = 0.30
    ece_warning: float = 0.05
    ece_critical: float = 0.10
    psi_warning: float = 0.10
    psi_critical: float = 0.25
    
    # Pipeline
    odds_stalled_warning: float = 1800  # 30 min
    odds_stalled_critical: float = 3600  # 60 min
    validation_failures_warning: int = 5
    validation_failures_critical: int = 20

# Instância global
THRESHOLDS = AlertThresholds()
```

---

## 8. THRESHOLDS DINÂMICOS

### 8.1 Conceito

Thresholds fixos podem ser demasiado sensíveis ou demasiado lentos. Thresholds dinâmicos ajustam-se baseados no histórico recente.

```python
class DynamicThresholds:
    """Ajusta thresholds baseado em rolling statistics."""
    
    def __init__(self, window_days: int = 30):
        self.window_days = window_days
    
    def calculate_dynamic_threshold(
        self, 
        metric_history: pd.Series,
        z_score: float = 2.0
    ) -> float:
        """
        Threshold dinâmico = média + z_score * std_dev.
        
        Exemplo: Se latência média API é 200ms com std 50ms,
        threshold warning = 200 + 2*50 = 300ms (em vez de 500ms fixo).
        """
        mean = metric_history.mean()
        std = metric_history.std()
        return mean + z_score * std
    
    def get_latency_threshold(self) -> dict:
        """Retorna thresholds dinâmicos para latência."""
        recent_latency = self.db.get_latency_history(days=self.window_days)
        
        return {
            'warning': self.calculate_dynamic_threshold(recent_latency, z_score=2.0),
            'critical': self.calculate_dynamic_threshold(recent_latency, z_score=3.0)
        }
```

**Aplicação:** Ideal para métricas que variam naturalmente (latência API varia com número de utilizadores). Não recomendado para thresholds de negócio (drawdown, CLV) que devem ser fixos.

---

## 9. BACKLOG

- [x] Definir thresholds de sistema (CPU, memória, disco)
- [x] Definir thresholds de aplicação (latência, erros, conexões)
- [x] Definir thresholds de negócio (CLV, drawdown, ROI)
- [x] Definir thresholds de drift (PSI, prediction, concept)
- [x] Definir thresholds de modelo (AUC, Brier, ECE)
- [x] Definir thresholds de pipeline (odds, validação)
- [x] Implementar configuração Prometheus completa
- [x] Implementar thresholds Python centralizados
- [x] Documentar thresholds dinâmicos
- [ ] Implementar thresholds dinâmicos em produção
- [ ] Adicionar thresholds específicos para player props

---

## 10. LINKS CRUZADOS

- [[33_Alerting/INDEX]] ← Secção mãe
- [[33_Alerting/ALERTAS_TELEGRAM]] → Sistema de alertas
- [[10_Monitoring/DASHBOARD_TECNICO]] → Dashboard de métricas
- [[10_Monitoring/DASHBOARD_NEGOCIO]] → Dashboard de negócio
- [[26_Runbooks/INDEX]] → Runbooks de resposta
