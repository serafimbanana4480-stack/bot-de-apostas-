# EXPANSÃO NFL — NFL Moneyline + Spread (VBQ-003)

**ID:** `MSE-001` | **Fase:** #phase/13-15 (VBQ-003) | **Owner:** Chief Systems Architect | **Status:** #status/pending
**Trigger de Ativação:** VBQ-002 completo com Football + MMA/UFC validados
**Última Atualização:** `2026-05-13`

---

## 1. PORQUÊ NFL

| Aspeto | Detalhe |
|--------|---------|
| **Ineficiências conhecidas** | Bye week effect, weather impact, divisional games, public money bias |
| **Liquidez alta** | Super Bowl e jogos de domingo têm liquidez comparável à NBA Playoffs |
| **Sinergia com NBA** | Stack tecnológico idêntico; apenas features e fontes de dados diferentes |
| **Timing ideal** | Época NFL (Set–Feb) complementa época NBA (Out–Jun) — cobertura quase anual |
| **Mercado menos coberto** | Menos modelos quant focados em NFL vs NBA |

---

## 2. DIFERENÇAS VS NBA — ANÁLISE COMPLETA

| Aspeto | NBA | NFL |
|--------|-----|-----|
| Jogos/época | 1.230 | 272 |
| Frequência | Diária | Semanal (domingo/segunda/quinta) |
| Amostras/equipa/época | 82 | 17 |
| Efeito lesão | Moderado (roster profundo) | **Alto** (QB lesionado = catástrofe) |
| Clima | Indoor (controlado) | Outdoor em 20+ estádios |
| Linha de spread típica | ±5 a ±12 pontos | ±3 a ±10 pontos |
| Overround típico | 3–5% | 4–6% |
| Mercados principais | Moneyline + Spread | Spread + Total (Over/Under) |
| Playoffs | 16 equipas | 14 equipas |
| Bye weeks | Não existe | Semana 5–14 (por equipa) |
| Dados históricos disponíveis | 20+ épocas | 20+ épocas |

**Implicação para modelos:** Menos dados por época = necessidade de mais épocas históricas (mínimo 5) e cautela com overfitting. Purged CV com embargo de 1 semana (em vez de 2 dias).

---

## 3. FONTES DE DADOS NFL

| Fonte | Tipo | Custo | Cobertura |
|-------|------|-------|-----------|
| `nfl-data-py` | Stats, schedules, rosters | Gratuito | 1999–presente |
| `nflreadr` (R port) | PBP data, win probability | Gratuito | 2000–presente |
| Pro Football Reference | Stats avançados | Gratuito (scraping) | 1920–presente |
| ESPN API (não oficial) | Odds, scores ao vivo | Gratuito | Temporada atual |
| The Odds API | Odds históricas multi-casa | Freemium | 2019–presente |
| Betfair Exchange | Odds NFL (menor liquidez) | Gratuito (com conta) | Temporada atual |

**Fonte primária recomendada:** `nfl-data-py` + The Odds API para odds históricas.

---

## 4. FEATURES ESPECÍFICAS NFL

### 4.1 Features de Team Performance
```python
nfl_team_features = [
    # Forma recente
    "wins_last_5",
    "point_differential_last_5",
    "yards_per_play_last_4",
    "turnover_differential_last_4",

    # Eficiência
    "epa_per_play_offense",        # Expected Points Added
    "epa_per_play_defense",
    "success_rate_offense",
    "third_down_conversion_pct",
    "red_zone_td_pct",

    # Situacional
    "is_divisional_game",          # Divisional games mais apertados
    "bye_week_rest",               # 1 se veio de bye week (vantagem)
    "opponent_bye_week",           # 1 se oponente veio de bye
    "days_rest",                   # 7, 10, 14+
    "travel_distance_km",

    # Clima (para jogos outdoor)
    "wind_speed_mph",
    "temperature_f",
    "precipitation_prob",
    "is_dome_game",
]
```

### 4.2 Features de QB (Críticas)
```python
qb_features = [
    "qb_epa_per_dropback_season",
    "qb_completion_percentage_season",
    "qb_is_starter",               # 0 se backup a jogar
    "qb_games_started_season",     # Experiência
    "qb_injury_status",            # healthy/questionable/out
    "qb_passer_rating_last_4",
]
```

---

## 5. ADAPTAÇÕES AO PIPELINE

### 5.1 Purged CV para NFL
```python
# NBA: embargo de 2 dias (jogos consecutivos)
# NFL: embargo de 1 semana (jogos semanais)

nfl_cv_config = {
    "n_splits": 5,              # 5 épocas de validação
    "embargo_weeks": 1,         # 1 semana de embargo
    "min_train_seasons": 3,     # Mínimo 3 épocas de treino
    "gap_weeks": 2              # Gap entre train e test
}
```

### 5.2 Tratamento de Bye Weeks
```python
def handle_bye_weeks(schedule_df: pd.DataFrame) -> pd.DataFrame:
    """
    Marcar jogos pós-bye week para ambas as equipas.
    Calcular dias de descanso reais (não apenas 7 dias base).
    """
    # Adicionar feature: dias desde último jogo (home e away)
    # Semanas com bye: 14 dias de descanso
    pass
```

---

## 6. CRITÉRIOS DE ENTRADA (GATE REVIEWS)

Para avançar de VBQ-002 (Fase 7-12) para VBQ-003 (Fase 13-15 NFL):

| Critério | Threshold | Verificação |
|----------|-----------|-------------|
| NBA ROI real | > 3% em 6+ meses | [[35_Financial_Tracking/INDEX]] |
| NBA CLV médio | > 2% com p < 0.05 | [[37_CLV_Analytics/INDEX]] |
| Sistema estável | Uptime > 99% últimos 3 meses | [[10_Monitoring/INDEX]] |
| Recursos disponíveis | Tempo de desenvolvimento > 20h/mês | Avaliação manual |
| Backtest NFL preliminar | CLV > 2% em 5 épocas com purged CV | Antes de arrancar |

**Regra absoluta:** Nenhuma expansão NFL com dinheiro real sem backtest independente validado. [[01_Vision_And_Strategy/FILOSOFIA_MVP]]

---

## 7. TIMELINE ESTIMADA (FASE 13-15)

| Semana | Tarefa |
|--------|--------|
| 1–2 | Ingestão histórica NFL (5 épocas) via nfl-data-py |
| 3–4 | Feature engineering NFL (adaptar pipeline NBA) |
| 5–6 | Treino XGBoost + purged walk-forward CV |
| 7–8 | Análise de CLV histórico e sensitividade |
| 9–10 | Shadow mode NFL (Betfair + SBK) |
| 11–12 | Avaliação: avançar ou voltar a backtest |

---

## 8. BACKLOG

- [ ] Instalar `nfl-data-py` e explorar dados históricos
- [ ] Definir features NFL prioritárias (EPA, bye weeks, QB)
- [ ] Adaptar pipeline de ingestão para schedule NFL
- [ ] Implementar purged CV com embargo semanal
- [ ] Executar backtest preliminar (go/no-go decision)
- [ ] Documentar diferenças de execução Betfair (NFL vs NBA liquidity)

---

## 9. LINKS CRUZADOS

- [[43_Multi_Sport_Expansion/INDEX]] ← Secção mãe
- [[01_Vision_And_Strategy/FILOSOFIA_MVP]] → Regra: um desporto até validação
- [[05_Machine_Learning/INDEX]] → Modelo base a adaptar
- [[06_Backtesting/INDEX]] → Walk-forward CV com embargo semanal
- [[47_Shadow_Betting/INDEX]] → Shadow mode NFL
