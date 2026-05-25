# FEATURES_COMPLETAS — Catalogo de Features

**ID:** `FS-001` | **Fase:** #phase/1 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Documentar TODAS as features usadas pelos modelos, incluindo definicao, formula, fonte de dados, timestamp de conhecimento (para prevenir leakage), e importancia esperada.

---

## 2. PRINCIPIOS DE CONSTRUCAO

1. **Cada feature tem um `known_at_timestamp`:** O momento exato em que esta informacao estava disponivel.
2. **Nenhuma feature usa dados do proprio jogo.** Todas sao calculadas antes do inicio.
3. **Rolling windows usam decaimento exponencial (halflife=5).**
4. **Interacoes so sao validas entre features ja conhecidas.**

---

## 3. GRUPO A — FORMA RECENTE COM DECAIMENTO

| # | Feature | Formula | Fonte | Window |
|---|---------|---------|-------|--------|
| A01 | `home_win_rate_decay5` | Media ponderada (exp halflife=5) de vitorias em casa | clean_games | Ultimos 20 jogos |
| A02 | `away_win_rate_decay5` | Idem para fora | clean_games | Ultimos 20 jogos |
| A03 | `home_efg_pct_decay5` | eFG% medio ponderado em casa | clean_team_game_stats | Ultimos 20 |
| A04 | `away_efg_pct_decay5` | Idem fora | clean_team_game_stats | Ultimos 20 |
| A05 | `home_tov_pct_decay5` | TOV% medio ponderado | clean_team_game_stats | Ultimos 20 |
| A06 | `away_tov_pct_decay5` | Idem | clean_team_game_stats | Ultimos 20 |
| A07 | `home_orb_pct_decay5` | ORB% medio ponderado | clean_team_game_stats | Ultimos 20 |
| A08 | `away_orb_pct_decay5` | Idem | clean_team_game_stats | Ultimos 20 |
| A09 | `home_ft_rate_decay5` | FT/FGA medio ponderado | clean_team_game_stats | Ultimos 20 |
| A10 | `away_ft_rate_decay5` | Idem | clean_team_game_stats | Ultimos 20 |
| A11 | `home_net_rating_decay5` | Net Rating medio ponderado | clean_team_game_stats | Ultimos 20 |
| A12 | `away_net_rating_decay5` | Idem | clean_team_game_stats | Ultimos 20 |
| A13 | `home_off_rating_decay5` | Offensive Rating medio | clean_team_game_stats | Ultimos 20 |
| A14 | `away_off_rating_decay5` | Idem | clean_team_game_stats | Ultimos 20 |
| A15 | `home_def_rating_decay5` | Defensive Rating medio | clean_team_game_stats | Ultimos 20 |
| A16 | `away_def_rating_decay5` | Idem | clean_team_game_stats | Ultimos 20 |
| A17 | `home_momentum_3g` | Off Rating ultimos 3 - Off Rating season | clean_team_game_stats | 3 vs season |
| A18 | `away_momentum_3g` | Idem | clean_team_game_stats | 3 vs season |

```python
import numpy as np

def exponential_decay_weights(n, halflife=5):
    """Retorna array de pesos [0.5^(0), 0.5^(1), ...]"""
    return np.array([0.5**(i/halflife) for i in range(n)])

def decayed_mean(values, halflife=5):
    weights = exponential_decay_weights(len(values), halflife)
    weights = weights / weights.sum()
    return np.average(values, weights=weights)
```

---

## 4. GRUPO B — METRICAS DE MERCADO

| # | Feature | Formula | Fonte |
|---|---------|---------|-------|
| B01 | `clv_implied` | (odd_atual - odd_open) / odd_open | clean_odds |
| B02 | `implied_prob` | 1 / odd_atual (normalizada por overround) | clean_odds |
| B03 | `overround` | Soma das implied probs - 1 | clean_odds |
| B04 | `odd_movement_pct` | (odd_close - odd_open) / odd_open | clean_odds |
| B05 | `market_confidence` | 1 - entropia(probs) / log(n_selections) | clean_odds |
| B06 | `home_implied_prob` | Prob implicita da casa | clean_odds |
| B07 | `away_implied_prob` | Prob implicita da fora | clean_odds |

