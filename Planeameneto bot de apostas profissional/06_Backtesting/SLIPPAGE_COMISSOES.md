# SLIPPAGE_E_COMISSOES — Custo de Transacao

**ID:** `BT-002` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/pending

---

## 1. DEFINICOES

| Custo | Valor | Descricao |
|-------|-------|-----------|
| Comissao Betfair | 5.0% | Sobre lucros (lucro * 0.05) |
| Slippage Moneyline | 0.5% | Odd obtida e 0.5% pior que a sinalizada |
| Slippage Spread | 0.7% | Menos liquido |
| Slippage Player Props | 1.0% | Mercado iliquido (futuro) |

---

## 2. FORMULA DE SIMULACAO

```python
def simulate_bet_outcome(odd_signal, outcome, slippage=0.005, commission=0.05):
    """
    outcome: 1 = win, 0 = loss
    odd_signal: odd recomendada pelo sistema
    
    Returns: multiplicador de PnL
    """
    odd_executed = odd_signal * (1 - slippage)
    
    if outcome == 1:
        profit = (odd_executed - 1)
        net_profit = profit * (1 - commission)
        return net_profit
    else:
        return -1.0
```

---

## 3. EXEMPLO

| Cenario | Odd Signal | Odd Executada (0.5% slip) | Resultado | Lucro Bruto | Comissao | Lucro Liquido |
|---------|------------|---------------------------|-----------|-------------|----------|---------------|
| Win | 2.00 | 1.99 | Win | 0.99 | 0.0495 | +0.9405 |
| Win | 1.80 | 1.791 | Win | 0.791 | 0.0396 | +0.7514 |
| Loss | 2.00 | 1.99 | Loss | - | - | -1.00 |

---

## 4. SENSITIVIDADE

```python
def sensitivity_analysis(clv_series, slippage_range=[0, 0.005, 0.01, 0.02]):
    """
    Mede como o ROI muda com diferentes niveis de slippage.
    """
    results = {}
    for slip in slippage_range:
        roi = calculate_roi(clv_series, slippage=slip)
        results[slip] = roi
    return results
```

---

## 5. BACKLOG

- [ ] Medir slippage real em paper trading
- [ ] Ajustar slippage de simulacao com base em dados reais
- [ ] Documentar diferenca entre backtest e real (divergencia)

---

## 6. LINKS CRUZADOS

- [[06_Backtesting/INDEX]] ← Secao mae
- [[09_Execution_System/SLIPPAGE_TRACKING]] → Medicao real
