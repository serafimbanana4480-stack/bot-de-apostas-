# ⚙️ Feature Engineering

**Componente:** Machine Learning  
**Status:** 🚧 Em desenvolvimento (75%)  
**Responsável:** ML Engineer  
**Última atualização:** 2026-05-19

---

## 🎯 Objetivo

Transformar dados brutos em features preditivas de alta qualidade que capturem padrões relevantes para prever resultados de jogos NBA.

---

## 🏗️ Arquitetura

### Categorias de Features

| Categoria | Features | Fonte | Importância |
|-----------|----------|-------|-------------|
| **Form Features** | 25 | Estatísticas recentes | Alta |
| **Context Features** | 15 | Contexto do jogo | Alta |
| **Market Features** | 20 | Movimento de odds | Média |
| **Lookahead Features** | 10 | Agenda futura | Média |
| **Historical Features** | 10 | Histórico head-to-head | Baixa |

**Total:** 80+ features

---

## 🔧 Componentes Técnicos

### 1. Form Features

**Arquivo:** `src/features/form.py`

**Descrição:** Captura a forma recente de equipas e jogadores

**Features principais:**
```python
# Rolling averages (últimos 5, 10, 20 jogos)
- points_per_game_5
- points_per_game_10
- points_per_game_20
- field_goal_pct_5
- three_point_pct_5
- free_throw_pct_5
- rebounds_per_game_5
- assists_per_game_5
- turnovers_per_game_5

# Diferenças home/away
- home_away_points_diff
- home_away_fg_pct_diff

# Momentum
- last_5_win_pct
- last_10_win_pct
- streak_current
```

**Implementação:**
```python
def calculate_rolling_stats(team_id, window):
    games = get_recent_games(team_id, window)
    return {
        'points_per_game': games['points'].mean(),
        'fg_pct': games['fg_made'] / games['fg_attempted'],
        'three_pct': games['three_made'] / games['three_attempted'],
        # ...
    }
```

### 2. Context Features

**Arquivo:** `src/features/context.py`

**Descrição:** Captura o contexto específico do jogo

**Features principais:**
```python
# Localização
- is_home_game (bool)
- days_since_home_game
- days_since_away_game

# Fadiga
- back_to_back (bool)
- back_to_back_away (bool)
- days_rest
- travel_distance

# Injuries
- key_players_injured_count
- key_players_injured_importance
- injury_score

# Motivação
- playoff_implication (bool)
- division_rival (bool)
- revenge_game (bool)
```

**Implementação:**
```python
def calculate_context_features(game):
    return {
        'is_home_game': game.home_team == team_id,
        'days_rest': (game.date - last_game_date).days,
        'back_to_back': (game.date - last_game_date).days == 1,
        'injury_score': calculate_injury_impact(team_id),
        # ...
    }
```

### 3. Market Features

**Arquivo:** `src/features/market.py`

**Descrição:** Captura movimento e consenso de mercado

**Features principais:**
```python
# Odds movement
- opening_odds_home
- current_odds_home
- odds_movement_home
- odds_movement_pct_home

# Consensus
- bookmaker_consensus_home
- bookmaker_std_home
- betfair_volume_home
- betfair_volume_away

# Line movement
- opening_spread
- current_spread
- spread_movement
- total_movement
```

**Implementação:**
```python
def calculate_market_features(game):
    odds_history = get_odds_history(game.game_id)
    return {
        'opening_odds_home': odds_history[0].home_odds,
        'current_odds_home': odds_history[-1].home_odds,
        'odds_movement': odds_history[-1].home_odds - odds_history[0].home_odds,
        'bookmaker_consensus': calculate_consensus(odds_history),
        # ...
    }
```

### 4. Lookahead Features

**Arquivo:** `src/features/lookahead.py`

**Descrição:** Captura impacto da agenda futura

**Features principais:**
```python
# Agenda futura
- games_next_7_days
- games_next_14_days
- difficult_games_next_7
- easy_games_next_7

# Rivalidades
- is_division_game
- is_conference_game
- historical_win_pct_vs_opponent

# Importância
- playoff_probability_impact
- tanking_probability (end of season)
```

**Implementação:**
```python
def calculate_lookahead_features(team_id, current_date):
    future_games = get_future_schedule(team_id, current_date)
    return {
        'games_next_7_days': len(future_games[:7]),
        'difficult_games_next_7': count_difficult_games(future_games[:7]),
        'playoff_impact': calculate_playoff_impact(team_id),
        # ...
    }
```

### 5. Historical Features

**Arquivo:** `src/features/historical.py`

**Descrição:** Captura padrões históricos

**Features principais:**
```python
# Head-to-head
- h2h_win_pct_last_10
- h2h_points_diff_last_10
- h2h_home_advantage

# Histórico de temporada
- season_win_pct
- home_win_pct
- away_win_pct
- vs_division_win_pct

# Padrões de temporada
- early_season_performance
- mid_season_performance
- late_season_performance
```

---

## 🔄 Pipeline de Features

### Fluxo Diário

```python
# 1. Coletar dados brutos
games = fetch_games()
stats = fetch_player_stats()
odds = fetch_odds()

# 2. Calcular features por categoria
form_features = calculate_form_features(games, stats)
context_features = calculate_context_features(games)
market_features = calculate_market_features(games, odds)
lookahead_features = calculate_lookahead_features(games)
historical_features = calculate_historical_features(games)

# 3. Merge de features
all_features = merge_features([
    form_features,
    context_features,
    market_features,
    lookahead_features,
    historical_features
])

# 4. Validação
validated = validate_features(all_features)

# 5. Armazenamento
feature_store.store(validated)
```

