# MATCHUP_ANALYSIS — Análise de Matchup para Player Props

**ID:** `PP-009` | **Fase:** #phase/6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar a abordagem de análise de matchup específica para player props, incluindo histórico head-to-head, matchup defensivo individual, e fatores de matchup equipa vs equipa que influenciam a produção estatística de jogadores.

---

## 2. IMPORTÂNCIA DE MATCHUP

### 2.1 Por Que Matchup é Crítico

```python
matchup_importance = {
    # Variabilidade de produção
    "production_variance": {
        "description": "Mesmo jogador pode variar 30-50% dependendo do matchup",
        "example": "LeBron vs Warriors: 28 pts vs LeBron vs Magic: 35 pts",
        "impact": "Features de matchup são essenciais para previsão precisa",
    },
    
    # Estilo defensivo
    "defensive_style": {
        "description": "Equipas têm estilos defensivos diferentes",
        "example": "Celtics (defesa forte) vs Kings (defesa fraca)",
        "impact": "Rating defensivo do adversário é feature importante",
    },
    
    # Matchup individual
    "individual_matchup": {
        "description": "Defensor específico pode limitar ou permitir produção",
        "example": "Embiid vs Turner (bom matchup) vs Embiid vs Gobert (difícil)",
        "impact": "Defender rating é feature crítica",
    },
    
    # Estilo de jogo
    "pace_and_style": {
        "description": "Ritmo e estilo afetam oportunidades",
        "example": "Warriors (pace alto) vs Cavs (pace baixo)",
        "impact": "Pace do adversário afeta minutos e posses",
    },
}
```

### 2.2 Exemplos de Variação

```python
matchup_variance_examples = {
    # Exemplo 1: Pontos
    "stephen_curry_pts": {
        "vs_raptors": 28.5,
        "vs_celtics": 24.2,
        "vs_kings": 32.1,
        "vs_grizzlies": 26.8,
        "variance": "+/- 4 pts (~15%)",
    },
    
    # Exemplo 2: Ressaltos
    "giannis_antetokounmpo_reb": {
        "vs_celtics": 11.2,
        "vs_heat": 13.5,
        "vs_nets": 12.8,
        "vs_hawks": 14.2,
        "variance": "+/- 1.5 reb (~12%)",
    },
    
    # Exemplo 3: Assistências
    "chris_paul_ast": {
        "vs_warriors": 9.8,
        "vs_suns": 11.2,
        "vs_lakers": 8.5,
        "vs_mavericks": 10.1,
        "variance": "+/- 1.5 ast (~15%)",
    },
}
```

---

## 3. HISTÓRICO HEAD-TO-HEAD

### 3.1 Cálculo de Histórico H2H

```python
def calculate_h2h_history(player_id, opponent_id, historical_data, window=10):
    """
    Calcula histórico head-to-head entre jogador e equipa adversária.
    
    Args:
        player_id: ID do jogador
        opponent_id: ID da equipa adversária
        historical_data: DataFrame com dados históricos
        window: número de jogos recentes a considerar
    
    Returns:
        h2h_stats: dicionário com estatísticas H2H
    """
    # Filtrar jogos contra este adversário
    h2h_games = historical_data[
        (historical_data['player_id'] == player_id) &
        (historical_data['opponent_id'] == opponent_id)
    ].tail(window)
    
    if len(h2h_games) == 0:
        return None
    
    h2h_stats = {
        # Médias
        'pts_avg': h2h_games['pts'].mean(),
        'reb_avg': h2h_games['reb'].mean(),
        'ast_avg': h2h_games['ast'].mean(),
        'minutes_avg': h2h_games['minutes'].mean(),
        
        # Volatilidade
        'pts_std': h2h_games['pts'].std(),
        'reb_std': h2h_games['reb'].std(),
        'ast_std': h2h_games['ast'].std(),
        
        # Tendência
        'pts_trend': calculate_trend(h2h_games['pts']),
        'reb_trend': calculate_trend(h2h_games['reb']),
        'ast_trend': calculate_trend(h2h_games['ast']),
        
        # Over rate
        'over_rate': (h2h_games['pts'] > h2h_games['line']).mean(),
        
        # Número de jogos
        'n_games': len(h2h_games),
    }
    
    return h2h_stats

def calculate_trend(series):
    """
    Calcula tendência (slope) de uma série.
    """
    if len(series) < 2:
        return 0.0
    
    x = np.arange(len(series))
    y = series.values
    
    slope = np.polyfit(x, y, 1)[0]
    
    return slope
```

