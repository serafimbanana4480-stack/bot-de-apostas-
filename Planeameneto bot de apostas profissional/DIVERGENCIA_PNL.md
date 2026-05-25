# DIVERGENCIA_PNL — Divergência de PnL

**ID:** `OP-004` | **Fase:** #phase/3 | **Owner:** Operations Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Detectar divergências entre PnL esperado (baseado em CLV) e PnL real para identificar problemas no sistema.

---

## 2. CÁLCULO DE DIVERGÊNCIA

```python
def calculate_pnl_divergence(expected_clv, actual_pnl):
    """
    Calcula divergência entre PnL esperado e real.
    
    Args:
        expected_clv: CLV total esperado
        actual_pnl: PnL real realizado
    
    Returns:
        Divergência em % e valor absoluto
    """
    divergence_pct = abs(actual_pnl - expected_clv) / abs(expected_clv) if expected_clv != 0 else 0
    divergence_abs = actual_pnl - expected_clv
    
    return {
        'divergence_pct': divergence_pct,
        'divergence_abs': divergence_abs
    }
```

---

## 3. CAUSAS DE DIVERGÊNCIA

| Causa | Sintoma | Ação |
|-------|---------|------|
| Slippage | PnL real < esperado | Ajustar para slippage |
| Odds mudaram | PnL real diferente | Verificar timing |
| Erro de execução | Apostas falharam | Revisar logs |
| Overfitting | PnL real << esperado | Re-treinar modelo |

---

## 4. ALERTAS

```python
def check_divergence_alerts(divergence):
    """Verifica se divergência requer alerta."""
    if divergence['divergence_pct'] > 0.20:
        send_alert(f"⚠️ Divergência de PnL: {divergence['divergence_pct']:.1%}")
    
    if divergence['divergence_abs'] < -expected_clv * 0.10:
        send_alert("🚨 PnL real muito abaixo do esperado")
```

---

## 5. INVESTIGAÇÃO

```python
def investigate_divergence(expected_clv, actual_pnl, bets):
    """Investiga causa da divergência."""
    # 1. Verificar slippage
    slippage = calculate_slippage(bets)
    
    # 2. Verificar apostas falhadas
    failed_bets = bets[bets['status'] == 'failed']
    
    # 3. Verificar odds mudadas
    odds_changed = bets[abs(bets['expected_odd'] - bets['actual_odd']) / bets['expected_odd'] > 0.02]
    
    return {
        'slippage': slippage,
        'failed_bets': len(failed_bets),
        'odds_changed': len(odds_changed)
    }
```

---

## 6. CRITÉRIOS

- **Alerta se divergência > 20%**
- **Investigar se divergência > 10%**
- **Aceitável até 5%** (variação normal)

---

## 7. LINKS CRUZADOS

- [[07_Execution/INDEX]]
- [[RECONCILIACAO]]
