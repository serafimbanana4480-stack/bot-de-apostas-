# DETECAO_CONCEPT_DRIFT — Monitorização de Relação Feature-Target

**ID:** `DRIFT-004` | **Fase:** #phase/6 | **Owner:** Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Detetar mudanças na relação entre as features e o target, indicando que o conceito que o modelo aprendeu mudou, mesmo que as distribuições de features e target permaneçam estáveis.

---

## 2. CONTEXTO

Concept drift ocorre quando:
- A relação entre features e target muda
- O modelo aprendeu um conceito que já não é válido
- As features têm o mesmo comportamento, mas explicam menos o target

**Exemplo no value betting:**
- Antes: "equipa em boa forma → maior probabilidade de vitória"
- Depois: "equipa em boa forma → menor probabilidade de vitória" (mudança tática)

**Importância:** Concept drift é o mais difícil de detetar e pode causar degradação silenciosa da performance do modelo.

---

## 3. MÉTRICAS DE DETEÇÃO

### 3.1 Performance Degradation

Monitorizar a performance do modelo ao longo do tempo.

**Métricas:**
- **Accuracy:** % de predições corretas
- **ROC AUC:** Capacidade de discriminação
- **Log Loss:** Erro de calibração
- **F1 Score:** Balance entre precision e recall
- **Expected Value (EV):** Valor esperado das apostas

**Thresholds:**
- Queda > 5% em accuracy: WARNING
- Queda > 10% em accuracy: HIGH
- Queda > 20% em accuracy: CRITICAL
- Queda > 0.05 em AUC: WARNING
- Queda > 0.10 em AUC: CRITICAL
- Queda > 15% em EV: WARNING
- Queda > 30% em EV: CRITICAL

### 3.2 Feature Importance Drift

Monitorizar mudanças na importância das features.

**Métodos:**
- **SHAP values:** Comparar valores SHAP médios ao longo do tempo
- **Permutation importance:** Comparar importance por permutação
- **Feature coefficients:** Comparar coeficientes do modelo

**Thresholds:**
- Mudança > 20% na importância de top 5 features: WARNING
- Mudança > 40% na importância de top 5 features: CRITICAL
- Mudança na ordem de ranking de features: WARNING

### 3.3 Residual Analysis

Analisar os resíduos do modelo ao longo do tempo.

**Métricas:**
- **Média dos resíduos:** Deve ser próxima de 0
- **Desvio padrão dos resíduos:** Mudança indica heteroscedasticidade
- **Autocorrelação dos resíduos:** Padrões temporais nos erros

**Thresholds:**
- Mudança > 0.02 na média dos resíduos: WARNING
- Mudança > 20% no desvio padrão: WARNING
- Autocorrelação > 0.3: WARNING

### 3.4 Adversarial Validation

Treinar um classificador para distinguir entre dados antigos e novos.

**Método:**
1. Criar dataset com dados antigos (label=0) e novos (label=1)
2. Treinar modelo para distinguir os dois períodos
3. Se AUC > 0.70, existe drift significativo

**Interpretação:**
- AUC < 0.55: Sem drift
- AUC 0.55 - 0.65: Drift moderado
- AUC 0.65 - 0.75: Drift significativo
- AUC > 0.75: Drift severo

---

## 4. CENÁRIOS DE CONCEPT DRIFT

### 4.1 Cenário 1: Inversão de Sinal

**Sintoma:** Feature que era positiva torna-se negativa (ou vice-versa).

**Exemplo:** "Forma recente" passa de preditor de vitória para preditor de derrota.

**Possíveis causas:**
- Mudança tática no desporto
- Mercado ajusta-se ao padrão
- Overfitting a padrão temporário

**Impacto:** Modelo pode fazer predições completamente erradas.

### 4.2 Cenário 2: Perda de Relevância

**Sintoma:** Feature importante perde relevância (importância → 0).

**Exemplo:** "Vantagem casa" deixa de ser relevante em certas ligas.

**Possíveis causas:**
- Mudança no formato da competição
- Mudanças nas regras do desporto
- Adaptação do mercado