### 3.2 Ajuste por Histórico H2H

```python
def adjust_by_h2h_history(base_prediction, h2h_stats, season_avg, min_games=3):
    """
    Ajusta previsão base baseado em histórico H2H.
    
    Args:
        base_prediction: previsão base do modelo
        h2h_stats: estatísticas H2H
        season_avg: média na época (baseline)
        min_games: mínimo de jogos H2H para considerar
    
    Returns:
        adjusted_prediction: previsão ajustada
    """
    if h2h_stats is None or h2h_stats['n_games'] < min_games:
        return base_prediction
    
    # Calcular fator de ajuste
    h2h_avg = h2h_stats['pts_avg']
    adjustment_factor = h2h_avg / season_avg
    
    # Limitar ajuste (evitar overfitting)
    adjustment_factor = max(0.8, min(1.2, adjustment_factor))
    
    # Ajustar previsão
    adjusted_prediction = base_prediction * adjustment_factor
    
    return adjusted_prediction

# Exemplo
base_pred = 25.0
h2h_stats = {'pts_avg': 28.5, 'n_games': 5}
season_avg = 24.0

adjusted = adjust_by_h2h_history(base_pred, h2h_stats, season_avg)
# fator = 28.5/24.0 = 1.1875
# ajustado = 25.0 * 1.1875 = 29.7
```

---

## 4. MATCHUP DEFENSIVO INDIVIDUAL

### 4.1 Identificação de Defensor Principal

```python
def identify_primary_defender(player_id, opponent_id, game_date, lineup_data):
    """
    Identifica o defensor principal que guardará o jogador.
    
    Args:
        player_id: ID do jogador ofensivo
        opponent_id: ID da equipa adversária
        game_date: data do jogo
        lineup_data: dados de lineup da equipa adversária
    
    Returns:
        defender_id: ID do defensor principal
        defender_position: posição do defensor
    """
    # Obter lineup provável da equipa adversária
    opponent_lineup = get_probable_lineup(opponent_id, game_date, lineup_data)
    
    # Posição do jogador ofensivo
    offensive_position = get_player_position(player_id)
    
    # Encontrar defensor na mesma posição
    primary_defender = None
    for player in opponent_lineup:
        if player['position'] == offensive_position:
            primary_defender = player
            break
    
    # Se não encontrar na mesma posição, usar defensor mais próximo
    if primary_defender is None:
        primary_defender = find_closest_defender(offensive_position, opponent_lineup)
    
    return primary_defender['player_id'], primary_defender['position']
```

### 4.2 Rating Defensivo do Defensor

```python
def calculate_defender_rating(defender_id, stat_type, historical_data, window=20):
    """
    Calcula rating defensivo de um defensor para uma estatística específica.
    
    Args:
        defender_id: ID do defensor
        stat_type: PTS/REB/AST
        historical_data: dados históricos de matchup
        window: número de jogos recentes
    
    Returns:
        defender_rating: rating defensivo (0-1, menor = melhor defesa)
    """
    # Filtrar jogos onde este defensor guardou jogadores
    defender_games = historical_data[
        historical_data['primary_defender_id'] == defender_id
    ].tail(window)
    
    if len(defender_games) == 0:
        return 0.5  # Valor neutro se sem dados
    
    # Calcular média da estatística permitida
    if stat_type == 'PTS':
        avg_allowed = defender_games['opponent_pts'].mean()
    elif stat_type == 'REB':
        avg_allowed = defender_games['opponent_reb'].mean()
    elif stat_type == 'AST':
        avg_allowed = defender_games['opponent_ast'].mean()
    
    # Normalizar (0 = melhor defesa, 1 = pior defesa)
    league_avg = get_league_average(stat_type)
    rating = min(1.0, max(0.0, avg_allowed / (league_avg * 1.5)))
    
    return rating
```

### 4.3 Ajuste por Defensor

