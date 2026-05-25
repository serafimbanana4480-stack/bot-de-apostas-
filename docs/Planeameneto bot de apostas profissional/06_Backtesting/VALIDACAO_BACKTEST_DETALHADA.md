# VALIDAÇÃO E BACKTEST DETALHADA — RIGOR ESTATÍSTICO

**ID:** `VAL-001` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar o processo de validação rigorosa que garante que o modelo tem vantagem matemática real antes de colocar dinheiro real.

**Princípio:** Não avançar para produção sem CLV > 2%, ROI > 5% e Sharpe > 0.5 no teste final.

---

## 2. PURGED WALK-FORWARD CROSS-VALIDATION

### 2.1 Estrutura Temporal

```
Épocas NBA:
2019-20, 2020-21, 2021-22 (TREINO)
        ↓
        2022-23 (VALIDAÇÃO — com embargo de 2 dias)
        ↓
        2023-24 (TESTE FINAL — nunca usado para otimização)
```

### 2.2 Embargo Temporal

**Por que embargo?** Evita leakage de eventos próximos no tempo (jogos adiados, adições de calendário).

**Regra:** 2 dias de exclusão entre treino e validação.

**Exemplo:**
- Jogo validação: 2022-10-15
- Limite treino: 2022-10-13 (inclusive)
- Embargo: 2022-10-14

### 2.3 Janela Deslizante (Mensal)

```
Fold 1: Treino 2019-20 a 2022-06 → Validação 2022-07
Fold 2: Treino 2019-20 a 2022-07 → Validação 2022-08
...
Fold 12: Treino 2019-20 a 2023-05 → Validação 2023-06
```

**Número de folds:** 12 (um por mês de validação)

### 2.4 Implementação

```python
from datetime import datetime, timedelta

def purged_walk_forward_split(games, embargo_days=2):
    folds = []
    validation_months = pd.date_range('2022-07-01', '2023-06-01', freq='MS')
    
    for val_month in validation_months:
        # Data de início do mês de validação
        val_start = val_month
        val_end = val_month + pd.DateOffset(months=1)
        
        # Data limite para treino (com embargo)
        train_end = val_start - timedelta(days=embargo_days)
        
        # Dados de treino (tudo antes do embargo)
        train_mask = games['date'] < train_end
        train_data = games[train_mask]
        
        # Dados de validação (mês completo)
        val_mask = (games['date'] >= val_start) & (games['date'] < val_end)
        val_data = games[val_mask]
        
        folds.append((train_data, val_data))
    
    return folds
```

---

## 3. MÉTRICAS DE DECISÃO

### 3.1 CLV (Closing Line Value)

**Definição:** Diferença entre odd usada e odd de fecho do Pinnacle.

```python
CLV = (odds_pinnacle_close - odds_used) / odds_used
```

**Target:** CLV médio > 2%

**Justificação:** CLV é o melhor proxy de vantagem matemática real. Se o mercado move na nossa direção após a aposta, o edge era genuíno.

### 3.2 ROI Simulado

```python
ROI = (profit - stake) / stake
```

**Comissões e Slippage:**
```python
profit_after = profit * (1 - 0.05) - stake * 0.005  # 5% comissão, 0.5% slippage
ROI_after = (profit_after - stake) / stake
```

**Target:** ROI > 5% após comissões e slippage

### 3.3 Sharpe Ratio

```python
sharpe = (mean(returns) - risk_free_rate) / std(returns)
```

**Assumptions:**
- `risk_free_rate = 0` (apostas não têm taxa livre de risco)
- Returns calculados diariamente

**Target:** Sharpe > 0.5

**Justificação:** Sharpe > 0.5 indica que o retorno ajustado pelo risco é positivo.

### 3.4 Drawdown

```python
def calculate_drawdown(cumulative_returns):
    peak = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - peak) / peak
    return drawdown

max_drawdown = calculate_drawdown(cumulative_returns).min()
```

**Target:** Max drawdown < 20%

**Justificação:** Drawdown excessivo indica risco de ruína.

---

## 4. SIMULAÇÕES DE MONTE CARLO

### 4.1 Objetivo

