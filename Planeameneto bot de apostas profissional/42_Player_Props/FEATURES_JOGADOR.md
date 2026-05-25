# FEATURES_JOGADOR — Feature Engineering para Player Props

**ID:** `PP-003` | **Fase:** #phase/6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Definir o conjunto de features específicas para player props, focando em métricas de desempenho individual, contexto de matchup, e fatores de utilização que influenciam a produção estatística de jogadores NBA.

---

## 2. CATEGORIAS DE FEATURES

### 2.1 Histórico de Desempenho

Features que capturam a tendência recente de produção do jogador.

```python
historical_features = {
    # Médias móveis de pontos
    "pts_last1": float,          # Pontos no jogo anterior
    "pts_last3": float,          # Média últimos 3 jogos
    "pts_last5": float,          # Média últimos 5 jogos
    "pts_last10": float,         # Média últimos 10 jogos
    "pts_season_avg": float,     # Média da época
    
    # Volatilidade (importante para calibração)
    "pts_std_last5": float,      # Desvio padrão últimos 5 jogos
    "pts_std_last10": float,     # Desvio padrão últimos 10 jogos
    "pts_cv_last5": float,       # Coeficiente de variação últimos 5
    
    # Tendência
    "pts_trend_5": float,        # Tendência últimos 5 jogos (slope)
    "pts_trend_10": float,       # Tendência últimos 10 jogos
    
    # Mesma lógica para REB e AST
    "reb_last5": float,
    "reb_last10": float,
    "reb_std_last5": float,
    "ast_last5": float,
    "ast_last10": float,
    "ast_std_last5": float,
}
```

### 2.2 Matchup Específico

Features que capturam como o jogador performa contra adversários específicos.

```python
matchup_features = {
    # Histórico head-to-head
    "pts_vs_opponent_last3": float,    # Média vs esta equipa últimos 3
    "pts_vs_opponent_season": float,   # Média vs esta equipa na época
    "reb_vs_opponent_last3": float,
    "reb_vs_opponent_season": float,
    "ast_vs_opponent_last3": float,
    "ast_vs_opponent_season": float,
    
    # Defensor principal (matchup individual)
    "primary_defender_rating": float,  # Rating defensivo do defensor
    "defender_position_match": bool,   # True se mesmo tamanho/posição
    "defender_allow_pts": float,       # Pontos que o defensor permite em média
    
    # Defesa da equipa adversária
    "opponent_def_rating": float,      # Rating defensivo da equipa
    "opponent_pts_allowed": float,     # Pontos permitidos pela equipa
    "opponent_reb_allowed": float,     # Ressaltos permitidos
    "opponent_ast_allowed": float,     # Assistências permitidas
    
    # Estilo de defesa
    "opponent_pace_rank": int,         # Rank de ritmo da equipa
    "opponent_switch_freq": float,     # Frequência de switches defensivos
}
```

### 2.3 Uso e Role

Features que capturam o papel do jogador na ofensiva da sua equipa.

```python
usage_features = {
    # Taxa de uso (fundamental)
    "usage_rate": float,           # % de posses que terminam em ação do jogador
    "usage_rate_last5": float,     # Taxa de uso últimos 5 jogos
    "usage_rate_season": float,    # Taxa de uso na época
    
    # Envolvimento ofensivo
    "touch_rate": float,           # % de posses em que toca na bola
    "touches_per_game": float,     # Toques por jogo
    "time_of_possession": float,   # Tempo de posse por jogo
    
    # Role na equipa
    "is_starter": bool,            # Titular ou suplente
    "starter_last5": bool,         # Foi titular últimos 5 jogos
    "is_primary_scorer": bool,     # É o 1º ou 2º scorer da equipa
    "is_playmaker": bool,          # É o playmaker principal
    
    # Shot distribution
    "fga_per_game": float,         # Field goals attempts por jogo
    "fga_rate_last5": float,       # Tentativas últimos 5 jogos
    "three_pt_rate": float,        # % de arremessos de 3 pontos
    "fta_rate": float,             # % de arremessos livres
    
    # Playmaking
    "potential_ast_per_game": float,  # Assistências potenciais (hockey assists)
    "pass_rate": float,            # % de posses que termina em passe
}
```

### 2.4 Minutos e Disponibilidade

Features que capturam o tempo de jogo e disponibilidade do jogador.

