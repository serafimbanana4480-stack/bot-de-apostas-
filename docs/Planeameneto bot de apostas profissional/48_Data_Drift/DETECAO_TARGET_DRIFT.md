# DETECAO_TARGET_DRIFT — Monitorização de Distribuição de Outcomes

**ID:** `DRIFT-003` | **Fase:** #phase/6 | **Owner:** Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Detetar mudanças significativas na distribuição dos outcomes reais (resultados dos jogos), indicando que o target do modelo está a mudar, o que pode afetar a performance do modelo mesmo que as features permaneçam estáveis.

---

## 2. CONTEXTO

Target drift ocorre quando:
- A distribuição de resultados (vitórias, empates, derrotas) muda
- A taxa de vitória média muda sistematicamente
- A variância dos outcomes muda

Isso pode indicar:
- Mudanças no desporto (regras, formatos)
- Mudanças na competitividade das ligas
- Eventos externos afetando resultados
- Mudanças sazonais

**Importância:** Mesmo que o modelo seja perfeito, se o target mudar, as predições podem ficar incorretas.

---

## 3. MÉTRICAS DE DETEÇÃO

### 3.1 Proporção de Classes

Para problemas de classificação (ex: vitória/empate/derrota):

**Métricas:**
- **Proporção de vitórias:** % de jogos com vitória da equipa casa
- **Proporção de empates:** % de jogos com empate
- **Proporção de derrotas:** % de jogos com vitória da equipa visitante

**Thresholds:**
- Mudança > 2% na proporção: WARNING
- Mudança > 5% na proporção: HIGH
- Mudança > 10% na proporção: CRITICAL

### 3.2 Chi-Square Test

Teste estatístico para comparar distribuições categóricas.

**Aplicação:**
- Comparar distribuição de outcomes entre referência e atual
- Teste de independência entre período e outcome

**Interpretação:**
- p-value < 0.01: Distribuições significativamente diferentes (drift detetado)
- p-value ≥ 0.01: Sem evidência de drift estatístico

### 3.3 Taxa de Vitória Média

Para problemas de regressão (ex: golos, pontos):

**Métricas:**
- **Média de golos:** Média de golos por jogo
- **Média de pontos:** Média de pontos por jogo
- **Desvio padrão:** Variabilidade dos outcomes

**Thresholds:**
- Mudança > 0.2 golos/jogo: WARNING
- Mudança > 0.5 golos/jogo: CRITICAL
- Mudança > 15% no desvio padrão: WARNING

### 3.4 PSI em Outcomes

Aplicar PSI na distribuição de outcomes (se contínuos) ou em buckets de outcomes.

**Configuração:**
- Para contínuos: 10 bins baseados em quantis
- Para categóricos: PSI não aplicável (usar Chi-square)
- Threshold PSI: 0.15

---

## 4. CENÁRIOS DE TARGET DRIFT

### 4.1 Cenário 1: Aumento de Empates

**Sintoma:** Proporção de empates aumenta significativamente.

**Possíveis causas:**
- Mudanças táticas (equipas mais defensivas)
- Mudanças nas regras (ex: VAR no futebol)
- Aumento da competitividade da liga

**Impacto:** Modelo pode subestimar probabilidade de empate.

### 4.2 Cenário 2: Shift para Vitórias Casa

**Sintoma:** Proporção de vitórias casa aumenta.

**Possíveis causas:**
- Vantagem casa aumentando (público, viagens)
- Mudanças no calendário (mais jogos em casa)
- Desequilíbrio competitivo

**Impacto:** Modelo pode subestimar vantagem casa.

### 4.3 Cenário 3: Aumento de Variabilidade

**Sintoma:** Desvio padrão de outcomes aumenta.

**Possíveis causas:**
- Maior paridade entre equipas
- Mudanças no formato da competição
- Eventos externos (lesões, clima)

**Impacto:** Modelo pode ficar subcalibrado (confiança excessiva).

---

## 5. PROCEDIMENTO DE DETEÇÃO

### 5.1 Coleta de Dados

**Conjunto de Referência:**
- Outcomes históricos utilizados no treino
- Período: últimos 6-12 meses
- Tamanho mínimo: 1000 jogos

**Conjunto Atual:**
- Outcomes mais recentes
- Período: última semana/mês
- Tamanho mínimo: 50 jogos

### 5.2 Frequência de Verificação

| Métrica | Frequência | Justificação |
|---------|------------|--------------|
| Proporção de classes | Semanal | Requer amostra suficiente |
| Chi-square test | Semanal | Requer amostra suficiente |
| Taxa de vitória média | Diária | Pode ser calculada com menos dados |
| PSI em outcomes | Semanal | Requer amostra suficiente |

### 5.3 Processo de Validação

1. **Coleta:** Extrair outcomes de referência e atual
2. **Cálculo:** Calcular proporções de classes
3. **Chi-square:** Aplicar teste de independência
4. **PSI:** Calcular PSI se outcomes contínuos
5. **Comparação:** Comparar com thresholds
6. **Alerta:** Gerar alertas se thresholds excedidos
7. **Logging:** Registar resultados para análise histórica

---

## 6. THRESHOLDS E ALERTAS

### 6.1 Thresholds por Métrica

