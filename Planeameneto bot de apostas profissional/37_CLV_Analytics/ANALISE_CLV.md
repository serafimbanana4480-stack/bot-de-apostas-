# ANALISE_CLV — Decomposicao e Segmentacao

**ID:** `CLV-001` | **Fase:** #phase/3-4 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. DECOMPOSICAO DE PnL

```
PnL_total = PnL_skill + PnL_luck + PnL_market

PnL_skill = turnover * CLV_avg * (1 - comissao)
PnL_luck = PnL_total - PnL_skill - PnL_market
```

---

## 2. SEGMENTACAO POR REGIME

```sql
SELECT 
    CASE 
        WHEN prob_modelo >= 0.65 THEN 'favorito'
        WHEN prob_modelo >= 0.35 THEN 'equilibrado'
        ELSE 'underdog'
    END as regime,
    AVG(clv) as clv_medio,
    COUNT(*) as n_apostas,
    SUM(pnl)/SUM(stake) as roi
FROM bets
WHERE status = 'settled'
GROUP BY 1;
```

---

## 3. INTERVALO DE CONFIANCA

```python
def bootstrap_clv_ci(clv_series, n=10000, block_size=10):
    means = []
    for _ in range(n):
        blocks = [clv_series.sample(block_size, replace=True) for _ in range(len(clv_series)//block_size)]
        sample = pd.concat(blocks)[:len(clv_series)]
        means.append(sample.mean())
    return np.percentile(means, 2.5), np.percentile(means, 97.5)
```

---

## 4. BACKLOG

- [ ] Criar dashboard de CLV por regime
- [ ] Implementar decomposicao automatica de PnL
- [ ] Documentar interpretacao de cada componente

---

## 5. LINKS CRUZADOS

- [[37_CLV_Analytics/INDEX]] ← Secao mae
- [[03_Quant_Research/CLV_CLOSED_LINE_VALUE]] → Definicao teorica
