# METRICAS_PAPER — Métricas de Paper Trading

**ID:** `OP-021` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir métricas para avaliar performance em paper trading.

---

## 2. MÉTRICAS CHAVE

| Métrica | Descrição | Target |
|---------|-----------|--------|
| ROI (Paper) | ROI simulado | > 5% |
| CLV (Paper) | CLV simulado | > 2% |
| Sharpe (Paper) | Sharpe simulado | > 0.5 |
| Win Rate | Taxa de acerto | > 52% |
| N Apostas | Volume de apostas | > 100 |

---

## 3. CÁLCULO

```python
def calculate_paper_trading_metrics(paper_bets):
    """
    Calcula métricas de paper trading.
    
    Args:
        paper_bets: Lista de apostas simuladas
    
    Returns:
        Dict com métricas
    """
    total_stake = sum(b['stake'] for b in paper_bets)
    total_pnl = sum(b['pnl'] for b in paper_bets)
    
    roi = total_pnl / total_stake
    
    # CLV
    clv_list = []
    for b in paper_bets:
        prob = b['prob']
        if b['won']:
            clv = (b['odd'] - 1) * prob - (1 - prob)
        else:
            clv = -prob
        clv_list.append(clv)
    clv = np.mean(clv_list)
    
    # Sharpe
    daily_returns = [b['pnl'] / b['stake'] for b in paper_bets]
    sharpe = np.mean(daily_returns) / np.std(daily_returns)
    
    return {
        'roi': roi,
        'clv': clv,
        'sharpe': sharpe,
        'n_bets': len(paper_bets)
    }
```

---

## 4. VALIDAÇÃO PARA REAL

```python
def validate_paper_trading(paper_metrics, real_thresholds):
    """
    Valida se paper trading justifica real.
    
    Args:
        paper_metrics: Métricas de paper
        real_thresholds: Thresholds para real
    
    Returns:
        Boolean se aprovado
    """
    if paper_metrics['roi'] < real_thresholds['roi']:
        return False
    
    if paper_metrics['clv'] < real_thresholds['clv']:
        return False
    
    if paper_metrics['n_bets'] < 100:
        return False
    
    return True
```

---

## 5. CRITÉRIOS

- **Mínimo 100 apostas** em paper
- **ROI > 5%** para aprovar real
- **CLV > 2%** para aprovar real

---

## 6. LINKS CRUZADOS

- [[06_Backtesting/INDEX]]
- [[PAPER_TRADING]]
