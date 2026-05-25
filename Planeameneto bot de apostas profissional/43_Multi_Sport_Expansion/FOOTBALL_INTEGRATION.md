# FOOTBALL INTEGRATION — Estratégia Detalhada

**ID:** `SEC-43-01` | **Status:** #status/pending | **Versão:** `2.0.0-FOOTBALL`

---

## 1. OBJETIVO

Expandir o sistema para incluir Futebol com modelo Poisson/ML e edge estimado de 4-6%.

---

## 2. MERCADOS PRIORITÁRIOS

### 2.1 Tipos de Mercados

| Mercado | Edge Estimado | Volume | Prioridade |
|---------|---------------|--------|------------|
| **Asian Handicap** | 4-5% | Alto | MÁXIMA |
| **Over/Under Goals** | 3-4% | Alto | MÁXIMA |
| **Cantos Asiáticos** | 5-7% | Médio | ALTA |
| **Cartões Asiáticos** | 5-7% | Médio | ALTA |
| **Correct Score** | 6-8% | Baixo | MÉDIA |
| **Both Teams to Score** | 3-4% | Médio | MÉDIA |

### 2.2 Ligas Prioritárias

**Ligas Principais (Alta Liquidez):**
- Premier League (Inglaterra)
- La Liga (Espanha)
- Bundesliga (Alemanha)
- Serie A (Itália)
- Ligue 1 (França)

**Ligas Secundárias (Maior Edge):**
- Championship (Inglaterra)
- Segunda Divisão (Espanha)
- 2. Bundesliga (Alemanha)
- Serie B (Itálça)

---

## 3. DADOS E FONTES

### 3.1 Dados de Equipas

```python
# Fontes de dados
football_api_sources = [
    "Football-Data.org",  # Dados históricos gratuitos
    "API-Football",      # Dados em tempo real
    "Betfair Exchange",  # Odds de mercado
    "Opta",             # Dados avançados (pagos)
]

# Dados necessários
required_data = {
    'team_form': ['last_5_results', 'last_10_results', 'goals_scored', 'goals_conceded'],
    'head_to_head': ['last_5_meetings', 'home_wins', 'away_wins', 'draws'],
    'home_away_form': ['home_record', 'away_record', 'home_goals', 'away_goals'],
    'injuries': ['injured_players', 'suspended_players', 'importance'],
    'lineups': ['expected_lineup', 'formation', 'key_players'],
}
```

---

## 4. MODELO PREDITIVO

### 4.1 Arquitetura Híbrida (Poisson + ML)

```
┌─────────────────────────────────────────┐
│         FEATURES (60-70)                 │
│  Forma │ H2H │ Home/Away │ Lesões       │
└──────────────┬──────────────────────────┘
               │
         ┌─────┴─────┐
         ▼           ▼
┌─────────────┐ ┌─────────────┐
│   Poisson   │ │    XGBoost  │
│  (Goals)    │ │  (Outcome)  │
└──────┬──────┘ └──────┬──────┘
       │                │
       └───────┬────────┘
               ▼
┌─────────────────────────────────────────┐
│      COMBINAÇÃO ENSEMBLE                 │
│  P(goals) × P(outcome) = P(final)       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         CÁLCULO DE EDGE                 │
│  edge = (P_model × odd) - 1            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      GESTÃO DE RISCO (Kelly)             │
└─────────────────────────────────────────┘
```

### 4.2 Modelo Poisson para Goals

```python
import numpy as np
from scipy.stats import poisson

class PoissonFootballModel:
    """
    Modelo Poisson para previsão de goals.
    """
    def __init__(self):
        self.home_attack = {}
        self.home_defense = {}
        self.away_attack = {}
        self.away_defense = {}
        self.home_advantage = 0.0
    
    def fit(self, historical_data):
        """
    Ajusta parâmetros do modelo Poisson com dados históricos.
        """
        # Calcular médias de goals por equipa
        for team in get_all_teams():
            home_games = historical_data[historical_data['home_team'] == team]
            away_games = historical_data[historical_data['away_team'] == team]
            
            # Attack strength (goals scored)
            self.home_attack[team] = home_games['home_goals'].mean() / league_avg_home_goals
            self.away_attack[team] = away_games['away_goals'].mean() / league_avg_away_goals
            
            # Defense strength (goals conceded)
            self.home_defense[team] = home_games['away_goals'].mean() / league_avg_away_goals
            self.away_defense[team] = away_games['home_goals'].mean() / league_avg_home_goals
        
        # Vantagem de jogar em casa
        self.home_advantage = historical_data['home_goals'].mean() - historical_data['away_goals'].mean()
    
    def predict_goals(self, home_team, away_team):
        """
        Prevê goals esperados para cada equipa.
        """
        # Home team goals
        home_expected = self.home_attack[home_team] * self.away_defense[away_team] * \
                       league_avg_home_goals * (1 + self.home_advantage * 0.1)
        
        # Away team goals
        away_expected = self.away_attack[away_team] * self.home_defense[home_team] * \
                       league_avg_away_goals * (1 - self.home_advantage * 0.1)
        
        return home_expected, away_expected
    
    def predict_score_probability(self, home_team, away_team, max_goals=5):
        """
        Prevê probabilidade de cada placar.
        """
        home_expected, away_expected = self.predict_goals(home_team, away_team)
        
        probabilities = {}
        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                prob = poisson.pmf(home_goals, home_expected) * \
                       poisson.pmf(away_goals, away_expected)
                probabilities[(home_goals, away_goals)] = prob
        
        return probabilities
```