**Impacto:** Modelo torna-se menos informativo.

### 4.3 Cenário 3: Nova Feature Torna-se Relevante

**Sintoma:** Feature irrelevante torna-se importante.

**Exemplo:** "Estatísticas de possança" torna-se importante após mudança tática.

**Possíveis causas:**
- Evolução do desporto
- Novos dados disponíveis
- Mudança no que o mercado valoriza

**Impacto:** Modelo perde机会 por não usar a feature.

### 4.4 Cenário 4: Interação de Features Muda

**Sintoma:** Interação entre features muda (ex: forma + vantagem casa).

**Exemplo:** Antes: forma + vantagem casa = muito forte. Depois: forma + vantagem casa = moderado.

**Possíveis causas:**
- Mudança tática complexa
- Interações de mercado
- Mudanças não lineares

**Impacto:** Modelo linear ou com interações fixas falha.

---

## 5. PROCEDIMENTO DE DETEÇÃO

### 5.1 Coleta de Dados

**Conjunto de Referência:**
- Dados e outcomes do período de treino
- Período: últimos 3-6 meses
- Tamanho mínimo: 500 observações com outcomes

**Conjunto Atual:**
- Dados e outcomes recentes
- Período: última semana/mês
- Tamanho mínimo: 50 observações com outcomes

### 5.2 Frequência de Verificação

| Métrica | Frequência | Justificação |
|---------|------------|--------------|
| Performance (accuracy, AUC) | Semanal | Requer outcomes |
| EV (Expected Value) | Diária | Pode ser estimado |
| Feature importance | Semanal | Requer outcomes |
| Residual analysis | Semanal | Requer outcomes |
| Adversarial validation | Mensal | Computationally expensive |

### 5.3 Processo de Validação

1. **Coleta:** Extrair dados e outcomes de referência e atual
2. **Performance:** Calcular métricas de performance em ambos períodos
3. **Feature Importance:** Calcular importance em ambos períodos
4. **Residuals:** Analisar resíduos em ambos períodos
5. **Adversarial:** Executar adversarial validation
6. **Comparação:** Comparar com thresholds
7. **Alerta:** Gerar alertas se thresholds excedidos
8. **Logging:** Registar resultados para análise histórica

---

## 6. THRESHOLDS E ALERTAS

### 6.1 Thresholds por Métrica

| Métrica | INFO | WARNING | HIGH | CRITICAL |
|---------|------|---------|------|----------|
| Δ Accuracy | < 2% | 2 - 5% | 5 - 10% | > 10% |
| Δ AUC | < 0.02 | 0.02 - 0.05 | 0.05 - 0.10 | > 0.10 |
| Δ EV | < 10% | 10 - 15% | 15 - 30% | > 30% |
| Δ Feature importance | < 10% | 10 - 20% | 20 - 40% | > 40% |
| Δ Residual mean | < 0.01 | 0.01 - 0.02 | 0.02 - 0.05 | > 0.05 |
| Adversarial AUC | < 0.55 | 0.55 - 0.65 | 0.65 - 0.75 | > 0.75 |

### 6.2 Níveis de Alerta

| Nível | Condição | Ação |
|-------|----------|------|
| INFO | Qualquer métrica em INFO | Logging apenas |
| WARNING | ≥ 1 métrica em WARNING | Monitorizar de perto |
| HIGH | ≥ 1 métrica em HIGH | Preparar retraining |
| CRITICAL | ≥ 1 métrica em CRITICAL | Pausar apostas; investigar urgentemente |

---

## 7. ANÁLISE DE RESULTADOS

### 7.1 Diagnóstico de Concept Drift

Quando drift é detetado, investigar:
- **Tipo de drift:** Inversão de sinal? Perda de relevância? Nova feature?
- **Features afetadas:** Quais features mudaram mais?
- **Performance impact:** Quanto impacto na performance?
- **Causa raiz:** Mudança tática? Mudança de regras? Evolução de mercado?

### 7.2 Visualização

