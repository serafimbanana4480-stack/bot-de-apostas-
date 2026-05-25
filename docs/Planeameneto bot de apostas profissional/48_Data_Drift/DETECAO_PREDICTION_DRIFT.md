# DETECAO_PREDICTION_DRIFT — Monitorização de Distribuição de Predições

**ID:** `DRIFT-002` | **Fase:** #phase/6 | **Owner:** Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Detetar mudanças significativas na distribuição das predições do modelo, indicando que o comportamento de output do modelo está a mudar, mesmo que as features de entrada permaneçam estáveis.

---

## 2. CONTEXTO

Prediction drift ocorre quando:
- O modelo começa a produzir predições com distribuições diferentes do esperado
- As probabilidades estimadas mudam sistematicamente
- A calibração do modelo degrada

Isso pode indicar:
- O modelo está a ficar desajustado (overfitting/underfitting)
- O modelo está a encontrar padrões espúrios
- Há mudanças no processo gerador de dados que afetam o output

---

## 3. MÉTRICAS DE DETEÇÃO

### 3.1 Distribuição de Probabilidades

Monitorizar a distribuição das probabilidades preditas pelo modelo.

**Métricas:**
- **Média de probabilidades:** Mudança na média das probs preditas
- **Mediana de probabilidades:** Mudança na mediana
- **Desvio padrão:** Mudança na variância das probs
- **Skewness:** Mudança na assimetria da distribuição
- **Kurtosis:** Mudança na "cauda" da distribuição

**Thresholds:**
- Mudança > 0.05 na média: WARNING
- Mudança > 0.10 na média: CRITICAL
- Mudança > 20% no desvio padrão: WARNING

### 3.2 PSI em Probabilidades

Aplicar PSI diretamente na distribuição de probabilidades preditas.

**Configuração:**
- Bins: 10 bins de igual tamanho (0.0-0.1, 0.1-0.2, ..., 0.9-1.0)
- Threshold PSI: 0.15 (mais conservativo que features)

**Interpretação:**
- PSI < 0.05: Estável
- PSI 0.05 - 0.15: Monitorizar
- PSI 0.15 - 0.25: Investigar
- PSI > 0.25: Ação necessária

### 3.3 KS Test em Probabilidades

Teste Kolmogorov-Smirnov nas distribuições de probabilidade.

**Interpretação:**
- p-value < 0.01: Distribuições diferentes (drift detetado)
- KS statistic > 0.10: Diferença significativa

### 3.4 Calibração do Modelo

Monitorizar a calibração das probabilidades preditas.

**Métodos:**
- **Brier Score:** Erro quadrático médio das probabilidades
- **Reliability Diagram:** Comparar probs preditas vs probs reais
- **Expected Calibration Error (ECE):** Erro médio de calibração

**Thresholds:**
- Aumento > 0.02 no Brier Score: WARNING
- Aumento > 0.05 no Brier Score: CRITICAL
- ECE > 0.10: Calibração pobre

---

## 4. CENÁRIOS DE PREDICTION DRIFT

### 4.1 Cenário 1: Shift para Probabilidades Extremas

**Sintoma:** Modelo começa a produzir mais probs perto de 0 ou 1.

**Possíveis causas:**
- Overfitting a outliers recentes
- Mudança na incerteza do mercado
- Modelo a ficar demasiado confiante

**Risco:** Apostas com probs extremas podem ter EV enganoso.

### 4.2 Cenário 2: Shift para Probabilidades Moderadas

**Sintoma:** Modelo começa a produzir mais probs perto de 0.5.

**Possíveis causas:**
- Underfitting
- Perda de signal nas features
- Mudança na competitividade do mercado

**Risco:** Menos oportunidades de value betting.

### 4.3 Cenário 3: Mudança na Forma da Distribuição

**Sintoma:** Distribuição muda de forma (skewness, kurtosis).

**Possíveis causas:**
- Modelo a aprender padrões diferentes
- Mudança no comportamento do mercado
- Interação entre features mudando

**Risco:** Predições podem ser mal calibradas.

---

## 5. PROCEDIMENTO DE DETEÇÃO

### 5.1 Coleta de Dados

**Conjunto de Referência:**
- Predições do modelo em validação (out-of-sample)
- Período: últimos 3-6 meses
- Tamanho mínimo: 500 predições

**Conjunto Atual:**
- Predições recentes em produção
- Período: última semana
- Tamanho mínimo: 100 predições

### 5.2 Frequência de Verificação

| Métrica | Frequência | Justificação |
|---------|------------|--------------|
| Distribuição de probs | Diária | Detetar mudanças rápidas |
| Calibração (Brier) | Semanal | Requer outcomes reais |
| Reliability diagram | Semanal | Requer outcomes reais |
| PSI de probs | Diária | Alerta rápido |

