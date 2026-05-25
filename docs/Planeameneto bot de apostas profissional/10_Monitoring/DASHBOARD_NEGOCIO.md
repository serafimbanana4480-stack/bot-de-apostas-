# DASHBOARD_NEGOCIO — PnL, ROI, CLV

**ID:** `MON-002` | **Fase:** #phase/4 | **Owner:** Operations Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Dashboard de negocio com metricas financeiras e de modelo, acessiveis a operadores e gestores.

---

## 2. PAINEL PRINCIPAL

### 2.1 PnL Acumulado
```sql
SELECT 
    DATE_TRUNC('day', bet_date) as dia,
    SUM(CASE WHEN result = 'win' THEN (odd_executed - 1) * stake ELSE -stake END) as pnl_dia,
    SUM(SUM(CASE WHEN result = 'win' THEN (odd_executed - 1) * stake ELSE -stake END)) 
        OVER (ORDER BY DATE_TRUNC('day', bet_date)) as pnl_acumulado
FROM bets
WHERE bet_date >= NOW() - INTERVAL '90 days'
GROUP BY 1
ORDER BY 1;
```

**Explicação:** A janela de 90 dias permite ver tendências recentes sem ruído de épocas antigas. O `OVER` calcula o PnL acumulado dinamicamente, essencial para identificar drawdowns e recuperações.

### 2.2 ROI (Return on Investment)
```sql
-- ROI global
SELECT 
    SUM(pnl) / SUM(stake) as roi_global,
    COUNT(*) as total_apostas,
    SUM(stake) as volume_total
FROM bets
WHERE status = 'settled';

-- ROI por mês (tendência)
SELECT 
    DATE_TRUNC('month', bet_date) as mes,
    SUM(pnl) / SUM(stake) as roi_mensal,
    COUNT(*) as n_apostas,
    SUM(stake) as volume
FROM bets
WHERE status = 'settled'
GROUP BY 1
ORDER BY 1;
```

**Explicação:** ROI mensal é mais informativo que global porque revela consistência. Um ROI global de 5% pode esconder meses de -10% e +20%. A consistência é mais importante que o retorno absoluto.

### 2.3 CLV Médio (Rolling 30 dias)
```sql
SELECT 
    DATE_TRUNC('day', bet_date) as dia,
    AVG((odd_executed / odd_close) - 1) as clv_avg,
    COUNT(*) as n_apostas
FROM bets
WHERE status = 'settled' 
  AND odd_close IS NOT NULL
  AND bet_date >= NOW() - INTERVAL '30 days'
GROUP BY 1
ORDER BY 1;
```

**Explicação:** CLV (Closed Line Value) mede se estamos a "bater" o mercado. CLV > 0% significa que a odd que obtivemos era melhor que a odd de fecho — o mercado moveu-se contra nós após a aposta, o que é sinal de que o nosso modelo tem edge real.

### 2.4 Yield por Unidade de Tempo
```sql
SELECT 
    DATE_TRUNC('week', bet_date) as semana,
    SUM(pnl) / SUM(stake) * 100 as yield_pct,
    SUM(stake) as turnover,
    COUNT(*) as n_apostas
FROM bets
WHERE status = 'settled'
  AND bet_date >= NOW() - INTERVAL '12 weeks'
GROUP BY 1
ORDER BY 1;
```

**Explicação:** Yield é o ROI ajustado ao turnover. Um yield de 3% com turnover de 10.000€/mês é muito diferente de yield 3% com turnover 1.000€/mês. Este painel ajuda a calibrar stakes e volume.

---

## 3. PAINEL DE REGIME

### 3.1 CLV por Regime de Mercado
```sql
SELECT 
    CASE 
        WHEN prob_model > 0.65 THEN 'Favorito'
        WHEN prob_model < 0.35 THEN 'Underdog'
        ELSE 'Equilibrado'
    END as regime,
    AVG((odd_executed / odd_close) - 1) as clv_medio,
    COUNT(*) as n_apostas,
    SUM(pnl) / SUM(stake) as roi_regime
FROM bets
WHERE status = 'settled' AND odd_close IS NOT NULL
GROUP BY 1
ORDER BY clv_medio DESC;
```

**Explicação:** Modelos tendem a performar diferentemente em favoritos vs underdogs. Favoritos têm menos variância mas odds mais baixas. Underdogs têm maior variância mas potencial de retorno maior. Identificar onde o modelo é mais forte permite ajustar thresholds.

