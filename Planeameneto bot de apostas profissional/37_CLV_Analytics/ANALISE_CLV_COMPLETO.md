# ANALISE_CLV — Análise Completa de Closed Line Value

**ID:** `CLV-001` | **Versão:** v2.0 | **Data:** 2026-05-17  
**Fase:** #phase/3-4 | **Owner:** Principal Quant Engineer  
**Status:** #status/pending | **Custo:** 0€ (análises próprias)

---

## 1. FUNDAMENTOS DE CLV

### 1.1 Definição

**Closed Line Value (CLV)** = Edge sobre a linha de fecho do mercado.

```
CLV = (odd_executada / odd_fecho) - 1
```

| CLV | Interpretação |
|-----|---------------|
| **CLV > 0** | Modelo bateu o mercado |
| **CLV = 0** | Modelo igual ao mercado |
| **CLV < 0** | Modelo perdeu para o mercado |

### 1.2 Por que CLV é a Métrica Suprema

- **Imune a luck** — Não depende do resultado
- **Benchmark do mercado** — Mede vs mercado, não vs sorte
- **Previsível** — CLV médio indica ROI futuro
- **Não manipulável** — Não pode ser "otimizado" no backtest

---

## 2. DECOMPOSIÇÃO DE PnL

### 2.1 Framework

```
PnL_total = PnL_skill + PnL_execution + PnL_luck

PnL_skill = turnover × CLV_teorico × (1 - comissao)
PnL_execution = turnover × (CLV_real - CLV_teorico) × (1 - comissao)
PnL_luck = PnL_total - PnL_skill - PnL_execution
```

### 2.2 Exemplo Numérico

```
Aposta:
├── Stake: 100€
├── Odd recomendada: 2.10
├── Odd executada: 2.05
├── Odd fecho: 2.00
├── Resultado: Win

Cálculos:
├── CLV_teorico = (2.10 / 2.00) - 1 = +5.0%
├── CLV_real = (2.05 / 2.00) - 1 = +2.5%
├── Slippage = 2.5% - 5.0% = -2.5%
│
├── PnL_skill = 100€ × 5.0% × 0.98 = 4.90€
├── PnL_execution = 100€ × (-2.5%) × 0.98 = -2.45€
└── PnL_real = 102.90€
```

---

## 3. ANÁLISES POR DIMENSÃO

### 3.1 Por Regime

| Regime | Definição | CLV Esperado |
|--------|-----------|--------------|
| **Favorito** | Prob >= 65% | Mais difícil |
| **Equilibrado** | 35% < Prob < 65% | Target principal |
| **Underdog** | Prob <= 35% | Mais volátil |

```sql
-- Análise por regime
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
GROUP BY 1
ORDER BY clv_medio DESC;
```

### 3.2 Por Dia da Semana / Mês da Época

```sql
-- Análise por mês
SELECT 
    EXTRACT(MONTH FROM bet_date) as mes,
    ROUND(AVG(clv) * 100, 2) as clv_medio,
    ROUND(SUM(net_pnl) / NULLIF(SUM(stake), 0) * 100, 2) as roi
FROM gold.bets
GROUP BY 1
ORDER BY clv_medio DESC;
```

---

## 4. ANÁLISE ESTATÍSTICA

### 4.1 Intervalo de Confiança (Bootstrap)

```python
def bootstrap_clv_ci(clv_series, n_bootstrap=10000):
    """Calcula 95% CI para CLV médio."""
    import numpy as np
    
    means = []
    for _ in range(n_bootstrap):
        sample = clv_series.sample(len(clv_series), replace=True)
        means.append(sample.mean())
    
    return np.percentile(means, 2.5), np.percentile(means, 97.5)

# Uso
lower, upper = bootstrap_clv_ci(df['clv'])
print(f"CLV: {df['clv'].mean():.2%} [{lower:.2%}, {upper:.2%}]")
```

### 4.2 Teste de Significância

```python
from scipy import stats

t_stat, p_value = stats.ttest_1samp(clv_series, 0)
# H0: CLV médio = 0
# H1: CLV médio > 0 (one-tailed)

if t_stat > 0:
    p_value_one_tailed = p_value / 2
else:
    p_value_one_tailed = 1 - (p_value / 2)

significant = p_value_one_tailed < 0.05
```

---

## 5. MONITORIZAÇÃO

### 5.1 Métricas de Alerta

| Métrica | Threshold | Ação |
|---------|-----------|------|
| CLV Médio (30d) | < 1% | Warning |
| CLV Médio (30d) | < 0% | Stop |
| Degradação (slope 7d) | Negativo | Revisão modelo |

### 5.2 SQL para Monitorização

```sql
-- Rolling CLV com alertas
WITH rolling AS (
    SELECT 
        bet_date,
        AVG(clv) OVER (ORDER BY bet_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as clv_30d,
        AVG(clv) OVER (ORDER BY bet_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as clv_7d
    FROM daily_clv
)
SELECT 
    bet_date,
    clv_30d,
    CASE 
        WHEN clv_7d < 0 THEN 'ALERTA: CLV 7d negativo'
        WHEN clv_7d < 0.01 THEN 'ATENÇÃO: CLV 7d baixo'
        ELSE 'OK'
    END as status
FROM rolling
ORDER BY bet_date DESC;
```

---

## 6. DASHBOARD DE CLV

### KPIs Recomendados

| KPI | Target |
|-----|--------|
| CLV Médio | > 2% |
| CLV Médio (30d) | > 1.5% |
| % Apostas CLV > 0 | > 55% |
| Sharpe de CLV | > 0.5 |

---

## 7. BACKLOG

- [x] Definir framework de decomposição
- [x] Criar queries por dimensão
- [x] Implementar bootstrap para IC
- [ ] Criar dashboard Grafana
- [ ] Implementar alertas de degradação

---

## 8. LINKS

- [[37_CLV_Analytics/INDEX]] ← Secção mãe
- [[03_Quant_Research/CLV_CLOSED_LINE_VALUE]] → Definição teórica
- [[36_KPIs/INDEX]] → KPIs relacionados

---

**Análise CLV Completa — Custo: 0€**