```python
minutes_features = {
    # Minutos jogados
    "minutes_last1": float,        # Minutos jogo anterior
    "minutes_last3": float,        # Média últimos 3 jogos
    "minutes_last5": float,        # Média últimos 5 jogos
    "minutes_last10": float,       # Média últimos 10 jogos
    "minutes_season_avg": float,   # Média da época
    
    # Projeção de minutos
    "minutes_projected": float,    # Minutos projetados para este jogo
    "minutes_projected_reason": str, # Razão da projeção (baseline/matchup/rest)
    
    # Fatores que afetam minutos
    "rest_days": int,              # Dias de descanso
    "is_back_to_back": bool,       # Jogo consecutivo
    "is_3_in_4": bool,             # 3 jogos em 4 noites
    "is_4_in_5": bool,             # 4 jogos em 5 noites
    
    # Situação de lesão
    "injury_status": str,          # healthy/questionable/doubtful/out
    "injury_body_part": str,       # Parte do corpo afetada
    "days_since_injury": int,      # Dias desde lesão
    "was_injured_last": bool,      # Esteve lesionado no jogo anterior
    
    # Situação de lineup
    "teammate_injured": bool,      # Companheiro lesionado (aumenta uso)
    "teammate_injured_impact": float, # Impacto esperado no uso
}
```

### 2.5 Contexto do Jogo

Features que capturam o contexto do jogo específico.

```python
game_context_features = {
    # Linhas do jogo
    "game_total_line": float,      # Linha de total do jogo
    "game_spread_line": float,     # Linha de spread
    
    # Situação da equipa
    "team_is_favored": bool,       # Equipa é favorita
    "team_spread": float,          # Spread da equipa
    "team_expected_pace": float,   # Ritmo esperado baseado no matchup
    
    # Sitação de playoff
    "is_playoff": bool,            # Jogo de playoff
    "playoff_round": str,          # Rodada (first/second/conf/finals)
    "is_elimination": bool,        # Jogo de eliminação
    
    # Situação de standings
    "team_playoff_spot_secure": bool,    # Vaga playoff garantida
    "team_tanking": bool,          # Equipa a perder propositadamente
    "opponent_tanking": bool,      # Adversário a perder propositadamente
}
```

### 2.6 Fatores de Blowout

Features que preveem probabilidade de blowout (que afeta minutos).

```python
blowout_features = {
    # Probabilidade de blowout
    "blowout_prob": float,         # Probabilidade de vitória por >15 pontos
    "blowout_risk_team": float,    # Risco de blowout para a equipa
    "blowout_risk_opponent": float, # Risco de blowout para o adversário
    
    # Fatores que aumentam blowout
    "spread_large": bool,          # Spread >10 pontos
    "talent_gap": float,           # Diferença de talento entre equipas
    "rest_advantage": bool,        # Vantagem de descanso significativa
    
    # Histórico de blowout
    "team_blowout_rate": float,    # % de jogos que terminaram em blowout
    "opponent_blowout_rate": float, # % de jogos que terminaram em blowout
}
```

---

## 3. ENGENHARIA DE FEATURES AVANÇADA

### 3.1 Features Compostas

Combinações de features que capturam interações complexas.

```python
composite_features = {
    # PRA (Points + Rebounds + Assists)
    "pra_last5": float,            # PRA últimos 5 jogos
    "pra_last10": float,           # PRA últimos 10 jogos
    "pra_projected": float,        # PRA projetado
    
    # Eficiência ajustada por minutos
    "pts_per_36_last5": float,     # Pontos por 36 minutos últimos 5
    "reb_per_36_last5": float,     # Ressaltos por 36 minutos últimos 5
    "ast_per_36_last5": float,     # Assistências por 36 minutos últimos 5
    
    # Uso ajustado por matchup
    "usage_vs_weak_def": float,    # Uso contra defesas fracas
    "usage_vs_strong_def": float,  # Uso contra defesas fortes
    
    # Sinergia com companheiros
    "usage_with_star_injured": float, # Uso quando estrela ausente
    "usage_with_star_active": float,  # Uso quando estrela presente
}
```

### 3.2 Features de Momentum

Capturam se o jogador está em "hot streak" ou "cold streak".

```python
momentum_features = {
    # Hot/Cold streaks
    "is_hot_streak": bool,         # Acima da média últimos 3 jogos
    "is_cold_streak": bool,        # Abaixo da média últimos 3 jogos
    "streak_length": int,          # Comprimento do streak atual
    
    # Performance vs projeção
    "over_line_rate_last5": float, # % de vezes que passou a linha últimos 5
    "over_line_rate_last10": float,# % de vezes que passou a linha últimos 10
    
    # Consistência
    "consistency_score": float,    # Score de consistência (1 = muito consistente)
    "volatility_score": float,     # Score de volatilidade (1 = muito volátil)
}
```

### 3.3 Features de Situação Específica

Capturam situações específicas que afetam a produção.

```python
situational_features = {
    # Situação de home/away
    "pts_home_avg": float,         # Média pontos em casa
    "pts_away_avg": float,         # Média pontos fora
    "home_vs_away_diff": float,    # Diferença casa vs fora
    
    # Situação de primetime
    "is_national_tv": bool,        # Jogo na TV nacional
    "pts_primetime_avg": float,    # Média em jogos na TV
    
    # Situação de rivalidade
    "is_rivalry": bool,            # Jogo de rivalidade
    "pts_rivalry_avg": float,      # Média em jogos de rivalidade
    
    # Situação de retorno
    "is_return_to_old_team": bool, # Jogo contra antiga equipa
    "pts_vs_old_team": float,      # Média contra antiga equipa
}
```