Criar visualizações para análise:
- Time series de performance (accuracy, AUC, EV)
- Bar charts de feature importance (ref vs atual)
- Scatter plots de SHAP values (ref vs atual)
- Residual plots ao longo do tempo
- Feature correlation heatmaps (ref vs atual)

### 7.3 Análise de Segmentação

Analisar drift por segmentos:
- Por tipo de aposta (moneyline, over/under, etc.)
- Por desporto (futebol, basquetebol, etc.)
- Por liga (Premier League, NBA, etc.)
- Por range de odds (low, medium, high)

**Objetivo:** Identificar se concept drift é generalizado ou específico.

### 7.4 Root Cause Analysis

Investigar causas potenciais:
- **Eventos externos:** Mudanças de regras, scandals, etc.
- **Mudanças táticas:** Novas estratégias dominantes
- **Evolução de mercado:** Bookmakers ajustam-se
- **Data quality:** Problemas na coleta de dados
- **Model degradation:** Overfitting, underfitting

---

## 8. INTEGRAÇÃO COM SISTEMA

### 8.1 Pipeline de Monitorização

1. **Prediction Logging:** Guardar todas as predições
2. **Outcome Tracking:** Guardar todos os outcomes
3. **Scheduler:** Executa verificações em frequência definida
4. **Performance Calculation:** Calcula métricas de performance
5. **Feature Importance:** Calcula importance periodicamente
6. **Drift Detection:** Executa testes de concept drift
7. **Alert Engine:** Envia alertas se thresholds excedidos
8. **Dashboard:** Atualiza visualizações
9. **Storage:** Guarda resultados históricos

### 8.2 Integração com Feature/Target Drift

Correlacionar concept drift com outros tipos:
- **Concept drift sem feature/target drift:** Mudança pura na relação
- **Concept drift com feature drift:** Features mudaram e causaram concept drift
- **Concept drift com target drift:** Target mudou e causou concept drift

### 8.3 Integração com Retraining

- Trigger automático de retraining quando:
  - Performance cai > 10% E adversarial AUC > 0.70
  - Feature importance muda > 40% para top features
- Shadow mode quando:
  - Performance cai > 5%
  - Adversarial AUC > 0.65

---

## 9. ESTRATÉGIAS DE MITIGAÇÃO

### 9.1 Retraining com Janela Deslizante

Treinar modelo apenas com dados recentes para capturar conceito atual.

**Vantagens:** Adapta-se a mudanças rapidamente.
**Desvantagens:** Perde contexto histórico; pode overfit a ruído recente.

### 9.2 Ensemble com Pesos Temporais

Usar ensemble de modelos treinados em diferentes períodos, com pesos baseados na performance recente.

**Vantagens:** Balanceia estabilidade e adaptabilidade.
**Desvantagens:** Mais complexo; requer tuning de pesos.

### 9.3 Feature Engineering Adaptativa

Adicionar features que capturam mudanças no conceito:
- Velocidade de mudança de features
- Interações temporais
- Features de "trend" vs "level"

**Vantagens:** Modelo pode aprender a adaptar-se.
**Desvantagens:** Mais complexidade; mais features.

---

## 10. MELHORIAS FUTURAS

- [ ] Implementar deteção de concept drift em tempo real
- [ ] Adicionar modelos de previsão de concept drift
- [ ] Implementar adaptive retraining (frequência ajusta-se ao drift)
- [ ] Desenvolver feature selection adaptativa
- [ ] Adicionar deteção de drift em interações de features

---

## 11. LINKS CRUZADOS

- [[48_Data_Drift/INDEX]] ← Secção mãe
- [[48_Data_Drift/DETECAO_FEATURE_DRIFT]] → Drift de features
- [[48_Data_Drift/DETECAO_PREDICTION_DRIFT]] → Drift de predições
- [[48_Data_Drift/DETECAO_TARGET_DRIFT]] → Drift de target
- [[48_Data_Drift/MITIGACAO_DRIFT]] → Resposta a drift
- [[11_MLOps/INDEX]] → Pipeline de retraining