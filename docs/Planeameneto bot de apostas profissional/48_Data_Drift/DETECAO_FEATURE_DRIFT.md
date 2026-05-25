# DETECAO_FEATURE_DRIFT — Monitorização de Distribuição de Features

**ID:** `DRIFT-001` | **Fase:** #phase/6 | **Owner:** Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Detetar mudanças significativas na distribuição das features de entrada do modelo de value betting, indicando que os dados utilizados para treino podem não representar mais a realidade atual do mercado de apostas.

---

## 2. CONTEXTO

Em sistemas de value betting, as features (variáveis de entrada) podem mudar ao longo do tempo devido a:
- Alterações nas regras dos desportos
- Mudanças nos padrões de apostas dos bookmakers
- Evolução das estratégias de mercado
- Eventos externos (pandemias, scandals, etc.)

Quando a distribuição das features muda significativamente, o modelo treinado com dados antigos pode produzir predições incorretas, levando a perdas financeiras.

---

## 3. MÉTRICAS DE DETEÇÃO

### 3.1 Population Stability Index (PSI)

O PSI mede a estabilidade da distribuição de uma feature entre o conjunto de referência (dados de treino) e o conjunto atual (dados recentes).

**Cálculo:**
1. Dividir a feature em bins (tipicamente 10-20)
2. Calcular a percentagem de observações em cada bin para referência e atual
3. Aplicar fórmula: PSI = Σ (atual - referência) × ln(atual / referência)

**Interpretação:**
- PSI < 0.10: Drift insignificante
- PSI 0.10 - 0.20: Drift moderado (monitorizar)
- PSI 0.20 - 0.30: Drift significativo (preparar retraining)
- PSI > 0.30: Drift crítico (ação imediata necessária)

### 3.2 Kolmogorov-Smirnov (KS) Test

Teste estatístico não-paramétrico que compara duas distribuições contínuas.

**Interpretação:**
- p-value < 0.01: Distribuições significativamente diferentes (drift detetado)
- p-value ≥ 0.01: Sem evidência de drift estatístico

**Vantagens:**
- Não requer binning (ao contrário do PSI)
- Sensível a diferenças na forma da distribuição
- Adequado para features contínuas

### 3.3 Comparação de Estatísticas

Comparar estatísticas descritivas entre referência e atual:
- Média e mediana
- Desvio padrão
- Quartis (25%, 50%, 75%)
- Valores mínimos e máximos

**Thresholds:**
- Mudança > 2 desvios padrão na média: alerta
- Mudança > 25% no desvio padrão: alerta

---

## 4. FEATURES CRÍTICAS PARA MONITORIZAR

### 4.1 Features com Maior Impacto

Priorizar monitorização das features com:
- Maior importância no modelo (feature importance)
- Maior variabilidade histórica
- Maior impacto no valor esperado (EV)

### 4.2 Categorias de Features

| Categoria | Exemplos | Frequência de Verificação |
|-----------|----------|---------------------------|
| **Odds** | Odds home, odds away, odds draw | Diária |
| **Histórico** | Forma recente, head-to-head | Semanal |
| **Estatísticas** | Goals, shots, possession | Semanal |
| **Mercado** | Volume de apostas, movimento de odds | Diária |
| **Contexto** | Lesões, clima, motivação | Por jogo |

---

## 5. PROCEDIMENTO DE DETEÇÃO

### 5.1 Coleta de Dados

**Conjunto de Referência:**
- Dados utilizados no último treino do modelo
- Período típico: últimos 3-6 meses
- Tamanho mínimo: 1000 observações

**Conjunto Atual:**
- Dados mais recentes (última semana/mês)
- Período: janela deslizante de 7-30 dias
- Tamanho mínimo: 100 observações

### 5.2 Frequência de Verificação

| Feature | Frequência | Justificação |
|---------|------------|--------------|
| Odds | Diária | Mudam rapidamente |
| Estatísticas de equipa | Semanal | Mudam mais lentamente |
| Contexto (lesões, etc.) | Por jogo | Event-driven |
| Volume de mercado | Diária | Indicador de atividade |

### 5.3 Processo de Validação

1. **Coleta:** Extrair dados de referência e atual
2. **Limpeza:** Remover outliers e valores missing
3. **Cálculo:** Calcular PSI, KS test e estatísticas para cada feature
4. **Comparação:** Comparar com thresholds definidos
5. **Alerta:** Gerar alertas se thresholds excedidos
6. **Logging:** Registar resultados para análise histórica

---

## 6. THRESHOLDS E ALERTAS

### 6.1 Thresholds por Feature

Diferentes features podem ter thresholds diferentes baseados em:
- Volatilidade histórica
- Importância no modelo
- Sensibilidade a mudanças externas

**Exemplo de Configuração:**
```
odds_home: PSI_threshold = 0.15 (mais volátil)
team_form: PSI_threshold = 0.25 (mais estável)
goals_avg: PSI_threshold = 0.20 (padrão)
```

### 6.2 Níveis de Alerta

| PSI | Nível | Ação |
|-----|-------|------|
| < 0.10 | INFO | Logging apenas |
| 0.10 - 0.20 | WARNING | Monitorizar de perto |
| 0.20 - 0.30 | HIGH | Preparar retraining |
| > 0.30 | CRITICAL | Pausar apostas; investigar |

---

## 7. ANÁLISE DE RESULTADOS

### 7.1 Diagnóstico de Drift

Quando drift é detetado, investigar:
- **Causa externa:** Mudanças de regras, eventos externos?
- **Causa técnica:** Erro na coleta de dados, mudança no schema?
- **Causa natural:** Evolução normal do mercado?

### 7.2 Visualização

Criar visualizações para análise:
- Histogramas comparativos (referência vs atual)
- Boxplots side-by-side
- Time series de PSI ao longo do tempo
- Heatmap de drift por feature e período

### 7.3 Relatório

Gerar relatório semanal com:
- Features com drift detetado
- Valores de PSI e KS test
- Tendências (melhorando/piorando)
- Recomendações de ação

---

## 8. INTEGRAÇÃO COM SISTEMA

### 8.1 Pipeline de Monitorização

1. **Scheduler:** Executa verificações em frequência definida
2. **Data Extraction:** Coleta dados de referência e atual
3. **Drift Detection:** Calcula métricas de drift
4. **Alert Engine:** Envia alertas se thresholds excedidos
5. **Dashboard:** Atualiza visualizações em tempo real
6. **Storage:** Guarda resultados históricos

### 8.2 Integração com Retraining

- Trigger automático de retraining quando PSI > 0.25
- Shadow mode quando PSI > 0.20
- Notificação ao time de MLOps para análise manual

---

## 9. MELHORIAS FUTURAS

- [ ] Implementar deteção de drift multivariado (não apenas univariado)
- [ ] Adicionar deteção de drift em tempo real para features críticas
- [ ] Desenvolver modelos preditivos de drift (antecipar mudanças)
- [ ] Implementar adaptive thresholds (ajustam automaticamente)
- [ ] Adicionar deteção de drift em features categóricas (Chi-square test)

---

## 10. LINKS CRUZADOS

- [[48_Data_Drift/INDEX]] ← Secção mãe
- [[48_Data_Drift/DETECAO_PREDICTION_DRIFT]] → Drift de predições
- [[48_Data_Drift/DETECAO_CONCEPT_DRIFT]] → Drift de conceito
- [[48_Data_Drift/MITIGACAO_DRIFT]] → Resposta a drift
- [[11_MLOps/INDEX]] → Pipeline de retraining