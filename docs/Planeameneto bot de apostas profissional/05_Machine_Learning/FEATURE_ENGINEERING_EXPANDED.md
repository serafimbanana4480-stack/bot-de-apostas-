# FEATURE ENGINEERING EXPANDIDO — 80-100 Features

**ID:** `SEC-05-02` | **Status:** #status/pending | **Versão:** `2.0.0-EXPANDED`

---

## 1. OBJETIVO

Expandir de 40-50 para 80-100 features incluindo descanso assimétrico, impacto On/Off, e microestrutura de mercado.

---

## 2. CATEGORIAS DE FEATURES

### 2.1 Forma da Equipa (20 features)

**Features Existentes:**
- Win rate últimos 10 jogos
- Win rate últimos 5 jogos
- Win rate últimos 3 jogos
- PPG últimos 10 jogos
- PPG concedidos últimos 10 jogos
- Net rating últimos 10 jogos
- Streak atual (vitórias/derrotas consecutivas)
- Home/away split

**Novas Features:**
```python
# Descanso Assimétrico
rest_days_asymmetric = abs(rest_days_team_a - rest_days_team_b)
rest_advantage_flag = 1 if rest_days_team_a > rest_days_team_b + 2 else 0
back_to_back_flag = 1 if (team_a_played_yesterday and team_b_didnt) else 0
travel_distance_km = calculate_travel_distance(last_game_location, current_location)
time_zone_change_hours = abs(timezone_last - timezone_current)

# Momentum
momentum_3g = sum(wins_last_3) / 3
momentum_5g = sum(wins_last_5) / 5
momentum_10g = sum(wins_last_10) / 10
momentum_trend = momentum_3g - momentum_10g  # Melhora ou piora recente

# Eficiência
offensive_rating_last_10 = points_scored / possessions
defensive_rating_last_10 = points_conceded / possessions
net_rating_last_10 = offensive_rating - defensive_rating
pace_last_10 = total_possessions / games_played

# Clutch Performance
clutch_win_rate = wins_in_last_5min / games_played_in_clutch
overtime_win_rate = wins_in_ot / games_played_ot
blowout_win_rate = wins_by_15plus / total_games
blowout_loss_rate = losses_by_15plus / total_games
```

### 2.2 Impacto On/Off (15 features)

```python
# Net Rating On/Off
net_rating_on_court = team_net_rating_with_player
net_rating_off_court = team_net_rating_without_player
on_off_diff = net_rating_on_court - net_rating_off_court

# Impacto Ofensivo
offensive_rating_on = team_pts_with_player / possessions
offensive_rating_off = team_pts_without_player / possessions
offensive_on_off_diff = offensive_rating_on - offensive_rating_off

# Impacto Defensivo
defensive_rating_on = team_pts_conceded_with_player / possessions
defensive_rating_off = team_pts_conceded_without_player / possessions
defensive_on_off_diff = defensive_rating_on - defensive_rating_off

# Impacto em Lineups
lineup_net_rating = net_rating_of_most_used_lineup
lineup_usage_pct = minutes_in_lineup / total_minutes
lineup_plus_minus = plus_minus_when_on_court

# Substituição
replacement_level = avg_net_rating_of_replacements
replacement_gap = on_off_diff - replacement_level
depth_score = quality_of_bench_players
```

### 2.3 Microestrutura de Mercado (20 features)

```python
# Movimento de Odds
opening_odd = get_opening_odd(market_id)
current_odd = get_current_odd(market_id)
odd_movement_pct = (current_odd - opening_odd) / opening_odd
odd_movement_direction = 1 if current_odd < opening_odd else -1
time_since_open = hours_since_market_opened
movement_velocity = odd_movement_pct / time_since_open

# Volume de Mercado
total_matched_volume = get_total_matched(market_id)
volume_last_hour = get_volume_last_hour(market_id)
volume_spike = volume_last_hour / avg_volume_per_hour
liquidity_score = total_matched / expected_stake
spread_width = best_back_odd - best_lay_odd

# CLV Indicators
closing_line_value = calculate_clv(opening_odd, closing_odd)
clv_direction = 1 if clv > 0 else -1
sharp_money_flag = 1 if (volume_spike > 2 and clv_direction == 1) else 0
public_money_flag = 1 if (volume_spike > 2 and clv_direction == -1) else 0

# Sentimento de Mercado
money_distribution = get_back_money / (get_back_money + get_lay_money)
price_pressure = (best_back_odd - prev_back_odd) / prev_back_odd
order_book_depth = depth_at_price(current_odd)
imbalance_ratio = back_volume / lay_volume
```

