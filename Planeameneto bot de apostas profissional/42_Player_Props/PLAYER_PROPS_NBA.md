# PLAYER PROPS NBA — Estratégia Detalhada

**ID:** `SEC-42` | **Status:** #status/pending | **Versão:** `2.0.0-PROPS`

---

## 1. OBJETIVO

Expandir para mercados de player props NBA (pontos, rebounds, assists, PRA) com edge estimado de 3-5%.

---

## 2. MERCADOS PRIORITÁRIOS

### 2.1 Tipos de Props

| Prop | Edge Estimado | Volume | Prioridade |
|------|---------------|--------|------------|
| **Points** | 3-4% | Alto | MÁXIMA |
| **Rebounds** | 3-5% | Médio | ALTA |
| **Assists** | 3-5% | Médio | ALTA |
| **PRA (Points+Rebounds+Assists)** | 4-6% | Médio | MÁXIMA |
| **Threes Made** | 2-3% | Baixo | MÉDIA |
| **Blocks+Steals** | 4-7% | Baixo | MÉDIA |

### 2.2 Foco em Jogadores

**Jogadores com Maior Edge:**
- Star players com uso consistente (>30 min/jogo)
- Role players com estatísticas estáveis
- Evitar jogadores com minutos variáveis
- Evitar jogadores lesionados frequentemente

---

## 3. FEATURES PARA PLAYER PROPS

### 3.1 Features Individuais (30 features)

```python
# Histórico de Performance
avg_points_last_5 = mean(points_last_5_games)
avg_points_last_10 = mean(points_last_10_games)
avg_points_last_20 = mean(points_last_20_games)
points_trend = avg_points_last_5 - avg_points_last_20

# Consistência
points_std_last_10 = std(points_last_10)
points_cv = points_std_last_10 / avg_points_last_10
games_above_avg_last_10 = count(points > avg_points_last_20) / 10

# Uso e Minutos
avg_minutes_last_5 = mean(minutes_last_5)
avg_minutes_last_10 = mean(minutes_last_10)
usage_rate_last_10 = team_usage_rate_with_player
minutes_trend = avg_minutes_last_5 - avg_minutes_last_20

# Matchup
opponent_defensive_rating = defensive_rating_of_opponent
opponent_points_conceded_at_position = avg_points_conceded_vs_position
opponent_pace = pace_of_opponent
matchup_difficulty = (opponent_defensive_rating - league_avg) / league_avg

# Contexto de Jogo
game_total_expected = expected_total_score
pace_expected = expected_pace
home_advantage = 1 if home_game else 0
back_to_back = 1 if played_yesterday else 0

# Lesões e Rotação
injury_status = 0 if healthy else (-1 if injured else 0)
teammate_injury_impact = impact_of_injured_teammate_on_stats
rotation_spot = 1 if starter else 0.5 if sixth_man else 0.2
```

### 3.2 Features de Equipa (15 features)

```python
team_offensive_rating = offensive_rating_last_10
team_pace = pace_last_10
team_usage_distribution = distribution_of_usage_among_players
team_play_style = run_and_gun vs halfcourt
opponent_defensive_scheme = man_to_man vs zone
```

### 3.3 Features de Mercado (10 features)

```python
# Odds e Linha
prop_line = get_prop_line(player_id, prop_type)
current_odd = get_current_odd(player_id, prop_type)
line_movement = prop_line - opening_line
odd_movement = (current_odd - opening_odd) / opening_odd

# Volume e Sentimento
prop_volume = get_volume_for_prop(player_id, prop_type)
sharp_money_on_over = 1 if sharp_money_direction == 'over' else 0
public_money_on_over = 1 if public_money_direction == 'over' else 0
```

---

## 4. MODELO PARA PLAYER PROPS

### 4.1 Arquitetura

```
┌─────────────────────────────────────────┐
│         FEATURES (55-60)                 │
│  Individual │ Team │ Market │ Context    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│    XGBoost REGRESSOR (Gradient)         │
│  Target: Points/Rebounds/Assists        │
│  Output: Valor previsto contínuo        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         CÁLCULO DE EDGE                 │
│  edge = (predicted - line) / line      │
│  Filtro: edge > 5%                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│       META-LABELING (XGBoost)            │
│  Target: P(CLV > 0 | edge, confiança)   │
│  Filtro: prob_meta > 0.55               │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      GESTÃO DE RISCO (Kelly)             │
│  Stake = f(bankroll, edge, volatilidade)│
└─────────────────────────────────────────┘
```

### 4.2 Configuração do Modelo

```python
from xgboost import XGBRegressor

prop_model_config = {
    "objective": "reg:squarederror",  # Regressão para valores contínuos
    "eval_metric": ["rmse", "mae"],
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 20,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "tree_method": "hist",
    "seed": 42,
    "n_estimators": 1000,
}
```

---

## 5. VALIDAÇÃO

### 5.1 Walk-Forward CV para Props

```python
def purged_walk_forward_props(X, y, dates, embargo_days=1):
    """
    Validação temporal para player props.
    """
    n_splits = 12
    prop_performance = []
    
    for i in range(n_splits):
        # Janela deslizante mensal
        train_start = i * 3
        train_end = train_start + 24  # 24 meses de treino
        val_start = train_end + embargo_days
        val_end = val_start + 1  # 1 mês de validação
        
        # Treinar modelo
        model = XGBRegressor(**prop_model_config)
        model.fit(X_train, y_train)
        
        # Prever e calcular CLV
        predictions = model.predict(X_val)
        clv = calculate_clv_for_props(predictions, prop_lines, odds)
        prop_performance.append(clv)
    
    return prop_performance
```

### 5.2 Critérios de Sucesso

| Critério | Threshold |
|----------|-----------|
| RMSE | < 3.0 pontos |
| MAE | < 2.0 pontos |
| CLV médio | > 3% |
| ROI simulado | > 5% |
| Sharpe Ratio | > 0.6 |

---

## 6. GESTÃO DE RISCO ESPECÍFICA PARA PROPS

### 6.1 Stake por Prop

```python
def calculate_prop_stake(edge, volatility, bankroll):
    """
    Calcula stake para player props considerando volatilidade.
    """
    base_stake = kelly_fraction(edge, bankroll)
    
    # Ajustar por volatilidade (props têm mais variância)
    volatility_adjustment = 1 / (1 + volatility)
    
    # Ajustar por liquidez
    liquidity_adjustment = min(1.0, prop_volume / 1000)
    
    final_stake = base_stake * volatility_adjustment * liquidity_adjustment
    
    # Limitar a 1% da banca por prop (mais conservativo que team props)
    final_stake = min(final_stake, 0.01 * bankroll)
    
    return final_stake
```

### 6.2 Limites de Exposição

- Máximo 3 props por jogador por jogo
- Máximo 10 props por jogo total
- Máximo 2% da banca total em props por dia
- Evitar correlação alta entre props do mesmo jogador

---

## 7. CRONOGRAMA DE IMPLEMENTAÇÃO

**Mês 1-2:** Coleta de dados históricos de props
**Mês 3:** Feature engineering para props
**Mês 4:** Treino e validação de modelo
**Mês 5:** Shadow mode (sem apostas reais)
**Mês 6:** Produção com banca reduzida (10% da banca total)