```python
def adjust_by_defender(base_prediction, defender_rating, league_avg):
    """
    Ajusta previsão baseado no rating do defensor.
    
    Args:
        base_prediction: previsão base
        defender_rating: rating do defensor (0-1)
        league_avg: média da liga
    
    Returns:
        adjusted_prediction: previsão ajustada
    """
    # Fator de ajuste baseado em rating
    # Rating 0 (melhor defesa) -> redução de 20%
    # Rating 1 (pior defesa) -> aumento de 10%
    adjustment_factor = 1.0 - (defender_rating * 0.3)
    
    # Ajustar previsão
    adjusted_prediction = base_prediction * adjustment_factor
    
    return adjusted_prediction

# Exemplo
base_pred = 25.0
defender_rating = 0.7  # Defesa média-fraca

adjusted = adjust_by_defender(base_pred, defender_rating, 24.0)
# fator = 1.0 - (0.7 * 0.3) = 0.79
# ajustado = 25.0 * 0.79 = 19.75
```

---

## 5. MATCHUP EQUIPA VS EQUIPA

### 5.1 Rating Defensivo da Equipa

```python
def calculate_team_defensive_rating(team_id, stat_type, historical_data, window=20):
    """
    Calcula rating defensivo de uma equipa para uma estatística.
    
    Args:
        team_id: ID da equipa
        stat_type: PTS/REB/AST
        historical_data: dados históricos
        window: número de jogos recentes
    
    Returns:
        team_rating: rating defensivo (0-1, menor = melhor)
    """
    # Filtrar jogos da equipa
    team_games = historical_data[
        historical_data['team_id'] == team_id
    ].tail(window)
    
    if len(team_games) == 0:
        return 0.5
    
    # Calcular média permitida
    if stat_type == 'PTS':
        avg_allowed = team_games['opponent_pts'].mean()
    elif stat_type == 'REB':
        avg_allowed = team_games['opponent_reb'].mean()
    elif stat_type == 'AST':
        avg_allowed = team_games['opponent_ast'].mean()
    
    # Normalizar
    league_avg = get_league_average(stat_type)
    rating = min(1.0, max(0.0, avg_allowed / (league_avg * 1.3)))
    
    return rating
```

### 5.2 Pace do Adversário

```python
def calculate_team_pace(team_id, historical_data, window=20):
    """
    Calcula pace (ritmo) de uma equipa.
    
    Args:
        team_id: ID da equipa
        historical_data: dados históricos
        window: número de jogos recentes
    
    Returns:
        pace: posses por 48 minutos
    """
    team_games = historical_data[
        historical_data['team_id'] == team_id
    ].tail(window)
    
    if len(team_games) == 0:
        return 100.0  # Média da liga
    
    pace = team_games['pace'].mean()
    
    return pace
```

### 5.3 Ajuste por Matchup de Equipa

```python
def adjust_by_team_matchup(
    base_prediction,
    opponent_def_rating,
    opponent_pace,
    league_pace=100.0
):
    """
    Ajusta previsão baseado em matchup de equipa.
    
    Args:
        base_prediction: previsão base
        opponent_def_rating: rating defensivo do adversário
        opponent_pace: pace do adversário
        league_pace: pace médio da liga
    
    Returns:
        adjusted_prediction: previsão ajustada
    """
    # Ajuste por defesa
    defense_factor = 1.0 - (opponent_def_rating * 0.25)
    
    # Ajuste por pace (mais pace = mais oportunidades)
    pace_factor = opponent_pace / league_pace
    
    # Ajuste combinado
    combined_factor = defense_factor * pace_factor
    
    # Limitar ajuste
    combined_factor = max(0.7, min(1.3, combined_factor))
    
    adjusted_prediction = base_prediction * combined_factor
    
    return adjusted_prediction

# Exemplo
base_pred = 25.0
opponent_def_rating = 0.6  # Defesa média
opponent_pace = 105.0  # Pace acima da média

adjusted = adjust_by_team_matchup(base_pred, opponent_def_rating, opponent_pace)
# defesa_factor = 1.0 - (0.6 * 0.25) = 0.85
# pace_factor = 105.0 / 100.0 = 1.05
# combined = 0.85 * 1.05 = 0.8925
# ajustado = 25.0 * 0.8925 = 22.3
```

---

## 6. MATCHUP ESPECÍFICO POR ESTATÍSTICA

### 6.1 Matchup para Pontos