Estimar a distribuição de possíveis resultados e probabilidade de ruína.

### 4.2 Metodologia

```python
import numpy as np

def monte_carlo_simulation(probabilities, stakes, n_simulations=10000):
    """
    probabilities: array de probabilidades de vitória para cada aposta
    stakes: array de stakes (em % do bankroll)
    """
    n_bets = len(probabilities)
    results = np.zeros((n_simulations, n_bets))
    
    for sim in range(n_simulations):
        # Gerar resultados aleatórios (Bernoulli)
        outcomes = np.random.binomial(1, probabilities)
        
        # Calcular retornos
        returns = np.where(
            outcomes == 1,
            stakes * (1/odds - 1),  # Vitória
            -stakes  # Derrota
        )
        
        results[sim, :] = returns
    
    return results

# Calcular métricas
simulations = monte_carlo_simulation(p_modelo, stakes, 10000)
final_bankrolls = np.cumprod(1 + simulations, axis=1)[:, -1]

# Probabilidade de ruína (banca < 50% do inicial)
prob_ruin = np.mean(final_bankrolls < 0.5)

# Distribuição de drawdown máximo
max_drawdowns = []
for sim in simulations:
    cumulative = np.cumprod(1 + sim)
    drawdown = calculate_drawdown(cumulative)
    max_drawdowns.append(drawdown.min())
```

### 4.3 Análise de Kelly

```python
# Testar diferentes frações de Kelly
kelly_fractions = [0.25, 0.5, 0.75, 1.0]

for k in kelly_fractions:
    stakes = k * kelly_fractions
    simulations = monte_carlo_simulation(p_modelo, stakes, 10000)
    prob_ruin = np.mean(np.cumprod(1 + simulations, axis=1)[:, -1] < 0.5)
    print(f"Kelly {k}: Prob. ruína = {prob_ruin:.2%}")
```

**Critério de aprovação:** Probabilidade de ruína < 5% com meio Kelly

---

## 5. CRITÉRIOS DE APROVAÇÃO

### 5.1 Métricas Obrigatórias

| Métrica | Threshold | Como Medir |
|---------|-----------|-------------|
| CLV médio | > 2.0% | Média de CLV no teste final |
| ROI simulado | > 5.0% | ROI após 5% comissão + 0.5% slippage |
| Sharpe Ratio | > 0.5 | ROI médio / std(returns) |
| Max Drawdown | < 20% | Drawdown máximo no teste final |
| Prob. Ruína (0.5 Kelly) | < 5% | Monte Carlo simulation |
| Número de apostas | > 100 | Amostra estatisticamente significativa |

### 5.2 Regra de Bloqueio

**Se QUALQUER critério não for satisfeito:**
- ❌ Bloquear avanço para produção
- ❌ Bloquear shadow mode
- ❌ Revisar modelo e features
- ✅ Apenas voltar ao backtest após ajustes

**Exceções:** Nenhuma. Rigor estatístico é não-negociável.

---

## 6. VALIDAÇÃO DE CALIBRAÇÃO

### 6.1 Brier Score

```python
from sklearn.metrics import brier_score_loss

brier = brier_score_loss(y_true, y_pred_prob)
```

**Target:** Brier < Brier do mercado (probabilidades implícitas)

### 6.2 ECE (Expected Calibration Error)

```python
def expected_calibration_error(y_true, y_pred, n_bins=10):
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(y_pred, bin_edges[:-1]) - 1
    
    ece = 0.0
    for bin_idx in range(n_bins):
        mask = bin_indices == bin_idx
        if np.sum(mask) == 0:
            continue
        
        bin_confidence = np.mean(y_pred[mask])
        bin_accuracy = np.mean(y_true[mask])
        bin_weight = np.sum(mask) / len(y_true)
        
        ece += bin_weight * np.abs(bin_confidence - bin_accuracy)
    
    return ece
```

**Target:** ECE < 0.05

### 6.3 Reliability Diagrams

Dividir previsões em bins (0-0.1, 0.1-0.2, ..., 0.9-1.0) e plotar:
- X-axis: Probabilidade prevista
- Y-axis: Frequência real de vitória

**Ideal:** Pontos devem estar próximos da linha diagonal (perfeita calibração)

