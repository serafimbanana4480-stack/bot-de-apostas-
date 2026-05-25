# CLV_POR_MERCADO — Análise de CLV por Mercado

**ID:** `QR-012` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Analisar CLV por mercado (Moneyline, Spread, Totals) para identificar mercados mais lucrativos.

---

## 2. MERCADOS

| Mercado | Descrição | Overround típico |
|---------|-----------|------------------|
| Moneyline | Vitória da equipa | 1-3% |
| Spread | Cobrir handicap | 2-4% |
| Totals | Over/Under pontos | 2-4% |

---

## 3. CÁLCULO POR MERCADO

```python
def clv_by_market(probs, odds, outcomes, markets):
    """
    Calcula CLV médio por mercado.
    
    Args:
        probs: Probabilidades previstas
        odds: Odds reais
        outcomes: Resultados reais
        markets: Array de mercados ['moneyline', 'spread', 'totals']
    
    Returns:
        Dict com CLV por mercado
    """
    results = {}
    
    for market in ['moneyline', 'spread', 'totals']:
        mask = markets == market
        
        if np.sum(mask) > 0:
            edges = (probs[mask] * odds[mask]) - 1
            clv = np.where(outcomes[mask] == 1, edges, -1)
            results[market] = {
                'clv_mean': np.mean(clv),
                'clv_std': np.std(clv),
                'n_bets': np.sum(mask)
            }
    
    return results
```

---

## 4. ESTRATÉGIA

- **Focar em Moneyline** inicialmente (menor overround)
- **Expandir para Spread** se CLV > 2% em backtest
- **Totals apenas** se modelo específico desenvolvido

---

## 5. CRITÉRIOS

- **CLV > 2%** para manter mercado ativo
- **Mínimo 100 apostas** para análise válida
- **Overround < 5%** preferencial

---

## 6. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[OVERROUND_VIG]]