### 4.3 Modelo XGBoost para Outcome

```python
from xgboost import XGBClassifier

football_model_config = {
    "objective": "multi:softprob",
    "eval_metric": ["mlogloss", "merror"],
    "num_class": 3,  # Home, Draw, Away
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 30,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "tree_method": "hist",
    "seed": 42,
    "n_estimators": 1000,
}
```

---

## 5. FEATURES PARA FUTEBOL

### 5.1 Features de Forma (20 features)

```python
# Forma recente
home_form_last_5 = results_last_5_home
away_form_last_5 = results_last_5_away
home_goals_last_5 = goals_scored_last_5_home
away_goals_last_5 = goals_scored_last_5_away
home_conceded_last_5 = goals_conceded_last_5_home
away_conceded_last_5 = goals_conceded_last_5_away

# Consistência
home_points_last_10 = sum(points_last_10_home) / 30  # Máx 3 pts por jogo
away_points_last_10 = sum(points_last_10_away) / 30
home_win_rate_last_10 = wins_last_10_home / 10
away_win_rate_last_10 = wins_last_10_away / 10
```

### 5.2 Features Head-to-Head (10 features)

```python
h2h_home_wins = count(home_wins_last_5_meetings)
h2h_away_wins = count(away_wins_last_5_meetings)
h2h_draws = count(draws_last_5_meetings)
h2h_home_goals = sum(home_goals_last_5_meetings) / 5
h2h_away_goals = sum(away_goals_last_5_meetings) / 5
```

### 5.3 Features Home/Away (10 features)

```python
home_advantage_home_team = home_win_rate_at_home
home_advantage_away_team = away_win_rate_away
home_goals_at_home = avg_goals_when_home
away_goals_when_away = avg_goals_when_away
home_conceded_at_home = avg_conceded_when_home
away_conceded_when_away = avg_conceded_when_away
```

### 5.4 Features de Lesões (10 features)

```python
home_injured_count = count_injured_players(home_team)
away_injured_count = count_injured_players(away_team)
home_injured_importance = avg_importance_injured(home_team)
away_injured_importance = avg_importance_injured(away_team)
home_suspended_count = count_suspended_players(home_team)
away_suspended_count = count_suspended_players(away_team)
```

### 5.5 Features de Mercado (10 features)

```python
opening_odd_home = get_opening_odd(home_team)
current_odd_home = get_current_odd(home_team)
odd_movement_home = (current_odd_home - opening_odd_home) / opening_odd_home
total_matched_volume = get_total_matched(market_id)
spread_width = best_back_odd - best_lay_odd
```

---

## 6. GESTÃO DE RISCO ESPECÍFICA PARA FUTEBOL

### 6.1 Stake por Mercado

```python
def calculate_football_stake(edge, market_type, bankroll):
    """
    Calcula stake para futebol considerando tipo de mercado.
    """
    base_stake = kelly_fraction(edge, bankroll)
    
    # Ajustar por volatilidade do mercado
    volatility_adjustment = {
        'asian_handicap': 1.0,
        'over_under': 0.9,
        'corners': 0.7,
        'cards': 0.7,
        'correct_score': 0.5
    }
    
    final_stake = base_stake * volatility_adjustment.get(market_type, 0.8)
    
    # Limitar a 1.5% da banca por aposta (mais conservativo que NBA)
    final_stake = min(final_stake, 0.015 * bankroll)
    
    return final_stake
```

### 6.2 Limites de Exposição

- Máximo 3 apostas por jogo (handicap + over/under + corner)
- Máximo 5 jogos por dia
- Máximo 3% da banca total em futebol por dia
- Evitar correlação alta entre mercados do mesmo jogo

---

## 7. CRONOGRAMA DE IMPLEMENTAÇÃO