---

## 5. GRUPO C — CONTEXTO DE JOGO E CALENDARIO

| # | Feature | Formula | Fonte |
|---|---------|---------|-------|
| C01 | `home_is_b2b` | Segundo jogo em 2 dias? | clean_schedules |
| C02 | `away_is_b2b` | Idem | clean_schedules |
| C03 | `home_rest_days` | Dias desde ultimo jogo | clean_schedules |
| C04 | `away_rest_days` | Idem | clean_schedules |
| C05 | `home_games_last5` | Jogos nos ultimos 5 dias | clean_schedules |
| C06 | `away_games_last5` | Idem | clean_schedules |
| C07 | `home_games_last7` | Jogos nos ultimos 7 dias | clean_schedules |
| C08 | `away_games_last7` | Idem | clean_schedules |
| C09 | `home_distance_km` | Km desde ultimo jogo | clean_schedules |
| C10 | `away_distance_km` | Idem | clean_schedules |
| C11 | `home_players_out` | # jogadores OUT | clean_player_injuries |
| C12 | `away_players_out` | # jogadores OUT | clean_player_injuries |
| C13 | `home_players_questionable` | # jogadores QUESTIONABLE | clean_player_injuries |
| C14 | `away_players_questionable` | # jogadores QUESTIONABLE | clean_player_injuries |
| C15 | `home_avg_age` | Idade media do plantel (se disponivel) | clean_team_game_stats |
| C16 | `away_avg_age` | Idem | clean_team_game_stats |

---

## 6. GRUPO D — INTERACOES NAO-LINEARES

| # | Feature | Formula |
|---|---------|---------|
| D01 | `home_pace_x_away_def` | home_pace_decay5 * away_def_rating_decay5 |
| D02 | `away_pace_x_home_def` | away_pace_decay5 * home_def_rating_decay5 |
| D03 | `home_efg_x_away_def_efg` | home_efg_pct_decay5 * (1 - away_efg_pct_def_decay5) |
| D04 | `away_efg_x_home_def_efg` | away_efg_pct_decay5 * (1 - home_efg_pct_def_decay5) |
| D05 | `home_b2b_x_age` | home_is_b2b * home_avg_age |
| D06 | `away_b2b_x_age` | away_is_b2b * away_avg_age |
| D07 | `rest_diff` | home_rest_days - away_rest_days |
| D08 | `net_rating_diff` | home_net_rating_decay5 - away_net_rating_decay5 |
| D09 | `off_rating_diff` | home_off_rating_decay5 - away_def_rating_decay5 |
| D10 | `home_rest_x_net` | home_rest_days * home_net_rating_decay5 |

**Nota:** Para eFG% defensivo (eFG% permitido ao adversario), calcular como:
```python
team_def_efg = opponent_efg_pct.mean()  # eFG% dos adversarios contra esta equipa
```

---

## 7. REGIME FLAGS (Nao-features, mas usadas em calibracao)

| Flag | Condicao |
|------|----------|
| `regime_favorito` | prob_modelo >= 0.65 |
| `regime_equilibrado` | 0.35 <= prob_modelo < 0.65 |
| `regime_underdog` | prob_modelo < 0.35 |

---

## 8. LINHAGEM (LINEAGE)

Cada feature deve poder ser tracada ate aos dados raw:

```
feat_home_efg_pct_decay5
  -> gold.feat_team_form.efg_pct_decay5
    -> silver.clean_team_game_stats.efg_pct
      -> bronze.raw_nba_boxscores.raw_json -> 'EFG_PCT'
        -> nba_api.stats.endpoints.boxscoretraditionalv2
```

---

## 9. BACKLOG

- [ ] Implementar pipeline de feature engineering (Prefect flow)
- [ ] Criar tests de leakage para cada feature
- [ ] Documentar importancia de cada feature (apos primeiro modelo)
- [ ] Implementar feature versioning (quando muda a formula)

---

## 10. LINKS CRUZADOS

- [[32_Feature_Store/INDEX]] ← Secao mae
- [[04_Data_Engineering/PIPELINE_ETL_NBA]] → Dados brutos
- [[05_Machine_Learning/INDEX]] → Modelos que consomem features
