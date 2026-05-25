# MONITORIZACAO_DRIFT

**ID:** `DD-006` | **Fase:** #phase/6 | **Owner:** Data Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Especificar o sistema de monitorização contínua de drift de dados, incluindo métricas, dashboards, alertas e procedimentos de resposta.

---

## 2. ARQUITETURA DE MONITORIZAÇÃO

```
┌─────────────────────────────────────────────────────────────┐
│                    PIPELINE DE DADOS                         │
│  (Ingestão → Features → Predições → Apostas)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              COLETA DE MÉTRICAS DE DRIFT                     │
│  ├─ PSI (Population Stability Index) para features         │
│  ├─ KS test para distribuições                              │
│  ├─ PSI para predições                                      │
│  ├─ Proporção de outcomes                                   │
│  └─ Performance degradation (accuracy, CLV)                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    STORAGE DE MÉTRICAS                       │
│  └─ PostgreSQL (tabela drift_metrics)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    DASHBOARDS (Grafana)                      │
│  ├─ Dashboard de Feature Drift                              │
│  ├─ Dashboard de Prediction Drift                           │
│  ├─ Dashboard de Target Drift                               │
│  └─ Dashboard de Concept Drift                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA DE ALERTAS                        │
│  └─ Telegram Bot (envio de alertas)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. MÉTRICAS DE MONITORIZAÇÃO

### 3.1 Feature Drift

| Métrica | Descrição | Threshold | Frequência |
|---------|-----------|-----------|------------|
| PSI (Population Stability Index) | Mede estabilidade da distribuição | > 0.20 = alerta | Diário |
| KS Test | Teste Kolmogorov-Smirnov para distribuições | p < 0.05 = alerta | Diário |
| Mean Shift | Mudança na média da feature | Δ > 2σ = alerta | Diário |
| Variance Shift | Mudança na variância da feature | Δ > 50% = alerta | Diário |

### 3.2 Prediction Drift

| Métrica | Descrição | Threshold | Frequência |
|---------|-----------|-----------|------------|
| PSI das Probabilidades | Estabilidade das predições | > 0.15 = alerta | Diário |
| Distribuição de Classes | Proporção de previsões por classe | Δ > 10% = alerta | Diário |
| Confiança Média | Probabilidade média das predições | Δ > 0.10 = alerta | Diário |

### 3.3 Target Drift

| Métrica | Descrição | Threshold | Frequência |
|---------|-----------|-----------|------------|
| Win Rate Proporção | Proporção de vitórias | Δ > 5% = alerta | Semanal |
| CLV Médio | Edge médio real | Δ > 1% = alerta | Semanal |
| ROI Médio | Return on Investment médio | Δ > 2% = alerta | Semanal |

### 3.4 Concept Drift

| Métrica | Descrição | Threshold | Frequência |
|---------|-----------|-----------|------------|
| Accuracy Degradation | Queda na accuracy do modelo | Δ > 10% = alerta | Semanal |
| CLV Degradation | Queda no CLV médio | Δ > 1% = alerta | Semanal |
| Feature Importance Shift | Mudança na importância das features | Δ > 20% = alerta | Mensal |

---

## 4. DASHBOARDS GRAFANA

### 4.1 Dashboard de Feature Drift

**Panels:**
1. PSI por Feature (bar chart) - últimas 30 dias
2. PSI Trend (line chart) - PSI agregado ao longo do tempo
3. Top 10 Features com Maior Drift (table)
4. Distribuição de Features (histogram) - comparação baseline vs atual
5. KS Test p-values (heatmap) - features vs tempo

### 4.2 Dashboard de Prediction Drift

**Panels:**
1. Distribuição de Probabilidades (histogram) - comparação baseline vs atual
2. PSI de Predições (line chart) - ao longo do tempo
3. Taxa de Aprovação (gauge) - % de sinais aprovados
4. Probabilidade Média (line chart) - ao longo do tempo
5. Confiança do Modelo (line chart) - desvio padrão do ensemble

### 4.3 Dashboard de Target Drift

**Panels:**
1. Win Rate (line chart) - últimas 4 semanas
2. CLV Médio (line chart) - últimas 4 semanas
3. ROI Médio (line chart) - últimas 4 semanas
4. Proporção de Outcomes (pie chart) - vitórias/derrotas
5. Performance por Regime (bar chart) - favorito/equilibrado/underdog

### 4.4 Dashboard de Concept Drift

**Panels:**
1. Accuracy (line chart) - últimas 8 semanas
2. CLV por Feature Bucket (bar chart) - agrupado por quartis de features
3. Feature Importance (bar chart) - baseline vs atual
4. Correlation Matrix (heatmap) - features vs target
5. Performance por Regime Temporal (line chart) - semana/mês/trimestre

---

## 5. SISTEMA DE ALERTAS

### 5.1 Níveis de Alerta

| Nível | PSI | Ação |
|-------|-----|------|
| INFO | 0.00 - 0.10 | Nenhuma (drift insignificante) |
| WARNING | 0.10 - 0.20 | Monitorizar de perto; preparar retraining |
| CRITICAL | 0.20 - 0.30 | Retraining triggered; shadow mode |
| EMERGENCY | > 0.30 | Pausar novas apostas até análise |

### 5.2 Canais de Notificação

| Canal | Tipo | Uso |
|-------|------|-----|
| Telegram Bot | Real-time | Alertas CRITICAL e EMERGENCY |
| Email | Diário | Resumo de drift (WARNING+) |
| Slack | Semanal | Relatório de métricas de drift |
| Grafana | Dashboard | Visualização contínua |

### 5.3 Formato de Alerta

```
🚨 ALERTA DE DRIFT - [NÍVEL]

