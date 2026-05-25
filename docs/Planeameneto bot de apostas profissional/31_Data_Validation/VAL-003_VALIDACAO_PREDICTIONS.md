# VAL-003 — Validação de Predictions

**ID:** `VAL-003` | **Fase:** #phase/5 | **Owner:** Data Engineer | **Status:** #status/in_progress

---

## 1. OBJETIVO

Definir estratégias e procedimentos para validar a qualidade e integridade das predictions geradas pelos modelos de Machine Learning. Predictions são o output dos modelos e a base para a deteção de value bets. Validações inadequadas podem levar a:
- Apostas com valor falso (negative EV disfarçado de positive EV)
- Overfitting não detetado
- Calibração incorreta das probabilidades
- Perdas financeiras significativas

---

## 2. CONTEXTO

As predictions são probabilidades ou valores numéricos gerados por modelos treinados em dados históricos. A validação deve garantir que:
1. As predictions estão dentro de bounds razoáveis
2. As predictions estão calibradas (probabilidades refletem realidade)
3. As predictions são consistentes ao longo do tempo
4. As predictions não têm bias sistemático

A validação de predictions deve ocorrer após a inferência e antes da deteção de value bets.

---

## 3. ESCOPO

Este documento abrange a validação de:
- **Predictions de probabilidade**: Probabilidade de um resultado (ex: P(home_win))
- **Predictions de spread**: Margem de vitória esperada
- **Predictions de totals**: Total de pontos esperado
- **Predictions de player props**: Estatísticas esperadas de jogadores
- **Predictions de valor**: Expected value (EV) de uma aposta

---

## 4. VALIDAÇÃO DE BOUNDS

### 4.1. Bounds para Predictions de Probabilidade

**Bounds gerais:**
- Probabilidade deve estar em [0.0, 1.0]
- Alerta se probabilidade < 0.01 ou > 0.99 (extrema confiança)

**Bounds por tipo de prediction:**
- Moneyline home: P(home_win) ∈ [0.10, 0.90]
- Moneyline away: P(away_win) = 1 - P(home_win)
- Spread cover: P(spread_cover) ∈ [0.20, 0.80]
- Totals over/under: P(over) ∈ [0.30, 0.70]

**Justificativa:**
- Probabilidades extremas indicam overfitting ou erro de modelo
- NBA tem paridade relativamente alta
- Margem de erro deve ser considerada

### 4.2. Bounds para Predictions de Spread

**Bounds gerais:**
- Spread prediction deve estar entre -30 e +30 pontos
- Alerta se |spread| > 20 (margem extrema)

**Bounds por contexto:**
- Regular season: |spread| < 15 na maioria dos casos
- Playoffs: |spread| pode chegar a 20 em matchups desiguais
- Overtime: spread pode ser mais extremo

**Validação de consistência:**
- Spread prediction deve ser consistente com probabilidade de vitória
- Ex: spread de -10 deve corresponder a P(home_win) ~ 0.75
- Usar curva de conversão histórica para validar

### 4.3. Bounds para Predictions de Totals

**Bounds gerais:**
- Total prediction deve estar entre 180 e 260 pontos
- Alerta se total < 190 ou > 250 (extremos)

**Bounds por contexto:**
- Regular season: média ~ 225 pontos
- Playoffs: média ~ 215 pontos (defesa mais intensa)
- Overtime: total pode ser 5-15 pontos maior

**Validação de consistência:**
- Total prediction deve aproximar soma de team_points_predictions
- Tolerância: ± 5 pontos
- Alertar se discrepância > 10 pontos

### 4.4. Bounds para Predictions de Player Props

**Bounds por estatística:**
- Points: 0-50 (recorde individual: 81)
- Rebounds: 0-25 (recorde individual: 55)
- Assists: 0-20 (recorde individual: 30)
- 3-pointers made: 0-15 (recorde individual: 14)

**Bounds por contexto:**
- Role do jogador (star vs role player)
- Minutos esperados (starter vs bench)
- matchup defensivo

**Validação de consistência:**
- Player prop prediction deve ser ≤ team prediction contribution
- Ex: player_pts_prediction ≤ team_pts_prediction × (player_minutes / team_minutes)
- Alertar se discrepância > 20%

### 4.5. Bounds para Predictions de Valor (EV)

**Bounds gerais:**
- EV deve estar entre -20% e +30%
- Alerta se EV < -10% (negative EV extremo) ou EV > +20% (value extremo)

**Bounds por tipo de aposta:**
- Moneyline: EV ∈ [-15%, +25%]
- Spread: EV ∈ [-10%, +20%]
- Totals: EV ∈ [-10%, +20%]
- Player props: EV ∈ [-20%, +30%] (mais volátil)

**Validação de consistência:**
- EV deve ser consistente com probabilidade e odd
- EV = (probabilidade × payout) - stake
- Alertar se EV calculado inconsistente com EV prediction

---

## 5. VALIDAÇÃO DE CALIBRAÇÃO