### Orquestração

**Arquivo:** `src/features/builder.py`

```python
class FeatureBuilder:
    def __init__(self):
        self.form_builder = FormFeatureBuilder()
        self.context_builder = ContextFeatureBuilder()
        self.market_builder = MarketFeatureBuilder()
        self.lookahead_builder = LookaheadFeatureBuilder()
        self.historical_builder = HistoricalFeatureBuilder()
    
    def build_all_features(self, game_id):
        game = get_game(game_id)
        
        features = {}
        features.update(self.form_builder.build(game))
        features.update(self.context_builder.build(game))
        features.update(self.market_builder.build(game))
        features.update(self.lookahead_builder.build(game))
        features.update(self.historical_builder.build(game))
        
        return features
```

---

## 🧪 Validação de Features

### Validação de Qualidade

**Regras:**
- **Missing values:** < 5%
- **Outliers:** ±3 desvios-padrão
- **Correlação:** < 0.95 entre features
- **Importância:** Feature importance > 0.01

**Implementação:**
```python
def validate_features(features):
    # Check missing values
    missing_pct = features.isnull().sum() / len(features)
    assert (missing_pct < 0.05).all(), "Too many missing values"
    
    # Check outliers
    z_scores = (features - features.mean()) / features.std()
    assert (abs(z_scores) < 3).all().all(), "Too many outliers"
    
    # Check correlation
    corr_matrix = features.corr()
    high_corr = (corr_matrix > 0.95) & (corr_matrix < 1)
    assert not high_corr.any().any(), "High correlation detected"
    
    return True
```

### Feature Importance

**Método:** SHAP values

```python
import shap

def calculate_feature_importance(model, X):
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    importance = pd.DataFrame({
        'feature': X.columns,
        'importance': abs(shap_values).mean(axis=0)
    })
    
    return importance.sort_values('importance', ascending=False)
```

---

## 📊 Feature Store

### Arquitetura

**Arquivo:** `32_Feature_Store/INDEX.md`

**Camadas:**
1. **Raw Layer:** Dados brutos
2. **Processed Layer:** Features calculadas
3. **Serving Layer:** Features para inferência

### Implementação

```python
class FeatureStore:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_features(self, game_id, feature_set):
        query = f"""
        SELECT * FROM features 
        WHERE game_id = '{game_id}' 
        AND feature_set = '{feature_set}'
        """
        return self.db.execute(query)
    
    def store_features(self, game_id, features):
        self.db.insert('features', {
            'game_id': game_id,
            'features': json.dumps(features),
            'timestamp': datetime.now()
        })
```

### Versioning

**Estratégia:**
- Cada feature set tem uma versão
- Versionamento semântico (major.minor.patch)
- Backward compatibility mantida

**Exemplo:**
```
v1.0.0 - Features iniciais (80 features)
v1.1.0 - Adicionadas 10 features de mercado
v2.0.0 - Refactor completo, breaking changes
```

---

## 🚀 Performance e Otimização

### Cache Strategy

**Cache de features:**
- Features de forma: 1 hora
- Features de contexto: 24 horas
- Features de mercado: 15 minutos
- Features de lookahead: 6 horas

### Precomputation

**Estratégia:**
- Pré-calcular features batch
- Atualizar incrementalmente
- Recalcular apenas quando necessário

### Parallel Processing

**Implementação:**
```python
from concurrent.futures import ThreadPoolExecutor

def build_features_parallel(game_ids):
    with ThreadPoolExecutor(max_workers=4) as executor:
        features = list(executor.map(build_features, game_ids))
    return pd.concat(features)
```

---

## 📈 Monitorização

### Métricas

**Feature Metrics:**
- Volume de features
- Taxa de atualização
- Latência de cálculo
- % de missing values

**Drift Detection:**
- Feature drift por Kolmogorov-Smirnov test
- Drift threshold: p-value < 0.05
- Alerta automático se drift detectado

### Alertas

**Telegram Alerts:**
- Falha no cálculo de features
- Drift detectado
- Missing values > 5%
- Latência > 10s

---

## 📝 Próximos Passos

### Curto Prazo (1-2 semanas)
- [ ] Implementar feature store completo
- [ ] Adicionar validação automática
- [ ] Otimizar performance
- [ ] Adicionar mais features de contexto

### Médio Prazo (1-2 meses)
- [ ] Implementar feature selection automática
- [ ] Adicionar features de NLP (injury reports)
- [ ] Criar feature importance dashboard
- [ ] Implementar online feature learning

### Longo Prazo (3-6 meses)
- [ ] Multi-desporto features
- [ ] Real-time feature computation
- [ ] Feature marketplace
- [ ] AutoML feature engineering

---

## 🔗 Links Relacionados

- [[Ingestão de Dados]] - Fonte de dados brutos
- [[Machine Learning]] - Consumidor das features
- [[Feature Store]] - Armazenamento e serving
- [[Índice Mestre]] - Documentação completa

---

**Última atualização:** 2026-05-19  
**Responsável:** ML Engineer  
**Status:** 🚧 Em desenvolvimento