📊 Métrica: [Feature/Prediction/Target/Concept Drift]
📈 Valor Atual: [PSI/Δ]
⚠️ Threshold: [Valor do threshold]
📅 Timestamp: [YYYY-MM-DD HH:MM:SS]
🔍 Detalhes: [Descrição do drift]

🎯 Ação Recomendada:
- [Ação 1]
- [Ação 2]

📋 Link para Dashboard: [URL do Grafana]
```

---

## 6. PROCEDIMENTO DE RESPOSTA

### 6.1 Quando PSI > 0.20 (CRITICAL)

1. **Imediato (0-1h):**
   - Enviar alerta CRITICAL via Telegram
   - Pausar novas apostas se PSI > 0.25
   - Iniciar investigação da causa

2. **Curto Prazo (1-24h):**
   - Analisar quais features têm maior drift
   - Verificar se é drift sazonal ou estrutural
   - Decidir se retraining é necessário

3. **Médio Prazo (24-72h):**
   - Se drift é estrutural: treinar novo modelo
   - Executar shadow mode com novo modelo
   - Comparar performance modelo novo vs atual
   - Se novo modelo é melhor: promover para produção

### 6.2 Quando PSI > 0.30 (EMERGENCY)

1. **Imediato (0-30min):**
   - Enviar alerta EMERGENCY via Telegram
   - PAUSAR TODAS AS NOVAS APOSTAS
   - Notificar stakeholder (Chief Quant Engineer)

2. **Curto Prazo (30min-4h):**
   - Investigação profunda da causa
   - Verificar se há corrupção de dados
   - Verificar se há mudança na fonte de dados

3. **Médio Prazo (4-24h):**
   - Corrigir causa raiz
   - Retreinar modelo com dados recentes
   - Validar novo modelo rigorosamente
   - Só retomar apostas após validação completa

---

## 7. AUTOMAÇÃO

### 7.1 Job de Monitorização (Prefect)

```python
# app/orchestration/monitor_drift.py
from prefect import task, flow
import pandas as pd
from scipy import stats
import numpy as np

@task
def calculate_psi(baseline: pd.Series, current: pd.Series, bins: int = 10) -> float:
    """Calcula Population Stability Index."""
    # Implementar cálculo de PSI
    pass

@task
def calculate_ks_test(baseline: pd.Series, current: pd.Series) -> float:
    """Calcula KS test p-value."""
    statistic, p_value = stats.ks_2samp(baseline, current)
    return p_value

@flow(name="monitor_drift_daily")
def monitor_drift_flow():
    """Flow de monitorização diária de drift."""
    # Carregar dados baseline e atuais
    # Calcular PSI para cada feature
    # Calcular KS test para cada feature
    # Calcular drift de predições
    # Calcular drift de target
    # Armazenar métricas no PostgreSQL
    # Enviar alertas se thresholds excedidos
    pass
```

### 7.2 Schedule

- **Feature Drift:** Diário às 06:00 UTC (antes do primeiro batch)
- **Prediction Drift:** Diário às 06:00 UTC
- **Target Drift:** Semanal às 06:00 UTC (segunda-feira)
- **Concept Drift:** Semanal às 06:00 UTC (segunda-feira)

---

## 8. BASELINE DE REFERÊNCIA

### 8.1 Estabelecimento de Baseline

O baseline é estabelecido durante o período de backtesting (últimos 30 dias de dados históricos).

**Processo:**
1. Coletar distribuição de cada feature dos últimos 30 dias
2. Calcular estatísticas descritivas (média, desvio padrão, quartis)
3. Armazenar baseline em PostgreSQL (tabela `drift_baseline`)
4. Versionar baseline com timestamp

### 8.2 Atualização de Baseline

O baseline é atualizado:
- **Mensalmente:** Com dados dos últimos 30 dias (se não houve drift significativo)
- **Após retraining:** Com dados usados para treinar o novo modelo
- **Mudança sazonal:** Antes de playoffs, off-season, etc.

---

## 9. INTEGRAÇÃO COM OUTROS SISTEMAS

### 9.1 MLOps (Retraining)

- Se drift > 0.20 → Trigger automático de retraining
- Se drift > 0.30 → Pausar apostas até retraining completo

### 9.2 Alerting

- Alertas de drift integrados com sistema de alertas geral (33_Alerting)
- Prioridade: CRITICAL drift = prioridade P1

### 9.3 Experiment Tracking

- Métricas de drift registadas no MLflow
- Correlação entre drift e performance do modelo

---

## 10. MELHORIAS FUTURAS

- [ ] Implementar deteção de drift em tempo real (streaming)
- [ ] Adicionar deteção de drift multivariado (não apenas univariado)
- [ ] Implementar auto-retraining com validação automática
- [ ] Adicionar explainability para drift (quais features causaram drift)
- [ ] Implementar deteção de drift por regime (playoffs vs regular season)

---

## 11. LINKS CRUZADOS

- [[48_Data_Drift/INDEX]] ← Index de Data Drift
- [[48_Data_Drift/DETECAO_FEATURE_DRIFT]] → Detecção de Feature Drift
- [[48_Data_Drift/DETECAO_PREDICTION_DRIFT]] → Detecção de Prediction Drift
- [[48_Data_Drift/DETECAO_TARGET_DRIFT]] → Detecção de Target Drift
- [[48_Data_Drift/DETECAO_CONCEPT_DRIFT]] → Detecção de Concept Drift
- [[48_Data_Drift/ALERTAS_DRIFT]] → Sistema de alertas
- [[33_Alerting/INDEX]] → Sistema de alertas geral
- [[11_MLOps/INDEX]] → MLOps e retraining