### 6.4 Calibração por Regime

Separar reliability diagrams por:
- Favorito (P ≥ 0.65)
- Equilibrado (0.35 ≤ P < 0.65)
- Underdog (P < 0.35)

**Target:** ECE < 0.05 em todos os regimes

---

## 7. TESTES DE OVERFITTING

### 7.1 Comparação Treino vs Validação

```python
train_metrics = evaluate_model(X_train, y_train)
val_metrics = evaluate_model(X_val, y_val)

# Overfitting se gap for grande
gap_clv = train_metrics['CLV'] - val_metrics['CLV']
gap_sharpe = train_metrics['Sharpe'] - val_metrics['Sharpe']

if gap_clv > 1.0 or gap_sharpe > 0.2:
    print("ALERTA: Possível overfitting")
```

### 7.2 Feature Importance Stability

**Teste:** Verificar se top 10 features são estáveis em ≥ 8 folds

```python
feature_importance_by_fold = []

for fold in folds:
    model = train_model(fold['X_train'], fold['y_train'])
    importance = model.feature_importances_
    feature_importance_by_fold.append(importance)

# Calcular variância de importância
importance_array = np.array(feature_importance_by_fold)
importance_std = np.std(importance_array, axis=0)

# Features estáveis têm std baixo
stable_features = np.argsort(importance_std)[:10]
```

### 7.3 Teste de Leakage Temporal

**Procedimento:**
1. Verificar que todas as features usam dados até timestamp do jogo
2. Verificar que nenhuma feature usa estatísticas do próprio jogo
3. Verificar que nenhuma feature usa dados de jogos futuros

**Automatização:**
```python
def check_temporal_leakage(features, game_date):
    for feature in features:
        if feature.data_source_date >= game_date:
            raise ValueError(f"Leakage detected in {feature.name}")
```

---

## 8. PIPELINE DE BACKTEST AUTOMATIZADO

```python
def run_backtest_pipeline():
    # 1. Carregar dados históricos
    data = load_historical_data(5_seasons_nba)
    
    # 2. Gerar features (com look-ahead protection)
    features = generate_features(data)
    
    # 3. Dividir em folds (purged walk-forward)
    folds = purged_walk_forward_split(data)
    
    # 4. Treinar e validar em cada fold
    results = []
    for fold in folds:
        model = train_model(fold['X_train'], fold['y_train'])
        predictions = model.predict(fold['X_val'])
        metrics = evaluate_predictions(
            predictions,
            fold['y_val'],
            fold['odds']
        )
        results.append(metrics)
    
    # 5. Agregar métricas
    final_metrics = aggregate_metrics(results)
    
    # 6. Monte Carlo simulation
    mc_results = monte_carlo_simulation(
        final_metrics['probabilities'],
        final_metrics['stakes'],
        10000
    )
    
    # 7. Calibração
    calibration_metrics = evaluate_calibration(
        final_metrics['y_true'],
        final_metrics['y_pred']
    )
    
    # 8. Gerar relatório
    report = {
        'CLV': final_metrics['CLV'],
        'ROI': final_metrics['ROI'],
        'Sharpe': final_metrics['Sharpe'],
        'Max_Drawdown': final_metrics['Max_Drawdown'],
        'Prob_Ruin': mc_results['prob_ruin'],
        'Brier': calibration_metrics['Brier'],
        'ECE': calibration_metrics['ECE']
    }
    
    return report
```

---

## 9. BACKLOG

- [ ] Implementar purged walk-forward CV com embargo
- [ ] Implementar cálculo de CLV vs Pinnacle
- [ ] Implementar Monte Carlo simulation
- [ ] Implementar reliability diagrams
- [ ] Implementar testes de overfitting automatizados
- [ ] Implementar testes de leakage temporal
- [ ] Criar dashboard de backtest results

---

## 10. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[05_Machine_Learning/INDEX]] → Modelos validados
- [[32_Feature_Store/INDEX]] → Features validadas
- [[47_Shadow_Betting/INDEX]] → Shadow mode (validação com odds reais)
- [[21_Paper_Trading/INDEX]] → Paper trading (validação operacional)
