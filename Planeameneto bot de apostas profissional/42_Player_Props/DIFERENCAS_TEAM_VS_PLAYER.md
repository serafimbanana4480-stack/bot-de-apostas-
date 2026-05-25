# DIFERENCAS_TEAM_VS_PLAYER — Player Props vs Team Props

**ID:** `PP-002` | **Fase:** #phase/6 | **Owner:** Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar as diferenças fundamentais entre mercados de Team Props (Moneyline, Spread) e Player Props, explicando por que requerem pipelines, features e modelos separados.

---

## 2. NATUREZA DO MERCADO

### 2.1 Team Props (Moneyline, Spread)

- **Agregação de desempenho:** Resultado depende do desempenho coletivo de 5 jogadores
- **Estabilidade relativa:** Lesão de um jogador tem impacto mitigado pelo restante da equipa
- **Liquidez elevada:** Mercados principais com volume significativo
- **Eficiência de mercado:** Alta eficiência, edges mais pequenos
- **Dados agregados:** Features ao nível da equipa (FG%, pontos, ritmo, etc.)

### 2.2 Player Props (PTS, REB, AST, PRA)

- **Desempenho individual:** Resultado depende exclusivamente de um jogador
- **Volatilidade extrema:** Lesão ou mudança de minutos anula a aposta imediatamente
- **Liquidez reduzida:** Mercados secundários com volume limitado
- **Ineficiência de mercado:** Menos eficiência, edges potencialmente maiores
- **Dados granulares:** Features ao nível do jogador (uso, matchup, histórico)

---

## 3. DIFERENÇAS DE FEATURES

### 3.1 Features Team Props

```python
team_features = {
    # Agregados da equipa
    "team_pts_last10": float,      # Média de pontos últimos 10 jogos
    "team_fg_pct_last10": float,   # Percentagem de campo últimos 10
    "team_pace_last10": float,     # Ritmo de jogo últimos 10
    
    # Força relativa
    "home_court_advantage": float, # Vantagem de casa
    "rest_days": int,              # Dias de descanso
    "travel_distance": float,      # Distância de viagem
    
    # Matchup equipa vs equipa
    "off_rating_diff": float,      # Diferença rating ofensivo
    "def_rating_diff": float,      # Diferença rating defensivo
}
```

### 3.2 Features Player Props

```python
player_features = {
    # Histórico individual
    "pts_last5": float,            # Média pontos últimos 5 jogos
    "pts_last10": float,           # Média pontos últimos 10 jogos
    "pts_vs_opponent": float,      # Histórico contra esta equipa específica
    "pts_home_vs_away": float,     # Diferença casa vs fora
    
    # Uso e role
    "usage_rate": float,           # % de posses que terminam em ação do jogador
    "touch_rate": float,           # % de posses em que toca na bola
    "is_starter": bool,            # Titular ou suplente
    "minutes_last5": float,        # Minutos jogados últimos 5 jogos
    "minutes_projected": float,    # Minutos projetados para este jogo
    
    # Matchup específico
    "defender_rating": float,      # Rating defensivo do defensor principal
    "position_matchup": str,       # PG/SG/SF/PF/C matchup
    "team_pace_vs_avg": float,     # Ritmo da equipa vs média da liga
    
    # Contexto do jogo
    "game_total_line": float,      # Linha de total do jogo
    "spread_line": float,          # Linha de spread
    "is_blowout_risk": float,      # Probabilidade de blowout (redução minutos)
}
```

---

## 4. DIFERENÇAS DE MODELAGEM

### 4.1 Team Props - Modelo Binário

- **Target:** Variável binária (home_won = 1/0)
- **Output:** Probabilidade de vitória
- **Métricas:** Logloss, Brier Score, AUC
- **Calibração:** Por regime (favorito/equilibrado/underdog)
- **Stability:** Alta, features mudam gradualmente

### 4.2 Player Props - Modelo de Regressão ou Classificação

#### Opção A: Regressão (Previsão de valor contínuo)

```python
# Target: valor contínuo (ex: pontos = 23.5)
# Output: previsão de pontos esperados
# Vantagem: mais informação granular
# Desvantagem: mais complexo para converter em probabilidade de over/under

from sklearn.ensemble import RandomForestRegressor

model = RandomForestRegressor(
    n_estimators=200,
    max_depth=6,
    min_samples_leaf=20,
    random_state=42
)

# Previsão
pts_predicted = model.predict(X_test)

# Converter em probabilidade de Over
prob_over = calculate_over_probability(pts_predicted, line, std_dev)
```

#### Opção B: Classificação Binária (Over/Under direto)

```python
# Target: binário (over_line = 1/0)
# Output: probabilidade de passar a linha
# Vantagem: direto para betting
# Desvantagem: perde informação de magnitude

import xgboost as xgb

model = xgb.XGBClassifier(
    objective='binary:logistic',
    max_depth=4,
    learning_rate=0.05,
    n_estimators=1000,
    random_state=42
)

# Previsão
prob_over = model.predict_proba(X_test)[:, 1]
```

