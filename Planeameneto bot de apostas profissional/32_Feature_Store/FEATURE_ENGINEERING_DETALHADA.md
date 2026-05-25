# FEATURE ENGINEERING DETALHADA — NBA VALUE BETTING

**ID:** `FEA-001` | **Fase:** #phase/1-2 | **Owner:** Lead Data Engineer + Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar em detalhe todas as features usadas no modelo, garantindo que são calculadas exclusivamente com informação disponível antes do início do evento (zero look-ahead).

---

## 2. PRINCÍPIOS FUNDAMENTAIS

**Regra de Ouro:** Nenhuma feature pode usar dados do próprio jogo ou de jogos futuros. Todas as features são calculadas no timestamp do início do jogo.

**Validação:** Cada feature deve passar por:
- Teste de estacionariedade (ADF/KPSS)
- Teste de leakage temporal
- Teste de significância estatística no backtest

---

## 3. GRUPO A: FORMA RECENTE COM DECAIMENTO TEMPORAL

### A.1 Win Rate Ponderado com Half-Life

**Fórmula:**
```python
half_life = 5  # jogos
decay_rate = np.log(2) / half_life

def weighted_win_rate(games):
    weights = np.exp(-decay_rate * np.arange(len(games)))
    weights = weights / weights.sum()
    return np.average(games['result'], weights=weights)
```

**Justificação:** Jogos recentes têm mais peso, mas não descarta histórico completamente.

### A.2 Four Factors com Decaimento

**eFG% (Effective Field Goal Percentage):**
```python
eFG = (FGM + 0.5 * 3PM) / FGA
```

**TOV% (Turnover Percentage):**
```python
TOV = TOV / (FGA + 0.44 * FTA + TOV)
```

**ORB% (Offensive Rebound Percentage):**
```python
ORB = ORB / (ORB + DRB_opponent)
```

**FT/FGA (Free Throws per Field Goal Attempt):**
```python
FT_FGA = FT / FGA
```

Cada métrica é calculada com decaimento exponencial (half-life = 5 jogos).

### A.3 Net Rating Decaído

**Fórmula:**
```python
offensive_rating = points_per_100_possessions
defensive_rating = opponent_points_per_100_possessions
net_rating = offensive_rating - defensive_rating
```

Aplicar decaimento exponencial aos últimos 15 jogos.

### A.4 Momentum (Rating Recente vs Época)

**Fórmula:**
```python
momentum = net_rating_last_3_games - net_rating_season_avg
```

**Justificação:** Captura se a equipa está jogando acima ou abaixo da sua média da época.

---

## 4. GRUPO B: MÉTRICAS DE MERCADO

### B.1 CLV Implícito do Mercado

**Fórmula:**
```python
CLV = (odds_betfair - odds_pinnacle_close) / odds_pinnacle_close
```

**Proxy de Sharp Money:** CLV positivo indica que o mercado moveu na nossa direção após a aposta (sinal de sharp money).

### B.2 Percentagem de Dinheiro vs Apostas

**Fórmula:**
```python
money_share = total_money_bet / total_bets
```

**Justificação:** Alto money_share em poucas apostas indica sharp money concentrado.

### B.3 Dispersão de Odds

**Fórmula:**
```python
odds_std = np.std([odds_bookmaker_1, odds_bookmaker_2, ...])
odds_cv = odds_std / np.mean(odds)
```

**Justificação:** Alta dispersão indica ineficiência de mercado ou baixa liquidez.

---

## 5. GRUPO C: CONTEXTO DE JOGO E CALENDÁRIO

### C.1 Flag de Back-to-Back

**Definição:** Jogo num dia após o jogo anterior.

**Impacto:** Equipas em B2B têm performance média 2-3% pior.

### C.2 Número de Jogos Recentes

**Features:**
- `games_last_5_days`: Número de jogos nos últimos 5 dias
- `games_last_7_days`: Número de jogos nos últimos 7 dias
- `games_last_10_days`: Número de jogos nos últimos 10 dias