### 5.1. Conceito de Calibração

**Definição:**
- Uma prediction está calibrada se a probabilidade prevista corresponde à frequência real
- Ex: Se modelo prevê P=0.7 para 100 jogos, deve haver ~70 vitórias

**Importância:**
- Predictions não calibradas levam a apostas com EV incorreto
- Overconfiança (P alto, win rate baixo) = perdas
- Subconfiança (P baixo, win rate alto) = oportunidades perdidas

### 5.2. Métricas de Calibração

**Reliability Diagram:**
- Gráfico de probabilidade prevista vs frequência real
- Curva ideal: linha diagonal y=x
- Desvio da diagonal indica má calibração

**Brier Score:**
- Métrica de qualidade de probabilidade
- Brier Score = 1/n × Σ(probabilidade - outcome)²
- Brier Score ∈ [0, 1]; menor é melhor
- Brier Score < 0.25 é aceitável

**Expected Calibration Error (ECE):**
- Média ponderada do erro de calibração por bin
- ECE < 0.05 é bom
- ECE < 0.10 é aceitável
- ECE > 0.10 precisa de recalibração

**Log Loss:**
- Métrica de qualidade de probabilidade
- Log Loss = -1/n × Σ[outcome × log(P) + (1-outcome) × log(1-P)]
- Menor é melhor
- Log Loss < 0.6 é bom para betting

### 5.3. Validação de Calibração por Bin

**Estratégia de binning:**
- Dividir predictions em bins de probabilidade
- Ex: [0.0-0.1], [0.1-0.2], ..., [0.9-1.0]
- Calcular win rate real em cada bin

**Critérios de aceitação:**
- Diferença entre P prevista e win rate real < 5% em cada bin
- Pelo menos 50 amostras por bin para estatística válida
- Alertar se bins extremos (< 0.2 ou > 0.8) têm discrepância > 10%

**Ações de correção:**
- Se systematicamente overconfiante: reduzir confiança (aplicar função sigmoid)
- Se systematicamente subconfiante: aumentar confiança
- Se calibration não monotônica: re-treinar modelo

### 5.4. Calibração Temporal

**Validação por período:**
- Calcular métricas de calibração por semana/mês
- Detectar degradação de calibração ao longo do tempo
- Alertar se Brier Score aumenta > 20% vs baseline

**Validação por fase da temporada:**
- Calibração pode variar entre regular season e playoffs
- Documentar diferenças esperadas
- Validar separadamente se necessário

**Validação por tipo de matchup:**
- Calibração pode variar por matchup (favorites vs underdogs)
- Analisar calibração por decil de spread
- Ajustar se necessário

---

## 6. VALIDAÇÃO DE CONSISTÊNCIA

### 6.1. Consistência entre Predictions

**Consistência home-away:**
- P(home_win) + P(away_win) = 1.0 (tolerância ±0.01)
- Alertar se soma ≠ 1.0

**Consistência spread-moneyline:**
- Spread prediction deve ser consistente com P(vitória)
- Usar curva de conversão histórica para validar
- Alertar se discrepância > 10%

**Consistência totals-over/under:**
- P(over) + P(under) = 1.0
- Total prediction deve ser consistente com P(over)
- Alertar se discrepância > 5%

### 6.2. Consistência com Features

**Consistência com rolling averages:**
- Prediction deve ser razoável dado rolling averages
- Ex: team com avg 110 pts não deve ter prediction de 90 pts
- Alertar se prediction > 2 desvios padrão do esperado

**Consistência com matchup:**
- Prediction deve refletir matchup defensivo
- Ex: offense forte vs defense fraco = prediction mais alta
- Validar com features de matchup

**Consistência com contexto:**
- Prediction deve refletir contexto (rest days, travel, injuries)
- Ex: team em back-to-back = prediction mais baixa
- Validar com features de contexto

### 6.3. Consistência Temporal

**Suavidade temporal:**
- Prediction para mesmo matchup não deve variar drasticamente dia-a-dia
- Variação < 10% entre dias consecutivos é aceitável
- Alertar se variação > 30%

**Consistência com tendências:**
- Prediction deve refletir tendências recentes
- Ex: team em winning streak = prediction mais alta
- Validar com features de momentum

---

## 7. VALIDAÇÃO DE BIAS

### 7.1. Detecção de Bias Sistemático

**Bias de favoritismo:**
- Analisar win rate para favorites vs underdogs
- Se modelo systematicamente overestima favorites: bias de favoritismo
- Ajustar predictions se bias > 5%

**Bias de home court:**
- Analisar se modelo overestima home teams
- Home court advantage na NBA é ~3 pontos
- Validar se predictions refletem isso

**Bias de recency:**
- Analisar se modelo overweigha jogos recentes
- Comparar predictions com rolling averages de diferentes janelas
- Ajustar se bias de recency detectado

### 7.2. Validação de Bias por Grupo