**Mês 4-5:** Coleta de dados históricos de futebol
**Mês 6:** Feature engineering para futebol
**Mês 7:** Treino e validação de modelo Poisson + XGBoost
**Mês 8:** Shadow mode (sem apostas reais)
**Mês 9:** Produção com banca reduzida (5% da banca total)
**Mês 10-12:** Expansão para mercados secundários (cantos, cartões)

---

## 8. CRITÉRIOS DE SUCESSO

| Critério | Threshold |
|----------|-----------|
| RMSE (goals) | < 1.2 goals |
| Brier Score (outcome) | < 0.20 |
| CLV médio | > 4% |
| ROI simulado | > 6% |
| Sharpe Ratio | > 0.7 |

---

## 9. NOTAS DETALHADAS

### 9.1 xG (Expected Goals) e Métricas Avançadas

**Importância do xG:**
- xG mede a qualidade de chances criadas independentemente do resultado
- Diferença entre xG e golos reais indica over/underperformance
- xG é mais preditivo de resultados futuros que golos simples

**Fontes de xG:**
- Understat (gratuito, cobre top 5 ligas europeias)
- Footystats (pago, mais detalhado)
- FBref (gratuito, xG básico)

**Features de xG:**
```python
# xG features
home_xg_last_5 = avg_xg_created_last_5_home
away_xg_last_5 = avg_xg_created_last_5_away
home_xg_conceded_last_5 = avg_xg_conceded_last_5_home
away_xg_conceded_last_5 = avg_xg_conceded_last_5_away

# xG difference (over/underperformance)
home_xg_diff_last_10 = (goals_scored - xg_created)_last_10_home
away_xg_diff_last_10 = (goals_scored - xg_created)_last_10_away

# xG per shot (qualidade de chances)
home_xg_per_shot = xg_created / shots
away_xg_per_shot = xg_created / shots
```

**Nota Crítica:** xG é mais importante em ligas secundárias onde a análise pública é menos sofisticada.

### 9.2 Eficiência de Mercado em Futebol

**Mercado Eficiente vs Ineficiente:**
- Ligas principais (EPL, La Liga): Alta eficiência, edge menor (3-4%)
- Ligas secundárias (Championship, 2. Bundesliga): Menor eficiência, edge maior (5-7%)
- Ligas terciárias: Ineficiência significativa, edge maior (7-10%) mas liquidez baixa

**Estratégia:**
- Começar com ligas secundárias onde edge/liquidez é ótimo
- Monitorizar eficiência de mercado em tempo real
- Reduzir stakes se liquidez cair abaixo de threshold

**Métricas de Eficiência:**
```python
# Liquidity metrics
total_matched = get_total_matched(market_id)
spread_width = best_back_odd - best_lay_odd
depth_at_price = get_depth_at_price(market_id, current_odd)

# Efficiency metrics
closing_line_value = (opening_odd - closing_odd) / opening_odd
market_movement_volatility = std(odd_changes_last_24h)
sharp_money_indicator = detect_sharp_bets(odd_history)
```

### 9.3 Handling de Lesões

**Impacto de Lesões:**
- Lesão de jogador chave (top scorer): -0.15 a -0.25 em probabilidade de vitória
- Lesão de defensor central: +0.05 a +0.10 em probabilidade de over goals
- Lesão de goleiro: +0.10 a +0.20 em probabilidade de over goals

**Fontes de Lesões:**
- Transfermarkt (mais completo)
- RSS (oficial, mas menos detalhado)
- Twitter (rápido, mas não estruturado)
- SofaScore (bom para status em tempo real)

**Scoring de Importância:**
```python
def score_injury_impact(player, position, minutes_played):
    """
    Score impacto de lesão (0-1).
    """
    base_impact = {
        'goalkeeper': 0.8,
        'center_back': 0.7,
        'midfielder': 0.5,
        'forward': 0.6
    }
    
    # Ajustar por minutos jogados
    minutes_adjustment = minutes_played / 90
    
    # Ajustar por importância na equipa
    importance_adjustment = player_importance_rating / 10
    
    final_score = base_impact[position] * minutes_adjustment * importance_adjustment
    
    return final_score
```

### 9.4 Timing de Apostas

**Pré-Jogo vs In-Play:**
- **Pré-Jogo:** Mais previsível, menor volatilidade, edge menor (3-4%)
- **In-Play:** Menos previsível, maior volatilidade, edge maior (5-7%) mas maior risco

**Recomendação:** Começar com pré-jogo. In-play apenas após validação pré-jogo estável.

**Timing Ótimo Pré-Jogo:**
- 1-2 horas antes do jogo: odds estabilizadas, liquidez boa
- 30 minutos antes do jogo: lineups confirmados, ajuste por lesões
- 10 minutos antes do jogo: liquidez máxima, mas odds mais eficientes