| Métrica | INFO | WARNING | HIGH | CRITICAL |
|---------|------|---------|------|----------|
| Δ Proporção classe | < 1% | 1 - 2% | 2 - 5% | > 5% |
| Chi-square p-value | > 0.05 | 0.01 - 0.05 | 0.001 - 0.01 | < 0.001 |
| Δ Média outcomes | < 0.1 | 0.1 - 0.2 | 0.2 - 0.5 | > 0.5 |
| Δ Desvio padrão | < 10% | 10 - 15% | 15 - 25% | > 25% |
| PSI outcomes | < 0.05 | 0.05 - 0.15 | 0.15 - 0.25 | > 0.25 |

### 6.2 Níveis de Alerta

| Nível | Condição | Ação |
|-------|----------|------|
| INFO | Qualquer métrica em INFO | Logging apenas |
| WARNING | ≥ 1 métrica em WARNING | Monitorizar de perto |
| HIGH | ≥ 1 métrica em HIGH | Preparar retraining |
| CRITICAL | ≥ 1 métrica em CRITICAL | Pausar apostas; investigar |

---

## 7. ANÁLISE DE RESULTADOS

### 7.1 Diagnóstico de Target Drift

Quando drift é detetado, investigar:
- **Causa externa:** Mudanças de regras, eventos?
- **Causa sazonal:** Padrão sazonal esperado?
- **Causa estrutural:** Mudança permanente no desporto?
- **Causa amostral:** Amostra muito pequena ou não representativa?

### 7.2 Visualização

Criar visualizações para análise:
- Bar charts de proporções de classes (ref vs atual)
- Time series de proporções ao longo do tempo
- Histogramas de outcomes contínuos
- Boxplots de outcomes por período
- Heatmap de outcomes por liga e período

### 7.3 Análise de Segmentação

Analisar drift por segmentos:
- Por desporto (futebol, basquetebol, etc.)
- Por liga (Premier League, La Liga, etc.)
- Por época (primeira volta, segunda volta)
- Por tipo de competição (liga, taça, europeia)

**Objetivo:** Identificar se drift é generalizado ou específico a certos segmentos.

### 7.4 Correlação com Eventos

Correlacionar drift com eventos externos:
- Mudanças de regras
- Eventos de calendário (férias, internacional breaks)
- Eventos externos (pandemias, scandals)
- Mudanças nos formatos das competições

---

## 8. INTEGRAÇÃO COM SISTEMA

### 8.1 Pipeline de Monitorização

1. **Outcome Tracking:** Guardar todos os outcomes reais
2. **Scheduler:** Executa verificações em frequência definida
3. **Drift Detection:** Calcula métricas de target drift
4. **Alert Engine:** Envia alertas se thresholds excedidos
5. **Dashboard:** Atualiza visualizações
6. **Storage:** Guarda resultados históricos

### 8.2 Integração com Feature/Prediction Drift

Correlacionar target drift com outros tipos de drift:
- **Target drift sem feature drift:** Possível concept drift
- **Target drift com feature drift:** Features explicam mudança no target
- **Target drift com prediction drift:** Modelo pode estar a reagir corretamente

### 8.3 Integração com Retraining

- Trigger automático de retraining quando:
  - Chi-square p-value < 0.001 E proporção muda > 5%
  - Mudança estrutural confirmada (não sazonal)
- Shadow mode quando:
  - Chi-square p-value < 0.01
  - Proporção muda > 2%

---

## 9. CONSIDERAÇÕES ESPECIAIS

### 9.1 Sazonalidade

Alguns desportos têm padrões sazonais naturais:
- Primeira vs segunda volta (futebol)
- Playoffs vs regular season (NBA/NFL)
- Diferentes épocas podem ter características diferentes

**Recomendação:** Usar conjunto de referência da mesma época do ano.

### 9.2 Tamanho da Amostra

Target drift requer amostras suficientes para deteção confiável:
- Mínimo 50 jogos para análise semanal
- Mínimo 100 jogos para análise mensal
- Mais jogos → maior poder estatístico

### 9.3 Lag de Informação

Outcomes só disponíveis após o jogo:
- Não é possível detetar target drift em tempo real
- Detecção sempre retrospective (após outcomes conhecidos)
- Usar para validação de modelo, não para decisão em tempo real

---

## 10. MELHORIAS FUTURAS

- [ ] Implementar deteção de target drift por liga individualmente
- [ ] Adicionar modelos de previsão de target drift (antecipar mudanças)
- [ ] Implementar adaptive thresholds baseados em variabilidade histórica
- [ ] Adicionar deteção de drift em outcomes específicos (ex: golos específicos)
- [ ] Integrar com análise de mercado (comparar com odds de bookmakers)

---

## 11. LINKS CRUZADOS

- [[48_Data_Drift/INDEX]] ← Secção mãe
- [[48_Data_Drift/DETECAO_FEATURE_DRIFT]] → Drift de features
- [[48_Data_Drift/DETECAO_PREDICTION_DRIFT]] → Drift de predições
- [[48_Data_Drift/DETECAO_CONCEPT_DRIFT]] → Drift de conceito
- [[48_Data_Drift/MITIGACAO_DRIFT]] → Resposta a drift
- [[11_MLOps/INDEX]] → Pipeline de retraining