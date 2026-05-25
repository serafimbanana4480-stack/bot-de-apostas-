# OVERFITTING_TESTS — Testes de Robustez e Validação Estatística

**ID:** `BT-002` | **Fase:** #phase/2 | **Owner:** Quant Research Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar testes estatísticos rigorosos para detetar overfitting em backtests de apostas desportivas. Overfitting é a segunda causa mais comum de falha em produção (após leakage), e os testes descritos aqui fornecem evidência estatística de que o modelo tem edge real e não apenas sorte ou overfitting aos dados históricos.

---

## 2. DEFINIÇÃO E IMPORTÂNCIA

### 2.1 O Que É Overfitting?

Overfitting ocorre quando um modelo aprende padrões específicos dos dados de treino que não generalizam para dados novos. Em backtesting, isto manifesta-se como:

- Performance excelente no treino mas pobre na validação/teste
- Sensibilidade extrema a pequenas mudanças nos hiperparâmetros
- Performance inconsistente across diferentes períodos temporais
- "Curve fitting" aos dados históricos específicos

### 2.2 Por Que É Crítico?

Um modelo overfitted passará no backtest (porque foi otimizado para esses dados) mas falhará catastroficamente em produção porque:

- Os padrões "aprendidos" são ruído, não sinal
- O modelo não generaliza para novos jogos/regimes
- Pequenas mudanças nas condições de mercado quebram o modelo
- O edge desaparece assim que o modelo encontra dados novos

**Custo de Overfitting:**
- Implementação de infraestrutura para um modelo sem edge
- Perda de capital real em apostas
- Tempo perdido em desenvolvimento e tuning
- Dano reputacional se for um serviço comercial

---

## 3. TESTES DE ROBUSTEZ

### 3.1 Train-Validation-Test Split Temporal

**Conceito:** Dividir os dados estritamente por tempo em três conjuntos independentes.

**Estrutura Recomendada:**
```
Treino:    36 meses (épocas 2018-19, 2019-20, 2020-21)
Validação: 12 meses (época 2021-22)
Teste:     12 meses (época 2022-23)
```

**Propósito:**
- **Treino:** Aprender parâmetros do modelo
- **Validação:** Tuning de hiperparâmetros (nunca usar teste para tuning!)
- **Teste:** Avaliação final, única, sem qualquer tuning adicional

**Critérios de Validação:**
- Performance em treino > validação > teste é esperado (degradação natural)
- Se treino >> validação: overfitting severo
- Se validação >> teste: overfitting de hiperparâmetros
- Gap > 20% entre treino e teste é sinal de alerta

### 3.2 Stability Across Folds

**Conceito:** Verificar que o modelo é consistente across diferentes períodos temporais.

**Implementação:**
- Usar purged walk-forward CV com 12 folds
- Calcular métricas (ROI, Sharpe, CLV) para cada fold
- Analisar distribuição das métricas across folds

**Métricas de Estabilidade:**
- **Coeficiente de variação (CV):** CV = std/mean das métricas
- **Range:** Min-max das métricas
- **Consistência:** % de folds com performance positiva

**Critérios de Passagem:**
- CV(ROI) < 0.5 (ROI não varia mais de 50% entre folds)
- Mínimo 8 de 12 folds com ROI > 0
- Sharpe positivo em pelo menos 10 de 12 folds
- CLV positivo em pelo menos 10 de 12 folds

### 3.3 Feature Importance Stability

**Conceito:** Verificar que as features mais importantes são consistentes across folds.