### 5.3 Processo de Validação

1. **Coleta:** Extrair predições de referência e atual
2. **Cálculo:** Calcular estatísticas descritivas
3. **PSI:** Calcular PSI na distribuição de probs
4. **KS Test:** Aplicar KS test nas distribuições
5. **Calibração:** Calcular Brier Score e ECE se outcomes disponíveis
6. **Comparação:** Comparar com thresholds
7. **Alerta:** Gerar alertas se necessário

---

## 6. THRESHOLDS E ALERTAS

### 6.1 Thresholds por Métrica

| Métrica | INFO | WARNING | HIGH | CRITICAL |
|---------|------|---------|------|----------|
| PSI probs | < 0.05 | 0.05 - 0.15 | 0.15 - 0.25 | > 0.25 |
| Δ Média probs | < 0.02 | 0.02 - 0.05 | 0.05 - 0.10 | > 0.10 |
| Δ Desvio padrão | < 10% | 10 - 20% | 20 - 30% | > 30% |
| Δ Brier Score | < 0.01 | 0.01 - 0.02 | 0.02 - 0.05 | > 0.05 |
| ECE | < 0.05 | 0.05 - 0.10 | 0.10 - 0.15 | > 0.15 |

### 6.2 Níveis de Alerta

| Nível | Condição | Ação |
|-------|----------|------|
| INFO | Qualquer métrica em INFO | Logging apenas |
| WARNING | ≥ 1 métrica em WARNING | Monitorizar de perto |
| HIGH | ≥ 1 métrica em HIGH | Preparar retraining |
| CRITICAL | ≥ 1 métrica em CRITICAL | Pausar apostas; investigar |

---

## 7. ANÁLISE DE RESULTADOS

### 7.1 Diagnóstico de Prediction Drift

Quando drift é detetado, investigar:
- **Feature drift correlato:** Features também mudaram?
- **Target drift:** Outcomes mudaram?
- **Model stability:** Modelo está instável?
- **Data quality:** Problemas na coleta de dados?

### 7.2 Visualização

Criar visualizações para análise:
- Histogramas de probs (ref vs atual)
- Time series de probs médias ao longo do tempo
- Reliability diagrams (calibração)
- Time series de Brier Score
- Scatter plot de probs preditas vs probs reais

### 7.3 Análise de Segmentação

Analisar drift por segmentos:
- Por tipo de aposta (moneyline, over/under, etc.)
- Por desporto (futebol, basquetebol, etc.)
- Por liga (Premier League, NBA, etc.)
- Por range de odds (low, medium, high)

**Objetivo:** Identificar se drift é generalizado ou específico a certos segmentos.

---

## 8. INTEGRAÇÃO COM SISTEMA

### 8.1 Pipeline de Monitorização

1. **Prediction Logging:** Guardar todas as predições em produção
2. **Outcome Tracking:** Guardar outcomes reais quando disponíveis
3. **Scheduler:** Executa verificações em frequência definida
4. **Drift Detection:** Calcula métricas de prediction drift
5. **Alert Engine:** Envia alertas se thresholds excedidos
6. **Dashboard:** Atualiza visualizações
7. **Storage:** Guarda resultados históricos

### 8.2 Integração com Feature Drift

Correlacionar prediction drift com feature drift:
- Se prediction drift sem feature drift → possível concept drift
- Se prediction drift com feature drift → feature drift pode ser a causa
- Se ambos estáveis → sistema saudável

### 8.3 Integração com Retraining

- Trigger automático de retraining quando:
  - PSI probs > 0.20 E Brier Score aumenta > 0.03
  - Calibração degrada significativamente (ECE > 0.12)
- Shadow mode quando:
  - PSI probs > 0.15
  - Brier Score aumenta > 0.02

---

## 9. MELHORIAS FUTURAS

- [ ] Implementar deteção de drift em tempo real para predições
- [ ] Adicionar métricas de incerteza (epistemic vs aleatórica)
- [ ] Desenvolver deteção de drift em ensemble models
- [ ] Implementar adaptive thresholds baseados em volatilidade histórica
- [ ] Adicionar deteção de drift em predições de valor esperado (EV)

---

## 10. LINKS CRUZADOS

- [[48_Data_Drift/INDEX]] ← Secção mãe
- [[48_Data_Drift/DETECAO_FEATURE_DRIFT]] → Drift de features
- [[48_Data_Drift/DETECAO_TARGET_DRIFT]] → Drift de target
- [[48_Data_Drift/DETECAO_CONCEPT_DRIFT]] → Drift de conceito
- [[48_Data_Drift/MITIGACAO_DRIFT]] → Resposta a drift
- [[11_MLOps/INDEX]] → Pipeline de retraining