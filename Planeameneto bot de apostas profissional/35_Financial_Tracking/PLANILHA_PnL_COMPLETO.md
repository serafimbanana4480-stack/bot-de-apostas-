# PLANILHA_PnL — Sistema Completo de Tracking Financeiro

**ID:** `FT-001` | **Versão:** v2.0 | **Data:** 2026-05-17  
**Fase:** #phase/4 | **Owner:** Operations Lead + Financial Analyst  
**Status:** #status/pending | **Custo:** 0€ (implementação própria)

---

## 1. OVERVIEW

Sistema completo de tracking de PnL (Profit and Loss) para todas as operações do VBQ-UNIFIED.

---

## 2. ESTRUTURA DA TABELA `bets`

### 2.1 Colunas Principais

| Coluna | Descrição | Tipo |
|--------|-----------|------|
| bet_id | ID único da aposta | VARCHAR(50) |
| game_id | ID do jogo NBA | VARCHAR(20) |
| bet_date | Data da aposta | DATE |
| market | Moneyline / Spread | VARCHAR(20) |
| selection | Equipa apostada | VARCHAR(100) |
| odd_signal | Odd recomendada | NUMERIC(6,3) |
| odd_executed | Odd real obtida | NUMERIC(6,3) |
| stake | Valor apostado | NUMERIC(10,2) |
| result | Win / Loss / Void | VARCHAR(10) |
| net_pnl | PnL líquido | NUMERIC(10,2) |
| clv | Closed Line Value | NUMERIC(8,4) |

### 2.2 Schema SQL

```sql
CREATE TABLE gold.bets (
    bet_id VARCHAR(50) PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL,
    bet_date DATE NOT NULL,
    market VARCHAR(20) NOT NULL,
    selection VARCHAR(100) NOT NULL,
    odd_signal NUMERIC(6,3) NOT NULL,
    odd_executed NUMERIC(6,3),
    stake NUMERIC(10,2) NOT NULL,
    result VARCHAR(10),
    net_pnl NUMERIC(10,2),
    clv NUMERIC(8,4),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 3. QUERIES ESSENCIAIS

### 3.1 Resumo Diário

```sql
SELECT 
    bet_date,
    COUNT(*) FILTER (WHERE result = 'win') as wins,
    COUNT(*) FILTER (WHERE result = 'loss') as losses,
    SUM(stake) as turnover,
    SUM(net_pnl) as pnl,
    ROUND(SUM(net_pnl) / NULLIF(SUM(stake), 0) * 100, 2) as roi_pct,
    ROUND(AVG(clv) * 100, 2) as avg_clv_pct
FROM gold.bets
WHERE paper_trade = FALSE
GROUP BY bet_date
ORDER BY bet_date DESC;
```

### 3.2 Acumulado Mensal

```sql
SELECT 
    DATE_TRUNC('month', bet_date) as mes,
    COUNT(*) as n_apostas,
    SUM(stake) as volume,
    SUM(net_pnl) as pnl_total,
    ROUND(SUM(net_pnl) / NULLIF(SUM(stake), 0) * 100, 2) as roi,
    ROUND(AVG(clv) * 100, 2) as clv_medio
FROM gold.bets
WHERE result IN ('win', 'loss')
GROUP BY 1
ORDER BY 1 DESC;
```

### 3.3 Por Regime

```sql
SELECT 
    CASE 
        WHEN prob_modelo >= 0.65 THEN 'favorito'
        WHEN prob_modelo >= 0.35 THEN 'equilibrado'
        ELSE 'underdog'
    END as regime,
    COUNT(*) as n,
    ROUND(AVG(clv) * 100, 2) as clv_medio,
    ROUND(SUM(net_pnl) / NULLIF(SUM(stake), 0) * 100, 2) as roi
FROM gold.bets
WHERE result IN ('win', 'loss')
GROUP BY 1;
```

---

## 4. DECOMPOSIÇÃO DE PnL

### 4.1 Framework

```
PnL_total = PnL_skill + PnL_execution + PnL_luck

PnL_skill = stake × CLV_teorico × (1 - comissao)
PnL_execution = stake × (CLV_real - CLV_teorico) × (1 - comissao)
PnL_luck = PnL_real - PnL_skill - PnL_execution
```

### 4.2 SQL para Decomposição

```sql
WITH decomposition AS (
    SELECT 
        stake,
        odd_signal,
        odd_close,
        odd_executed,
        net_pnl,
        (odd_close / odd_signal - 1) * stake as pnl_skill,
        (odd_executed - odd_close) / odd_close * stake as pnl_execution,
        net_pnl - ((odd_close / odd_signal - 1) * stake) - 
                  ((odd_executed - odd_close) / odd_close * stake) as pnl_luck
    FROM gold.bets
    WHERE result IN ('win', 'loss')
)
SELECT 
    ROUND(SUM(pnl_skill)::numeric, 2) as total_skill,
    ROUND(SUM(pnl_execution)::numeric, 2) as total_execution,
    ROUND(SUM(pnl_luck)::numeric, 2) as total_luck,
    ROUND(SUM(net_pnl)::numeric, 2) as total_pnl
FROM decomposition;
```

---

## 5. DASHBOARD DE PnL

### 5.1 KPIs Principais

| KPI | Fórmula | Target |
|-----|---------|--------|
| **PnL MTD** | SUM(net_pnl) no mês | > 0 |
| **ROI MTD** | SUM(net_pnl) / SUM(stake) | > 3% |
| **CLV Avg** | AVG(clv) | > 2% |
| **Sharpe** | MEAN(roi) / STD(roi) | > 0.5 |

### 5.2 Gráficos Recomendados

1. **PnL Cumulativo** — Evolução ao longo do tempo
2. **CLV por Dia** — Tendência de médio prazo
3. **Distribuição por Regime** — Favorito/Equilibrado/Underdog
4. **Drawdown** — Máxima queda da banca

---

## 6. RELATÓRIOS AUTOMATIZADOS

### 6.1 Relatório Diário (SQL)

```sql
-- Resumo executivo diário
SELECT 
    'Volume Total' as metric, 
    ROUND(SUM(stake)::numeric, 2) as value,
    'EUR' as unit
FROM gold.bets 
WHERE bet_date = CURRENT_DATE - 1

UNION ALL

SELECT 
    'PnL Líquido',
    ROUND(SUM(net_pnl)::numeric, 2),
    'EUR'
FROM gold.bets 
WHERE bet_date = CURRENT_DATE - 1

UNION ALL

SELECT 
    'ROI %',
    ROUND((SUM(net_pnl) / NULLIF(SUM(stake), 0) * 100)::numeric, 2),
    '%'
FROM gold.bets 
WHERE bet_date = CURRENT_DATE - 1;
```

---

## 7. CUSTO

| Componente | Custo |
|------------|-------|
| PostgreSQL (self-hosted) | 0€ |
| Grafana (OSS) | 0€ |
| **TOTAL** | **0€** |

---

## 8. CHECKLIST DE IMPLEMENTAÇÃO

- [x] Definir estrutura da tabela
- [x] Criar queries essenciais
- [ ] Implementar tabela no PostgreSQL
- [ ] Criar dashboard no Grafana
- [ ] Configurar alertas de anomalias
- [ ] Documentar procedimento de reconciliação

---

## 9. LINKS

- [[35_Financial_Tracking/INDEX]] ← Secção mãe
- [[35_Financial_Tracking/PLANO_CONTAS]] → Plano de contas
- [[35_Financial_Tracking/BANKROLL_MANAGEMENT]] → Gestão de banca

---

**Sistema de Tracking PnL Completo — Custo: 0€**