**Implementação:**
- Calcular feature importance (SHAP ou gain) para cada fold
- Ranking das top 10 features por fold
- Calcular estabilidade do ranking (ex: Kendall's tau)

**Critérios de Validação:**
- Top 5 features consistentes em ≥ 8 dos 12 folds
- Correlação de ranking > 0.6 entre folds adjacentes
- Nenhuma feature com importância > 80% (sinal de leakage)

**Sinais de Alerta:**
- Features diferentes dominando em folds diferentes (instabilidade)
- Uma feature com importância > 90% (provável leakage)
- Ranking completamente aleatório entre folds (modelo instável)

### 3.4 Hyperparameter Sensitivity Analysis

**Conceito:** Verificar que o modelo não é excessivamente sensível a pequenas mudanças nos hiperparâmetros.

**Implementação:**
- Variar cada hiperparâmetro ±10% do valor ótimo
- Recalcular performance em validação
- Analisar sensibilidade (delta performance / delta parâmetro)

**Critérios de Validação:**
- Performance não deve cair mais de 20% com ±10% de variação
- Não deve haver "cliffs" (quedas abruptas de performance)
- Curva de performance deve ser suave em torno do ótimo

**Sinais de Alerta:**
- Pequenas mudanças causam grandes quedas de performance
- Múltiplos picos locais de performance (overfitting)
- Performance muito específica a valores exatos de parâmetros

---

## 4. RANDOMIZATION TESTS

### 4.1 Label Randomization Test

**Conceito:** Permutar aleatoriamente os labels (resultados dos jogos) e verificar se o modelo ainda tem "performance".

**Implementação:**
1. Manter features inalteradas
2. Permutar aleatoriamente os resultados dos jogos
3. Treinar modelo com dados permutados
4. Calcular métricas (ROI, Sharpe, accuracy)
5. Repetir 1000 vezes para criar distribuição nula

**Interpretação:**
- Modelo real deve estar no percentil 95+ da distribuição nula
- Se modelo permutado tem performance similar → overfitting ou leakage
- Gap entre real e nula deve ser estatisticamente significativo (p < 0.05)

**Exemplo:**
```
Modelo real: ROI = 7%, Sharpe = 0.8
Modelo permutado (média): ROI = -2%, Sharpe = -0.1
Modelo permutado (percentil 95): ROI = 1%, Sharpe = 0.2

Conclusão: Modelo real está bem acima da distribuição nula → evidência de edge real
```

### 4.2 Feature Randomization Test

**Conceito:** Permutar individualmente cada feature e verificar impacto na performance.

**Implementação:**
1. Para cada feature:
   - Permutar aleatoriamente os valores
   - Treinar modelo e calcular performance
   - Comparar com performance baseline
2. Features importantes devem causar grande queda ao serem permutadas
3. Features irrelevantes não devem afetar performance

**Interpretação:**
- Feature importante: performance cai > 20% quando permutada
- Feature irrelevante: performance muda < 5%
- Feature suspeita: performance MELHORA quando permutada (overfitting)

### 4.3 Time Block Randomization

**Conceito:** Permutar blocos de tempo (ex: semanas) em vez de observações individuais.

**Implementação:**
1. Dividir dados em blocos temporais (ex: semanas)
2. Permutar aleatoriamente a ordem dos blocos
3. Treinar modelo e calcular performance
4. Repetir 1000 vezes

**Propósito:**
- Preserva estrutura temporal dentro de blocos
- Destrui estrutura temporal entre blocos
- Mais realista que permutação individual

**Interpretação:**
- Similar ao label randomization test
- Modelo real deve estar no percentil 95+ da distribuição nula

---

## 5. WHITE'S REALITY CHECK

### 5.1 Conceito Teórico

White's Reality Check (WRC) é um teste estatístico desenvolvido por Halbert White para determinar se uma estratégia de trading tem desempenho estatisticamente significativo acima do que seria esperado por sorte.

**Questão que Responde:** "A performance observada é estatisticamente significativa, ou poderia ter sido obtida por sorte?"

### 5.2 Implementação

**Passo 1: Definir a Estatística de Teste**
- Usar uma métrica de performance (ex: retorno acumulado)
- Calcular valor observado nos dados reais

**Passo 2: Bootstrapping**
1. Gerar amostras bootstrap dos retornos
2. Calcular a estatística de teste para cada amostra
3. Criar distribuição bootstrap da estatística

**Passo 3: Calcular p-value**
- p-value = proporção de amostras bootstrap com estatística ≥ observada
- p-value < 0.05 indica significância estatística

**Passo 4: Ajuste por Múltiplas Estratégias**
- Se testando múltiplas estratégias, ajustar p-value
- Controlar Family-Wise Error Rate (FWER)

### 5.3 Interpretação

**Resultado Significativo (p < 0.05):**
- Evidência estatística de edge real
- Performance improvável de ser obtida por sorte
- Pode considerar implementação

**Resultado Não Significativo (p ≥ 0.05):**
- Não há evidência estatística de edge
- Performance pode ser devida a sorte
- Requerer mais dados ou revisão do modelo

### 5.4 Limitações

- **Assume i.i.d.:** Retornos devem ser independentes e identicamente distribuídos
- **Power limitada:** Requer amostra grande para detetar edge pequeno
- **Sensível a outliers:** Retornos extremos podem distorcer resultados
- **Não deteta leakage:** Um modelo com leakage pode passar no WRC

**Melhoria:**
- Use **Stationary Bootstrap** para lidar com autocorrelação
- Combine com outros testes (randomization, feature importance)
- Use como parte de um framework mais amplo de validação

---

## 6. OUTROS TESTES IMPORTANTES

### 6.1 Out-of-Sample Decay Test

**Conceito:** Verificar se performance degrada gradualmente com distância temporal do treino.

**Implementação:**
- Dividir dados de teste em buckets temporais (ex: trimestres)
- Calcular performance para cada bucket
- Analisar tendência temporal

**Interpretação:**
- **Decay suave (5-10% por ano):** Normal, degradação natural
- **Decay rápido (>20% em 6 meses):** Overfitting ou regime shift
- **Sem decay ou melhoria:** Suspeito, possivelmente leakage

### 6.2 Regime Stability Test

**Conceito:** Verificar performance em diferentes regimes de mercado.

**Implementação:**
- Identificar regimes (ex: pré-COVID, COVID, pós-COVID)
- Calcular performance separada por regime
- Comparar performance entre regimes

**Interpretação:**
- **Performance consistente:** Modelo robusto a regime shifts
- **Performance muito variável:** Modelo overfitted a regime específico
- **Zero performance em regime novo:** Modelo não generaliza

### 6.3 Subsampling Test

**Conceito:** Verificar que performance não depende de um subconjunto específico de dados.

**Implementação:**
1. Amostrar aleatoriamente 80% dos dados (sem reposição)
2. Treinar modelo e calcular performance
3. Repetir 100 vezes
4. Analisar distribuição de performance

**Interpretação:**
- **Distribuição estreita (CV < 0.3):** Modelo robusto
- **Distribuição larga (CV > 0.5):** Modelo sensível a dados específicos
- **Performance negativa em algumas amostras:** Overfitting severo

---

## 7. FRAMEWORK DE VALIDAÇÃO COMPLETO

### 7.1 Pipeline Sugerido

```
1. VALIDAÇÃO BÁSICA
   ├── Train-validation-test split temporal
   ├── Gap analysis (treino vs validação vs teste)
   └── Performance acima de thresholds mínimos

2. ESTABILIDADE TEMPORAL
   ├── Walk-forward CV (12 folds)
   ├── Stability across folds (CV < 0.5)
   └── Feature importance consistency

3. RANDOMIZATION TESTS
   ├── Label randomization (percentil 95+)
   ├── Feature randomization
   └── Time block randomization

4. WHITE'S REALITY CHECK
   ├── Bootstrap da distribuição de retornos
   ├── Calcular p-value
   └── Ajuste por múltiplas comparações

5. ROBUSTEZ ADICIONAL
   ├── Hyperparameter sensitivity
   ├── Out-of-sample decay
   ├── Regime stability
   └── Subsampling test

6. AUDIT FINAL
   ├── Revisar todos os resultados
   ├── Documentar decisões
   └── Aprovar/rejeitar para produção
```

### 7.2 Critérios de Passagem

O modelo passa na validação se:

✅ **Gap aceitável:** Treino > validação > teste, mas gap < 30%
✅ **Estabilidade:** CV(ROI) < 0.5, 8/12 folds positivos
✅ **Feature importance:** Top 5 consistentes em 8/12 folds
✅ **Label randomization:** Modelo no percentil 95+ da distribuição nula
✅ **White's Reality Check:** p-value < 0.05
✅ **Hyperparameter sensitivity:** Performance cai < 20% com ±10% variação
✅ **Regime stability:** Performance positiva em todos os regimes
✅ **Subsampling:** CV < 0.3 na distribuição de performance

**Se qualquer critério falhar:**
- Investigar causa (overfitting, leakage, regime shift)
- Corrigir problema
- Re-executar validação completa
- Não aprovar para produção sem passar em todos os critérios

---

## 8. EXEMPLOS PRÁTICOS

### 8.1 Caso de Estudo: Modelo Overfitted

**Sintomas:**
- Treino: ROI = 15%, Sharpe = 1.5
- Validação: ROI = 8%, Sharpe = 0.8
- Teste: ROI = -2%, Sharpe = -0.3
- Gap treino-teste = 17% (crítico)

**Randomization Test:**
- Modelo real: ROI = -2%
- Modelo permutado (média): ROI = -3%
- Modelo permutado (percentil 95): ROI = -1%
- Modelo real está no percentil 40 (não significativo)

**Conclusão:** Modelo severamente overfitted, não tem edge real

**Ação:** Revisar feature engineering, simplificar modelo, reduzir complexidade

### 8.2 Caso de Estudo: Modelo Robusto

**Sintomas:**
- Treino: ROI = 8%, Sharpe = 0.9
- Validação: ROI = 6%, Sharpe = 0.7
- Teste: ROI = 5%, Sharpe = 0.6
- Gap treino-teste = 3% (aceitável)

**Stability Across Folds:**
- Mean ROI = 6.2%, Std ROI = 2.1%, CV = 0.34
- 10/12 folds com ROI > 0
- Top 5 features consistentes em 10/12 folds

**Randomization Test:**
- Modelo real: ROI = 5%, Sharpe = 0.6
- Modelo permutado (média): ROI = -2%, Sharpe = -0.1
- Modelo permutado (percentil 95): ROI = 1%, Sharpe = 0.2
- Modelo real está no percentil 98 (significativo)

**White's Reality Check:** p-value = 0.02 (significativo)

**Conclusão:** Modelo robusto com evidência estatística de edge real

**Ação:** Aprovar para paper trading e eventual produção

### 8.3 Caso de Estudo: Modelo com Leakage

**Sintomas:**
- Treino: ROI = 20%, Sharpe = 2.0
- Validação: ROI = 18%, Sharpe = 1.8
- Teste: ROI = 17%, Sharpe = 1.7
- Gap treino-teste = 3% (parece aceitável)

**Feature Importance:**
- Feature "closing_line_value" = 95% de importância
- Todas as outras features = < 1%

**Randomization Test:**
- Modelo real: ROI = 17%, Sharpe = 1.7
- Modelo permutado (média): ROI = -2%, Sharpe = -0.1
- Modelo permutado (percentil 95): ROI = 0%, Sharpe = 0.1
- Modelo real está no percentil 99 (muito significativo)

**Conclusão:** Modelo passa nos testes mas tem feature com 95% de importância → provável leakage

**Ação:** Investigar feature "closing_line_value", verificar se está disponível no momento da predição, remover se necessário

---

## 9. REFERÊNCIAS E BOAS PRÁTICAS

### 9.1 Literatura Recomendada

- **"Advances in Financial Machine Learning"** — Marcos Lopez de Prado (Capítulo 11 sobre Backtesting)
- **"A Reality Check for Data Snooping"** — Halbert White (2000)
- **"Pseudo-Mathematics and Financial Charlatanism"** — Bailey et al. (2014)
- **"Evidence-Based Technical Analysis"** — David Aronson (2006)

### 9.2 Ferramentas Úteis

- **Scikit-learn:** TimeSeriesSplit, permutation_test_score
- **Statsmodels:** Testes estatísticos
- **Custom implementations:** White's Reality Check, Stationary Bootstrap
- **SHAP:** Feature importance e interpretabilidade

### 9.3 Regras de Ouro

1. **Nunca confiar num único teste:** Use um framework completo de validação
2. **Overfitting é mais comum que leakage:** Teste extensivamente para ambos
3. **Simplicidade é virtude:** Modelos simples tendem a ser mais robustos
4. **Documente tudo:** Mantenha registro de todos os testes e resultados
5. **Seja conservador:** Rejeitar modelos marginais é melhor que aceitar modelos falsos

---

## 10. LINKS CRUZADOS

- [[06_Backtesting/INDEX]] ← Secção mãe
- [[06_Backtesting/LEAKAGE_TEMPORAL]] → Detecção de leakage
- [[06_Backtesting/MULTIPLE_TESTING_CORRECTION]] → Ajuste por múltiplas comparações
- [[05_Machine_Learning/INDEX]] → Modelagem e feature engineering
- [[03_Quant_Research/INDEX]] → Fundamentos estatísticos

---

## 11. GLOSSÁRIO

- **Overfitting:** Modelo aprende ruído específico dos dados de treino
- **Generalização:** Capacidade do modelo performar bem em dados novos
- **Randomization test:** Teste que permuta dados para criar distribuição nula
- **White's Reality Check:** Teste estatístico para validar performance de estratégias
- **Bootstrap:** Método de reamostragem para estimar distribuições
- **p-value:** Probabilidade de observar resultado extremo assumindo hipótese nula
- **Stationary Bootstrap:** Bootstrap que preserva estrutura temporal
- **Regime shift:** Mudança fundamental nas condições de mercado