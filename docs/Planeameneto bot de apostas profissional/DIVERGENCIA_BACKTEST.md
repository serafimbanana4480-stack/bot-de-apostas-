# DIVERGENCIA_BACKTEST — Divergência Backtest vs Real

**ID:** `BT-002` | **Fase:** #phase/3 | **Owner:** Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Comparar resultados de backtest com performance real para validar modelo.

---

## 2. CÁLCULO DE DIVERGÊNCIA

```python
def backtest_vs_real(backtest_metrics, real_metrics):
    """
    Compara métricas de backtest vs real.
    
    Args:
        backtest_metrics: Métricas do backtest
        real_metrics: Métricas reais
    
    Returns:
        Divergência por métrica
    """
    divergence = {}
    
    for metric in ['roi', 'clv', 'sharpe', 'win_rate']:
        if metric in backtest_metrics and metric in real_metrics:
            diff = real_metrics[metric] - backtest_metrics[metric]
            divergence[metric] = {
                'backtest': backtest_metrics[metric],
                'real': real_metrics[metric],
                'diff': diff,
                'diff_pct': diff / backtest_metrics[metric] if backtest_metrics[metric] != 0 else 0
            }
    
    return divergence
```

---

## 3. CAUSAS DE DIVERGÊNCIA

| Causa | Sintoma | Ação |
|-------|---------|------|
| Overfitting | Real << Backtest | Simplificar modelo |
| Slippage não modelado | Real < Backtest | Ajustar para slippage |
| Mudança de mercado | Real ≠ Backtest | Re-treinar |
| Data leakage | Backtest >> Real | Revisar validação |

---

## 4. CRITÉRIOS DE ACEITAÇÃO

| Métrica | Divergência Aceitável |
|---------|----------------------|
| ROI | < 20% |
| CLV | < 30% |
| Sharpe | < 25% |
| Win Rate | < 10% |

---

## 5. AÇÃO SE DIVERGÊNCIA ALTA

```python
def handle_high_divergence(divergence):
    """Ação se divergência excede limites."""
    for metric, data in divergence.items():
        if abs(data['diff_pct']) > 0.20:
            logger.warning(f"Alta divergência em {metric}: {data['diff_pct']:.1%}")
            
            # Ações
            if metric in ['roi', 'clv']:
                # Revisar modelo
                schedule_model_review()
            elif metric == 'sharpe':
                # Revisar gestão de risco
                review_risk_management()
```

---

## 6. CRITÉRIOS

- **Divergência < 20%** aceitável
- **Investigar se > 20%**
- **Re-treinar se > 30%**

---

## 7. LINKS CRUZADOS

- [[06_Backtesting/INDEX]]
- [[OVERFITTING_TESTS]]