**Notas:**
- Evitar apostas muito cedo (24h antes) - odds podem mudar drasticamente
- Monitorizar lineups até 30 minutos antes - lesões tardias podem invalidar modelo

### 9.5 Correlação Entre Mercados

**Correlações Naturais:**
- Home win e Over 2.5: +0.3 a +0.5 (positiva)
- Away win e Over 2.5: +0.2 a +0.4 (positiva)
- Home win e Under 2.5: -0.3 a -0.5 (negativa)

**Risco de Correlação:**
- Apostar em Home win + Over 2.5 no mesmo jogo aumenta risco
- Se Home perde, Over 2.5 também perde frequentemente
- Limitar exposição total por jogo a 4% da banca

**Estratégia de Diversificação:**
- Apostar em jogos diferentes para reduzir correlação
- Se apostar no mesmo jogo, escolher mercados com correlação negativa (Home win + Under 2.5)

### 9.6 Features de Contexto Adicionais

**Fatores Externos:**
```python
# Competição europeia
days_since_europa_match = days_since_last_europa_game(home_team)
europa_fatigue_score = calculate_europa_fatigue(home_team)

# Rebaixamento/Promoção
relegation_risk_home = probability_of_relegation(home_team)
promotion_race_home = probability_of_promotion(home_team)

# Motivação
motivation_score = assess_motivation(home_team, away_team, season_stage)
manager_importance = is_manager_under_pressure(home_team)

# Clima/Condições
weather_condition = get_weather(match_stadium)
pitch_quality = get_pitch_condition(match_stadium)
```

### 9.7 Modelagem Dixon-Coles (Avançado)

**Modelo Dixon-Coles:**
- Extensão do Poisson que ajusta para correlação em scores baixos
- 0-0 ocorre mais frequentemente que Poisson puro prevê
- 1-0 e 0-1 também são mais frequentes

**Implementação:**
```python
def dixon_coles_correction(rho, home_goals, away_goals):
    """
    Ajuste Dixon-Coles para correlação.
    """
    if home_goals == 0 and away_goals == 0:
        return 1 - rho
    elif home_goals == 1 and away_goals == 0:
        return 1 + rho
    elif home_goals == 0 and away_goals == 1:
        return 1 + rho
    else:
        return 1 - rho

# rho é estimado a partir de dados históricos
# Típico: rho = -0.1 a -0.2 para futebol
```

**Nota:** Dixon-Coles é mais preciso para placares específicos (Correct Score), mas computacionalmente mais pesado.

### 9.8 Backtesting Específico

**Purged CV com Embargo:**
- Purge: Remover dados de 7 dias antes e 7 dias após cada jogo
- Embargo: Não usar dados de jogos futuros no treino
- Previne data leakage em séries temporais

**Validação Out-of-Sample:**
- Treinar em temporadas 2019-2022
- Validar em temporada 2023-2024
- Testar em temporada 2024-2025 (não usada em treino)

**Métricas de Validação:**
```python
# Calcular CLV por tipo de aposta
clv_handicap = calculate_clv(handicap_bets)
clv_over_under = calculate_clv(over_under_bets)
clv_corners = calculate_clv(corner_bets)

# Calcular ROI por tipo de aposta
roi_handicap = calculate_roi(handicap_bets)
roi_over_under = calculate_roi(over_under_bets)
roi_corners = calculate_roi(corner_bets)

# Identificar mercados com melhor edge
best_market = argmax([clv_handicap, clv_over_under, clv_corners])
```

### 9.9 Notas de Produção

**Execução em Futebol:**
- Odds em futebol são mais voláteis que NBA (mais movimentos)
- Liquidez em ligas secundárias pode ser inconsistente
- Limite orders podem expirar sem ser preenchidas

**Recomendações:**
- Usar limit orders com timeout de 30 segundos
- Monitorizar liquidez antes de cada aposta
- Reduzir stakes se liquidez < 50% do esperado
- Evitar apostas nos últimos 5 minutos antes do jogo (volatilidade extrema)

---

## 10. LINKS CRUZADOS

- [[43_Multi_Sport_Expansion/INDEX]] ← Secção mãe
- [[43_Multi_Sport_Expansion/MMA_INTEGRATION]] → MMA/UFC
- [[43_Multi_Sport_Expansion/UNIFIED_DECISION_ENGINE]] → Motor unificado
- [[05_Machine_Learning/ENSEMBLE_STACKING]] → Ensemble NBA
- [[08_Risk_Management/EXIT_CRITERIA_SPORT]] → Exit criteria
