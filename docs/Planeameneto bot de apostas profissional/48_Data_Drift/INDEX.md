# 48_Data Drift — INDEX

**ID:** `SEC-48` | **Fase:** #phase/6 | **Owner:** Data Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Detetar quando a distribuição dos dados de entrada muda significativamente, indicando que o modelo pode estar a ficar desajustado (model drift). Ação deve ser automática ou semi-automática.

---

## 2. TIPOS DE DRIFT

| Tipo | Definição | Teste | Threshold |
|------|-----------|-------|-----------|
| **Feature Drift** | Distribuição das features muda | KS test, PSI | PSI > 0.20 |
| **Prediction Drift** | Distribuição das predições muda | KS test nas probs | PSI > 0.15 |
| **Target Drift** | Distribuição dos outcomes muda | Proporção de vitórias | Δ > 5% |
| **Concept Drift** | Relação feature-target muda | Performance degradation | Δ accuracy > 10% |

---

## 3. RESPOSTA A DRIFT

| PSI | Ação |
|-----|------|
| 0.00 - 0.10 | Nenhuma (drift insignificante) |
| 0.10 - 0.20 | Monitorizar de perto; preparar retraining |
| 0.20 - 0.30 | Retraining triggered; shadow mode com novo modelo |
| > 0.30 | Alerta CRITICAL; pausar novas apostas até análise |

---

## 4. DOCUMENTAÇÃO

### 4.1 Detecção de Drift

| Ficheiro | Descrição |
|----------|-----------|
| [[48_Data_Drift/DETECAO_FEATURE_DRIFT]] | Monitorização de distribuição de features (PSI, KS test) |
| [[48_Data_Drift/DETECAO_PREDICTION_DRIFT]] | Monitorização de distribuição de predições |
| [[48_Data_Drift/DETECAO_TARGET_DRIFT]] | Monitorização de distribuição de outcomes |
| [[48_Data_Drift/DETECAO_CONCEPT_DRIFT]] | Monitorização de relação feature-target |

### 4.2 Resposta a Drift

| Ficheiro | Descrição |
|----------|-----------|
| [[48_Data_Drift/ALERTAS_DRIFT]] | Sistema de notificação automática |
| [[48_Data_Drift/ANALISE_CAUSAS_DRIFT]] | Investigação e diagnóstico de causas |
| [[48_Data_Drift/MITIGACAO_DRIFT]] | Estratégias de resposta e correção |

### 4.3 Implementação

| Ficheiro | Descrição |
|----------|-----------|
| [[48_Data_Drift/IMPLEMENTACAO_DRIFT]] | Pipeline de deteção automática e arquitetura |

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[11_MLOps/INDEX]] → Retraining e resposta a drift