**Justificação:** Fadiga acumulada afeta performance.

### C.3 Dias de Descanso

**Features:**
- `days_rest_team`: Dias desde o último jogo da equipa
- `days_rest_opponent`: Dias desde o último jogo do adversário
- `days_rest_diff`: Diferença de descanso entre equipas

### C.4 Distância Percorrida

**Cálculo:**
```python
from geopy.distance import geodesic

distance = geodesic(
    (prev_venue_lat, prev_venue_lon),
    (current_venue_lat, current_venue_lon)
).kilometers
```

**Justificação:** Viagens longas causam fadiga e jet lag.

### C.5 Contexto de Jogo

**Features:**
- `home_game`: 1 se jogo em casa, 0 fora
- `back_to_back`: 1 se B2B, 0 caso contrário
- `rivalry_game`: 1 se rivalidade histórica, 0 caso contrário
- `nationally_televised`: 1 se TV nacional, 0 caso contrário

---

## 6. GRUPO D: INTERAÇÕES NÃO LINEARES

### D.1 Pace × Rating Defensivo

**Fórmula:**
```python
pace_offensive_A = possessions_per_48_min_A
rating_defensive_B = opponent_points_per_100_possessions_B
interaction = pace_offensive_A * rating_defensive_B
```

**Justificação:** Equipa rápida contra defesa fraca amplifica vantagem.

### D.2 eFG% Ofensivo × eFG% Defensivo

**Fórmula:**
```python
eFG_offensive_A = (FGM + 0.5 * 3PM_A) / FGA_A
eFG_defensive_B = opponent_eFG_against_B
interaction = eFG_offensive_A * eFG_defensive_B
```

### D.3 Back-to-Back × Idade Média

**Fórmula:**
```python
avg_age_team = mean(player_ages)
interaction = back_to_back * avg_age_team
```

**Justificação:** Equipas mais velhas sofrem mais com B2B.

---

## 7. TOTAL DE FEATURES

| Grupo | Número Features | Exemplos |
|-------|----------------|----------|
| A: Forma Recente | 12-15 | Win rate decay, Four Factors decay, Net rating, Momentum |
| B: Métricas de Mercado | 8-10 | CLV, Money share, Odds dispersion |
| C: Contexto e Calendário | 12-15 | B2B, Rest days, Distance, Home/Away |
| D: Interações | 8-10 | Pace × Rating, eFG × eFG, B2B × Age |
| **TOTAL** | **40-50** | |

---

## 8. VALIDAÇÃO DE FEATURES

### Teste de Estacionariedade

```python
from statsmodels.tsa.stattools import adfuller

def test_stationarity(series):
    result = adfuller(series.dropna())
    p_value = result[1]
    return p_value < 0.05  # Rejeitar H0 se p < 0.05
```

**Critério:** Feature é estacionária se p-value < 0.05.

### Teste de Leakage Temporal

**Procedimento:**
1. Para cada feature, verificar que só usa dados até timestamp do jogo
2. Verificar que não usa estatísticas do próprio jogo
3. Verificar que não usa dados de jogos futuros

### Teste de Significância

**Procedimento:**
1. Correr purged CV com e sem a feature
2. Medir delta de CLV e Brier Score
3. Feature é aprovada se delta > 0.1% e estatisticamente significativo (p < 0.05)

---

## 9. BACKLOG DE FEATURES

- [ ] Implementar pipeline de feature engineering com decaimento temporal
- [ ] Adicionar testes de estacionariedade automatizados
- [ ] Adicionar testes de leakage temporal automatizados
- [ ] Implementar cálculo de distância geográfica com geopy
- [ ] Criar feature store com versioning (MLflow)
- [ ] Implementar feature drift detection (PSI)

---

## 10. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[05_Machine_Learning/INDEX]] → Modelos que usam estas features
- [[06_Backtesting/INDEX]] → Validação de features
- [[48_Data_Drift/INDEX]] → Monitorização de drift de features
