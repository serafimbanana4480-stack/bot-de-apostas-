# MONITORIZAÇÃO DE DRIFT — Detecção e Resposta à Degradação do Modelo

**ID:** `ML-010` | **Fase:** #phase/6-12 | **Owner:** MLOps Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Detetar quando o modelo degrada em produção devido a mudanças nos dados (data drift) ou no comportamento do sistema (model drift), e acionar respostas automáticas para mitigar o impacto.

---

## 2. TIPOS DE DRIFT

### 2.1 Feature Drift
Mudança na distribuição das features de entrada.

**Causas comuns:**
- Mudança na forma das equipas
- Novos padrões de jogo
- Mudança na forma como os dados são recolhidos
- Sazonalidade (playoffs vs temporada regular)

**Deteção:**
- PSI (Population Stability Index) > 0.2
- KS test (Kolmogorov-Smirnov) p-value < 0.05
- Comparação de histogramas

### 2.2 Prediction Drift
Mudança na distribuição das predições do modelo.

**Causas comuns:**
- Calibração desajustada
- Mudança no comportamento do mercado
- Modelo overfitted a regime específico

**Deteção:**
- Média de probabilidades muda > 0.05
- Distribuição de predições desvia do histórico
- Win rate real vs predito diverge

### 2.3 Concept Drift
Mudança na relação entre features e target.

**Causas comuns:**
- Novas estratégias de equipas
- Mudanças nas regras do jogo
- Novos fatores de performance não capturados

**Deteção:**
- CLV médio cai consistentemente
- Performance em hold-out set degrada
- Feature importance muda significativamente

---

## 3. SISTEMA DE MONITORIZAÇÃO

### 3.1 Métricas Calculadas Diariamente

```python
# Para cada feature importante
psi = calculate_psi(feature_historical, feature_recente)

# Para predições
prediction_mean_recent = predictions_last_7d.mean()
prediction_mean_historical = predictions_all_time.mean()

# Para performance
clv_recent = clv_last_50_bets.mean()
clv_historical = clv_all_time.mean()
```

### 3.2 Thresholds de Alerta

| Métrica | Threshold Normal | Warning | Crítico | Ação |
|---------|------------------|---------|----------|------|
| PSI (feature drift) | < 0.1 | 0.1 - 0.2 | > 0.2 | Investigar feature |
| Prediction mean shift | < 0.02 | 0.02 - 0.05 | > 0.05 | Recalibrar |
| CLV decline | > 1% | 0 - 1% | < 0% | Retreinar |
| Feature importance change | < 10% | 10 - 25% | > 25% | Investigar |

---

## 4. RESPOSTA AUTOMÁTICA

### 4.1 Nível 1: Leve (Warning)

**Trigger:** PSI 0.1 - 0.2 em 1-2 features

**Ação:**
- Alerta para equipa técnica
- Monitorização aumentada (cada 4h em vez de 24h)
- Coletar mais dados para validação

### 4.2 Nível 2: Moderado

**Trigger:** PSI > 0.2 em 3+ features OU CLV < 1% por 7 dias

**Ação:**
- Retreino triggered com últimos 6 meses + peso extra em dados recentes
- Shadow deployment do novo modelo
- Comparação CLV shadow vs produção por 3 dias

### 4.3 Nível 3: Crítico

**Trigger:** PSI > 0.3 em 5+ features OU CLV < 0% por 14 dias

**Ação:**
- Retreino imediato com dados recentes
- Se shadow não melhora → rollback para versão anterior
- Investigação manual de causa raiz
- Pausa de novos sinais se performance não recupera em 7 dias

---

## 5. PREVENÇÃO DE DRIFT

### 5.1 Retreino Contínuo

- **Semanal:** Retreino automático com dados da última semana
- **Mensal:** Retreino profundo com dados dos últimos 3 meses
- **Trimestral:** Reavaliação completa de features e hiperparâmetros

### 5.2 Feature Engineering Adaptativa

- Features com drift alto são desativadas temporariamente
- Novas features são testadas em shadow mode
- Sistema de feedback automático para feature importance

### 5.3 Calibração Dinâmica

- Recalibração mensal dos calibradores isotónicos
- Ajuste de regimes se necessário
- Monitorização contínua de Brier Score e ECE

---

## 6. MONITORIZAÇÃO DE LONGO PRAZO

### 6.1 Métricas Trimestrais

- Estabilidade de feature importance (top 10 features devem ser consistentes)
- Tendência de CLV (deve ser estável ou crescente)
- Taxa de drift events (deve diminuir com o tempo)

### 6.2 Relatório de Saúde do Modelo

Gerado trimestralmente com:
- Histórico de drift events
- Ações tomadas e sua eficácia
- Recomendações para melhorias
- Previsão de drift sazonal (ex: playoffs)

---

## 7. INTEGRAÇÃO COM MLOPS

### 7.1 Pipeline Automático

```
Diariamente:
  1. Calcular PSI para todas as features importantes
  2. Calcular métricas de predição
  3. Calcular CLV rolling
  4. Comparar com thresholds
  5. Se threshold excedido → acionar resposta apropriada
  6. Log tudo em MLflow
```

### 7.2 Dashboard Grafana

Painel "Model Drift" com:
- PSI por feature (gráfico de barras)
- Predição mean ao longo do tempo (line chart)
- CLV rolling (line chart)
- Alertas visuais quando thresholds excedidos

---

## 8. LINKS CRUZADOS

- [[11_MLOps/INDEX]] ← Secção mãe
- [[48_Data_Drift/INDEX]] → Detecção detalhada de drift
- [[30_Model_Registry/INDEX]] → Gestão de versões de modelos