### 3.2 Performance por Contexto
```sql
SELECT 
    CASE WHEN is_back_to_back THEN 'B2B' ELSE 'Rest' END as contexto,
    home_away,
    AVG((odd_executed / odd_close) - 1) as clv,
    COUNT(*) as n,
    SUM(pnl) / SUM(stake) as roi
FROM bets
JOIN games g ON bets.game_id = g.game_id
WHERE status = 'settled' AND odd_close IS NOT NULL
GROUP BY 1, 2
ORDER BY clv DESC;
```

**Explicação:** Back-to-backs afetam drasticamente a performance NBA. Equipas em B2B têm ~5% menos eficiência. Se o modelo não ajusta suficientemente para isto, pode haver edge em apostar contra equipas em B2B.

### 3.3 Performance por Mercado
```sql
SELECT 
    market_type,
    AVG((odd_executed / odd_close) - 1) as clv,
    COUNT(*) as n_apostas,
    SUM(pnl) / SUM(stake) as roi,
    STDDEV(pnl / stake) as volatilidade
FROM bets
WHERE status = 'settled' AND odd_close IS NOT NULL
GROUP BY market_type
ORDER BY clv DESC;
```

---

## 4. PAINEL DE RISCO

### 4.1 Drawdown e Recovery
```sql
WITH daily_pnl AS (
    SELECT 
        DATE_TRUNC('day', bet_date) as dia,
        SUM(CASE WHEN result = 'win' THEN (odd_executed - 1) * stake ELSE -stake END) as pnl
    FROM bets
    WHERE status = 'settled'
    GROUP BY 1
),
cumulative AS (
    SELECT 
        dia,
        pnl,
        SUM(pnl) OVER (ORDER BY dia) as equity
    FROM daily_pnl
)
SELECT 
    dia,
    equity,
    equity - MAX(equity) OVER (ORDER BY dia ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as drawdown
FROM cumulative
ORDER BY dia;
```

**Explicação:** Drawdown é a queda desde o pico mais recente. Um sistema pode ter ROI positivo mas drawdown de 50% — insustentável psicologicamente e financeiramente. Target: max drawdown < 20% do bankroll.

### 4.2 Kelly Real vs Teórico
```sql
SELECT 
    DATE_TRUNC('week', bet_date) as semana,
    AVG(kelly_fraction) as kelly_medio,
    AVG(actual_stake / bankroll) as stake_real,
    COUNT(*) as n_apostas
FROM bets
WHERE status = 'settled'
GROUP BY 1
ORDER BY 1;
```

---

## 5. GRAFANA DASHBOARD JSON

```json
{
  "dashboard": {
    "title": "Business Metrics - NBA Value Betting",
    "panels": [
      {
        "title": "PnL Acumulado",
        "type": "graph",
        "targets": [{
          "expr": "SELECT dia, pnl_acumulado FROM v_pnl_acumulado"
        }],
        "yAxes": [{"label": "EUR"}]
      },
      {
        "title": "ROI Mensal",
        "type": "graph",
        "targets": [{
          "expr": "SELECT mes, roi_mensal FROM v_roi_mensal"
        }],
        "yAxes": [{"label": "%", "min": -10, "max": 20}]
      },
      {
        "title": "CLV por Regime",
        "type": "table",
        "targets": [{
          "expr": "SELECT regime, clv_medio, n_apostas, roi_regime FROM v_clv_regime"
        }]
      },
      {
        "title": "Drawdown",
        "type": "graph",
        "targets": [{
          "expr": "SELECT dia, drawdown FROM v_drawdown"
        }],
        "yAxes": [{"label": "EUR", "max": 0}]
      }
    ]
  }
}
```

---

## 6. BACKLOG

- [x] Criar queries SQL para todas as métricas
- [x] Documentar explicações de cada métrica
- [ ] Construir dashboards Grafana com estas queries
- [ ] Implementar exportação automática diária (CSV/PDF)
- [ ] Adicionar comparação paper vs real money

---

## 7. LINKS CRUZADOS

- [[10_Monitoring/INDEX]] ← Secção mãe
- [[10_Monitoring/DASHBOARD_TECNICO]] → Dashboard de infraestrutura
- [[22_Real_Money_Operations/BANCA_GESTAO]] → Gestão de bankroll
- [[35_Financial_Tracking/PLANILHA_PnL]] → Planilha de PnL