```python
def analyze_pts_matchup(player_id, opponent_id, historical_data):
    """
    Análise de matchup específica para pontos.
    """
    # Histórico H2H
    h2h_stats = calculate_h2h_history(player_id, opponent_id, historical_data, 'PTS')
    
    # Rating defensivo da equipa
    team_def_rating = calculate_team_defensive_rating(opponent_id, 'PTS', historical_data)
    
    # Identificar defensor principal
    defender_id, _ = identify_primary_defender(player_id, opponent_id, datetime.now(), None)
    
    # Rating do defensor
    defender_rating = calculate_defender_rating(defender_id, 'PTS', historical_data)
    
    return {
        'h2h_avg': h2h_stats['pts_avg'] if h2h_stats else None,
        'team_def_rating': team_def_rating,
        'defender_rating': defender_rating,
        'overall_matchup_score': (1 - team_def_rating) * 0.6 + (1 - defender_rating) * 0.4,
    }
```

### 6.2 Matchup para Ressaltos

```python
def analyze_reb_matchup(player_id, opponent_id, historical_data):
    """
    Análise de matchup específica para ressaltos.
    """
    # Histórico H2H
    h2h_stats = calculate_h2h_history(player_id, opponent_id, historical_data, 'REB')
    
    # Rating defensivo de ressaltos da equipa
    team_def_rating = calculate_team_defensive_rating(opponent_id, 'REB', historical_data)
    
    # Identificar defensor principal (provavelmente PF/C)
    defender_id, defender_position = identify_primary_defender(player_id, opponent_id, datetime.now(), None)
    
    # Rating do defensor em ressaltos
    defender_rating = calculate_defender_rating(defender_id, 'REB', historical_data)
    
    # Fator adicional: tamanho do matchup
    player_height = get_player_height(player_id)
    defender_height = get_player_height(defender_id)
    size_advantage = (player_height - defender_height) / 10.0  # Normalizar
    
    return {
        'h2h_avg': h2h_stats['reb_avg'] if h2h_stats else None,
        'team_def_rating': team_def_rating,
        'defender_rating': defender_rating,
        'size_advantage': size_advantage,
        'overall_matchup_score': (1 - team_def_rating) * 0.5 + (1 - defender_rating) * 0.3 + size_advantage * 0.2,
    }
```

### 6.3 Matchup para Assistências

```python
def analyze_ast_matchup(player_id, opponent_id, historical_data):
    """
    Análise de matchup específica para assistências.
    """
    # Histórico H2H
    h2h_stats = calculate_h2h_history(player_id, opponent_id, historical_data, 'AST')
    
    # Rating defensivo de assistências da equipa (defesa perimetral)
    team_def_rating = calculate_team_defensive_rating(opponent_id, 'AST', historical_data)
    
    # Identificar defensor principal
    defender_id, _ = identify_primary_defender(player_id, opponent_id, datetime.now(), None)
    
    # Rating do defensor em assistências
    defender_rating = calculate_defender_rating(defender_id, 'AST', historical_data)
    
    # Fator adicional: estilo defensivo (switch vs não-switch)
    switch_frequency = get_team_switch_frequency(opponent_id, historical_data)
    switch_factor = 1.0 + (switch_frequency * 0.1)  # Mais switches = mais assistências
    
    return {
        'h2h_avg': h2h_stats['ast_avg'] if h2h_stats else None,
        'team_def_rating': team_def_rating,
        'defender_rating': defender_rating,
        'switch_factor': switch_factor,
        'overall_matchup_score': (1 - team_def_rating) * 0.5 + (1 - defender_rating) * 0.3 + (switch_factor - 1.0) * 0.2,
    }
```

---

## 7. INTEGRAÇÃO NO MODELO

### 7.1 Features de Matchup para o Modelo