### 2.4 Contexto e Situação (15 features)

```python
# Contexto de Temporada
games_played = total_games_season
games_remaining = total_games_season - games_played
playoff_probability = calculate_playoff_prob(current_record, remaining_games)
rest_of_season_strength = avg_opponent_strength_remaining
season_progress_pct = games_played / total_games_season

# Situação do Jogo
home_court_advantage = 1 if is_home_game else 0
altitude_difference = altitude_arena - altitude_previous_arena
back_to_back_3rd = 1 if played_last_2_days else 0
injury_impact_score = sum(injury_impact_of_out_players)
suspension_impact_score = sum(suspension_impact)

# Rivalidade e Motivação
rivalry_flag = 1 if is_rivalry_game else 0
revenge_game_flag = 1 if lost_last_meeting else 0
importance_score = calculate_game_importance(playoff_prob, opponent_strength
motivation_factor = combine(rivalry_flag, revenge_game_flag, importance_score)
```

### 2.5 Interações e Features Derivadas (15 features)

```python
# Interações de Forma
form_mismatch = momentum_team_a - momentum_team_b
efficiency_mismatch = net_rating_team_a - net_rating_team_b
pace_mismatch = pace_team_a - pace_team_b

# Interações On/Off
on_off_mismatch = on_off_diff_team_a - on_off_diff_team_b
star_power_gap = max_on_off_diff_team_a - max_on_off_diff_team_b
depth_mismatch = bench_rating_team_a - bench_rating_team_b

# Interações de Mercado
market_sentiment_mismatch = money_distribution_team_a - money_distribution_team_b
clv_mismatch = clv_team_a - clv_team_b
volume_pressure_mismatch = volume_spike_team_a - volume_spike_team_b

# Features Polinomiais (selecionadas)
rest_squared = rest_days_asymmetric ** 2
momentum_squared = momentum_10g ** 2
on_off_squared = on_off_diff ** 2
```

### 2.6 Flags de Regime (5 features)

```python
# Flags Binários para Calibração
favorite_flag = 1 if implied_prob > 0.55 else 0
underdog_flag = 1 if implied_prob < 0.45 else 0
balanced_flag = 1 if 0.45 <= implied_prob <= 0.55 else 0
high_edge_flag = 1 if calculated_edge > 0.06 else 0
low_confidence_flag = 1 if model_uncertainty > 0.1 else 0
```

---

## 3. IMPLEMENTAÇÃO

```python
def extract_expanded_features(game_data, market_data):
    """
    Extrai todas as 80-100 features para um jogo.
    """
    features = {}
    
    # 1. Forma da Equipa (20)
    features.update(extract_team_form_features(game_data))
    
    # 2. Impacto On/Off (15)
    features.update(extract_on_off_features(game_data))
    
    # 3. Microestrutura de Mercado (20)
    features.update(extract_market_microstructure(market_data))
    
    # 4. Contexto e Situação (15)
    features.update(extract_context_features(game_data))
    
    # 5. Interações (15)
    features.update(extract_interaction_features(features))
    
    # 6. Flags de Regime (5)
    features.update(extract_regime_flags(features, market_data))
    
    return pd.Series(features)
```

---

## 4. SELEÇÃO DE FEATURES

```python
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.model_selection import cross_val_score

def feature_selection_pipeline(X, y, n_features=80):
    """
    Seleciona as melhores features baseado em significância estatística.
    """
    # 1. Remover features com correlação > 0.95
    corr_matrix = X.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [column for column in upper.columns if any(upper[column] > 0.95)]
    X_reduced = X.drop(columns=to_drop)
    
    # 2. Selecionar top K features baseado em F-score
    selector = SelectKBest(f_classif, k=n_features)
    X_selected = selector.fit_transform(X_reduced, y)
    selected_features = X_reduced.columns[selector.get_support()]
    
    # 3. Validar com cross-validation
    cv_scores = cross_val_score(ensemble_model, X_selected, y, cv=5)
    
    return selected_features, cv_scores
```

---

## 5. CRITÉRIOS DE SUCESSO

| Critério | Threshold |
|----------|-----------|
| Total de features | 80-100 |
| Features com correlação < 0.95 | > 90% |
| Feature importance top 10 estável | Em ≥ 8 folds |
| CLV com features expandidas | > 3% (vs 2% baseline) |
| Tempo de extração por jogo | < 500ms |