---

## 5. DIFERENÇAS DE RISCO

### 5.1 Team Props

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Lesão de estrela | Médio (equipa compensa) | Monitor lineup changes |
| Blowout | Médio (garbage time) | Filtros de spread |
| Mudança de treino | Baixo (sistemas estáveis) | Monitor trend |
| Viagens | Baixo (fator conhecido) | Incluir como feature |

### 5.2 Player Props

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Lesão do jogador | CRÍTICO (aposta anulada) | Monitor injury reports até tip-off |
| Mudança de minutos | ALTO (uso direto) | Projetar minutos, filtrar incerteza |
| Role change | ALTO (uso muda drasticamente) | Monitor lineup changes |
| Blowout | MUITO ALTO (titulares saem) | Filtros agressivos de spread |
| matchup defensivo | ALTO (defensor específico) | Incluir defender rating |
| Load management | ALTO (descanso programado) | Back-to-back tracking |

---

## 6. DIFERENÇAS DE LIQUIDEZ

### 6.1 Team Props

- **Volume:** €10,000+ por jogo típico
- **Slippage:** 0.5% (Moneyline), 0.7% (Spread)
- **Depth:** Múltiplos níveis de livro de ordens
- **Execution:** Rápida, pouco impacto de tamanho

### 6.2 Player Props

- **Volume:** €500-2,000 por linha típico
- **Slippage:** 1.0-2.0% (depende do jogador)
- **Depth:** Limitado, poucos níveis
- **Execution:** Sensível a tamanho, impacto significativo
- **Limites:** Bookmakers limitam rapidamente

---

## 7. IMPLICAÇÕES DE ARQUITETURA

### 7.1 Pipeline Separado Necessário

```
Team Props Pipeline:
├── Data Ingestion (team-level)
├── Feature Engineering (team aggregates)
├── Model Training (binary classification)
├── Prediction (probabilities)
└── Execution (high liquidity)

Player Props Pipeline:
├── Data Ingestion (player-level box scores)
├── Feature Engineering (player-specific)
├── Model Training (regression or classification)
├── Prediction (over/under probabilities)
├── Injury Monitoring (real-time)
├── Minutes Projection (context-aware)
└── Execution (low liquidity, careful sizing)
```

### 7.2 Banco de Dados Separado

```sql
-- Team props tables
team_features
├── game_id
├── team_id
├── team_pts_last10
├── team_fg_pct_last10
└── ...

-- Player props tables
player_features
├── game_id
├── player_id
├── pts_last5
├── usage_rate
├── minutes_projected
├── injury_status
└── ...
```

---

## 8. ESTRATÉGIA DE IMPLEMENTAÇÃO

### 8.1 Fase 1: Validação Conceitual

1. Coletar dados históricos de player props (2 épocas)
2. Comparar eficiência de mercado (CLV) entre team e player props
3. Testar features básicas de jogador
4. Validar que edges existem e são suficientes

### 8.2 Fase 2: Pipeline MVP

1. Implementar ingestão de box scores a nível de jogador
2. Construir feature engineering dedicado
3. Treinar modelo baseline (XGBoost classification)
4. Backtest com slippage aumentado (1.0%)
5. Paper trading por 1 mês

### 8.3 Fase 3: Produção

1. Micro banca dedicada (separada da banca principal)
2. Monitorização de lesões em tempo real
3. Sistema de projeção de minutos
4. Filtros de risco (blowout, injury, role change)
5. Scaling gradual com validação contínua

---

## 9. CONCLUSÃO

Player props não são uma extensão trivial de team props. São mercados fundamentalmente diferentes que requerem:

- **Pipeline de dados separado** (features de jogador vs equipa)
- **Modelos separados** (regressão/classificação vs classificação binária)
- **Sistema de risco separado** (lesões, minutos, role changes)
- **Estratégia de execução separada** (liquidez reduzida, slippage maior)
- **Banca dedicada** (risco diferente, correlação baixa)

A separação de arquitetura não é opcional — é necessária para gestão de risco adequada e performance consistente.

---

## 10. BACKLOG

- [ ] Coletar dados históricos de player props (2 épocas)
- [ ] Implementar ingestão de box scores a nível de jogador
- [ ] Construir feature engineering dedicado para player props
- [ ] Comparar eficiência de mercado team vs player props
- [ ] Definir arquitetura de pipeline separado
- [ ] Implementar sistema de monitorização de lesões
- [ ] Criar sistema de projeção de minutos

---

## 11. LINKS CRUZADOS

- [[42_Player_Props/INDEX]] ← Secção mãe
- [[42_Player_Props/PIPELINE_PROPS]] → Pipeline geral
- [[42_Player_Props/FEATURES_JOGADOR]] → Features detalhadas
- [[42_Player_Props/RISCOS_ESPECIFICOS]] → Gestão de risco