---

## 4. PREVENÇÃO DE LEAKAGE

### 4.1 Regras de Temporalidade

Todas as features devem ser calculadas apenas com dados disponíveis antes do jogo.

```python
def calculate_player_features(game_date, player_id, historical_data):
    """
    Calcula features para um jogador num jogo específico.
    
    CRÍTICO: Usar apenas dados com data < game_date
    """
    
    # Filtrar dados históricos antes do jogo
    historical_before = historical_data[
        historical_data['game_date'] < game_date
    ]
    
    # Calcular médias móveis
    last_5 = historical_before.tail(5)
    features['pts_last5'] = last_5['pts'].mean()
    
    # Calcular matchup (usar dados históricos do adversário)
    opponent_games = historical_before[
        historical_before['opponent_id'] == opponent_id
    ]
    features['pts_vs_opponent'] = opponent_games['pts'].mean()
    
    return features
```

### 4.2 Validação de Leakage

```python
def validate_no_leakage(features_df, game_dates):
    """
    Valida que nenhuma feature usa dados futuros.
    """
    for idx, row in features_df.iterrows():
        game_date = row['game_date']
        
        # Para cada feature numérica
        for col in features_df.columns:
            if col not in ['game_date', 'player_id', 'game_id']:
                # Verificar que o valor é plausível
                # (ex: média não pode ser maior que max histórico)
                pass
    
    return True
```

---

## 5. SELEÇÃO DE FEATURES

### 5.1 Importância de Features

Usar XGBoost feature importance para identificar features mais relevantes.

```python
import xgboost as xgb

def get_feature_importance(X, y):
    model = xgb.XGBRegressor(
        max_depth=4,
        learning_rate=0.05,
        n_estimators=100,
        random_state=42
    )
    
    model.fit(X, y)
    
    importance = model.feature_importances_
    feature_names = X.columns
    
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    return importance_df
```

### 5.2 Features Esperadas como Mais Importantes

Baseado em experiência em player props NBA:

1. **Minutes projected** - Fator mais importante
2. **Usage rate** - Determina oportunidades
3. **Pts last 5/10** - Tendência recente
4. **Matchup vs opponent** - Histórico específico
5. **Injury status** - Disponibilidade
6. **Blowout risk** - Risco de redução de minutos
7. **Usage with star injured** - Aumento de role
8. **Defender rating** - Dificuldade defensiva

---

## 6. ARMAZENAMENTO DE FEATURES

### 6.1 Schema de Base de Dados

```sql
CREATE TABLE player_features (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    player_id VARCHAR(50) NOT NULL,
    game_date DATE NOT NULL,
    
    -- Histórico
    pts_last5 FLOAT,
    pts_last10 FLOAT,
    reb_last5 FLOAT,
    reb_last10 FLOAT,
    ast_last5 FLOAT,
    ast_last10 FLOAT,
    
    -- Matchup
    pts_vs_opponent FLOAT,
    opponent_def_rating FLOAT,
    
    -- Uso
    usage_rate FLOAT,
    usage_rate_last5 FLOAT,
    is_starter BOOLEAN,
    
    -- Minutos
    minutes_last5 FLOAT,
    minutes_projected FLOAT,
    injury_status VARCHAR(20),
    
    -- Contexto
    game_total_line FLOAT,
    blowout_prob FLOAT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_game_player UNIQUE (game_id, player_id)
);

CREATE INDEX idx_player_features_game ON player_features(game_id);
CREATE INDEX idx_player_features_player ON player_features(player_id);
CREATE INDEX idx_player_features_date ON player_features(game_date);
```

---

## 7. BACKLOG

- [ ] Implementar cálculo de todas as features de histórico
- [ ] Implementar cálculo de features de matchup
- [ ] Implementar cálculo de features de uso e role
- [ ] Implementar cálculo de features de minutos
- [ ] Implementar cálculo de features de contexto
- [ ] Implementar validação de leakage temporal
- [ ] Criar pipeline de feature engineering automatizado
- [ ] Analisar feature importance em dados históricos
- [ ] Documentar features mais importantes por mercado (PTS/REB/AST)

---

## 8. LINKS CRUZADOS

- [[42_Player_Props/INDEX]] ← Secção mãe
- [[42_Player_Props/DIFERENCAS_TEAM_VS_PLAYER]] → Diferenças fundamentais
- [[42_Player_Props/MODELACAO_PLAYER_PROPS]] → Modelagem com estas features
- [[05_Machine_Learning/LEAKAGE_PREVENTION]] → Prevenção de leakage