```python
def create_matchup_features(player_id, opponent_id, game_date, historical_data):
    """
    Cria features de matchup para o modelo.
    """
    features = {}
    
    # Histórico H2H
    h2h_pts = calculate_h2h_history(player_id, opponent_id, historical_data, 'PTS', window=5)
    h2h_reb = calculate_h2h_history(player_id, opponent_id, historical_data, 'REB', window=5)
    h2h_ast = calculate_h2h_history(player_id, opponent_id, historical_data, 'AST', window=5)
    
    features['pts_vs_opponent_last5'] = h2h_pts['pts_avg'] if h2h_pts else None
    features['reb_vs_opponent_last5'] = h2h_reb['reb_avg'] if h2h_reb else None
    features['ast_vs_opponent_last5'] = h2h_ast['ast_avg'] if h2h_ast else None
    
    # Rating defensivo da equipa
    features['opponent_def_rating_pts'] = calculate_team_defensive_rating(opponent_id, 'PTS', historical_data)
    features['opponent_def_rating_reb'] = calculate_team_defensive_rating(opponent_id, 'REB', historical_data)
    features['opponent_def_rating_ast'] = calculate_team_defensive_rating(opponent_id, 'AST', historical_data)
    
    # Rating do defensor principal
    defender_id, _ = identify_primary_defender(player_id, opponent_id, game_date, None)
    features['defender_rating_pts'] = calculate_defender_rating(defender_id, 'PTS', historical_data)
    features['defender_rating_reb'] = calculate_defender_rating(defender_id, 'REB', historical_data)
    features['defender_rating_ast'] = calculate_defender_rating(defender_id, 'AST', historical_data)
    
    # Pace do adversário
    features['opponent_pace'] = calculate_team_pace(opponent_id, historical_data)
    
    # Matchup score combinado
    features['matchup_score_pts'] = analyze_pts_matchup(player_id, opponent_id, historical_data)['overall_matchup_score']
    features['matchup_score_reb'] = analyze_reb_matchup(player_id, opponent_id, historical_data)['overall_matchup_score']
    features['matchup_score_ast'] = analyze_ast_matchup(player_id, opponent_id, historical_data)['overall_matchup_score']
    
    return features
```

### 7.2 Ponderação de Features de Matchup

```python
# Importância relativa de features de matchup (baseado em análise histórica)
matchup_feature_weights = {
    # PTS
    'pts_vs_opponent_last5': 0.25,
    'opponent_def_rating_pts': 0.20,
    'defender_rating_pts': 0.15,
    'opponent_pace': 0.10,
    'matchup_score_pts': 0.30,
    
    # REB
    'reb_vs_opponent_last5': 0.20,
    'opponent_def_rating_reb': 0.25,
    'defender_rating_reb': 0.20,
    'size_advantage': 0.15,
    'matchup_score_reb': 0.20,
    
    # AST
    'ast_vs_opponent_last5': 0.20,
    'opponent_def_rating_ast': 0.25,
    'defender_rating_ast': 0.20,
    'switch_factor': 0.15,
    'matchup_score_ast': 0.20,
}
```

---

## 8. VALIDAÇÃO DE MATCHUP

### 8.1 Teste de Predição de Matchup

```python
def validate_matchup_predictions(historical_data, test_period_days=30):
    """
    Valida se features de matchup melhoram previsões.
    """
    # Dividir dados em treino e teste
    cutoff_date = historical_data['game_date'].max() - pd.Timedelta(days=test_period_days)
    train_data = historical_data[historical_data['game_date'] < cutoff_date]
    test_data = historical_data[historical_data['game_date'] >= cutoff_date]
    
    # Modelo sem features de matchup
    model_without = train_model(train_data, include_matchup=False)
    preds_without = model_without.predict(test_data)
    
    # Modelo com features de matchup
    model_with = train_model(train_data, include_matchup=True)
    preds_with = model_with.predict(test_data)
    
    # Comparar erro
    mae_without = mean_absolute_error(test_data['pts'], preds_without)
    mae_with = mean_absolute_error(test_data['pts'], preds_with)
    
    improvement = (mae_without - mae_with) / mae_without
    
    return {
        'mae_without': mae_without,
        'mae_with': mae_with,
        'improvement': improvement,
        'matchup_helpful': improvement > 0.05,  # 5% de melhoria
    }
```

---

## 9. BACKLOG

- [ ] Implementar cálculo de histórico H2H
- [ ] Implementar identificação de defensor principal
- [ ] Implementar cálculo de rating defensivo
- [ ] Implementar cálculo de pace de equipa
- [ ] Implementar análise de matchup por estatística
- [ ] Integrar features de matchup no modelo
- [ ] Validar se features de matchup melhoram previsões
- [ ] Calibrar ponderação de features de matchup
- [ ] Documentar matchups mais favoráveis/desfavoráveis por jogador

---

## 10. LINKS CRUZADOS

- [[42_Player_Props/INDEX]] ← Secção mãe
- [[42_Player_Props/FEATURES_JOGADOR]] → Features gerais
- [[42_Player_Props/MODELACAO_PLAYER_PROPS]] → Modelagem