**Por equipa:**
- Calcular erro médio por equipa
- Alertar se某 equipa tem erro sistemático > 10%
- Pode indicar que modelo não captura style específico

**Por jogador:**
- Calcular erro médio por jogador (para player props)
- Alertar se某 jogador tem erro sistemático > 15%
- Ajustar se necessário

**Por matchup:**
- Calcular erro médio por tipo de matchup
- Ex: high-scoring vs low-scoring matchups
- Ajustar se bias específico detectado

---

## 8. VALIDAÇÃO DE PERFORMANCE

### 8.1. Métricas de Performance

**Accuracy:**
- % de predictions corretas (para classificações)
- Target: > 55% para moneyline, > 52% para spread
- Alerta se accuracy cair > 5% vs baseline

**MAE (Mean Absolute Error):**
- Erro médio absoluto (para regressões)
- Para spread: MAE < 5 pontos é bom
- Para totals: MAE < 7 pontos é bom
- Alertar se MAE aumenta > 20% vs baseline

**RMSE (Root Mean Squared Error):**
- Raiz do erro quadrático médio
- Penaliza erros grandes mais fortemente
- RMSE deve ser < 1.5 × MAE
- Alertar se RMSE >> MAE (outliers)

**R² (R-squared):**
- % de variância explicada
- R² > 0.1 é aceitável para betting
- R² > 0.2 é bom
- Alertar se R² cai > 30% vs baseline

### 8.2. Validação de Performance por Período

**Performance rolling:**
- Calcular métricas nos últimos N jogos
- Ex: accuracy nos últimos 50 jogos
- Alertar se performance cai > 10% vs performance total

**Performance por fase:**
- Comparar performance regular season vs playoffs
- Documentar diferenças esperadas
- Alertar se diferença > 20%

**Performance por mercado:**
- Comparar performance moneyline vs spread vs totals
- Identificar mercados onde modelo é melhor/pior
- Ajustar estratégia de betting se necessário

---

## 9. VALIDAÇÃO DE VALOR (EV)

### 9.1. Validação de EV Calculation

**Fórmula de EV:**
- EV = (Probabilidade × Payout) - Stake
- Onde Payout = Odd × Stake
- EV = (Probabilidade × Odd) - 1

**Validação de cálculo:**
- Recalcular EV a partir de probabilidade e odd
- Comparar com EV prediction
- Alertar se discrepância > 1%

### 9.2. Validação de Realized EV

**Conceito:**
- Realized EV = (Win Rate × Payout) - Stake
- Deve aproximar Predicted EV ao longo do tempo

**Validação:**
- Calcular realized EV nos últimos N apostas
- Comparar com predicted EV médio
- Tolerância: ± 5%
- Alertar se discrepância > 10%

**Ações de correção:**
- Se realized EV << predicted EV: modelo overestima valor
- Recalibrar probabilidades
- Re-treinar modelo se necessário

### 9.3. Validação de Kelly Criterion

**Fórmula de Kelly:**
- Kelly Fraction = (EV / (Odd - 1))
- Stake = Kelly Fraction × Bankroll

**Validação:**
- Kelly fraction deve estar em [0, 0.25]
- Alertar se Kelly > 0.25 (overbetting)
- Alertar se Kelly < 0 (negative EV)

**Conservadorismo:**
- Usar fractional Kelly (ex: 0.5 × Kelly)
- Reduzir volatilidade do bankroll
- Documentar fator de conservadorismo usado

---

## 10. MONITORIZAÇÃO

### 10.1. Métricas em Tempo Real

**Taxa de predictions válidas:**
- % de predictions que passam validações
- Target: > 99%
- Alerta se < 95%

**Distribuição de predictions:**
- Histograma de predictions por tipo
- Alertar se distribuição muda drasticamente
- Detectar anomalias no modelo

**EV médio por tipo de aposta:**
- EV médio para moneyline, spread, totals
- Alerta se EV cai > 20% vs baseline
- Detectar degradação do modelo

### 10.2. Dashboard de Predictions

**Componentes:**
1. Reliability diagram (calibração)
2. Distribuição de predictions (histogramas)
3. Accuracy rolling (line chart)
4. Realized vs Predicted EV (line chart)
5. Top 10 erros mais recentes

**Frequência de atualização:**
- Em tempo real: após cada batch de predictions
- Tendências: atualização a cada hora
- Relatórios: diários e semanais

---

## 11. REFERÊNCIAS CRUZADAS

- [[31_Data_Validation/INDEX]] ← Secção mãe
- [[05_Machine_Learning/INDEX]] → Modelos que geram predictions
- [[06_Backtesting/INDEX]] → Validação histórica de predictions
- [[07_Value_Detection/INDEX]] → Uso de predictions para deteção de value

---

## 12. HISTÓRICO DE ALTERAÇÕES

| Data | Versão | Alteração | Autor |
|------|--------|-----------|-------|
| 2024-XX-XX | 1.0 | Criação inicial do documento | Data Engineer |