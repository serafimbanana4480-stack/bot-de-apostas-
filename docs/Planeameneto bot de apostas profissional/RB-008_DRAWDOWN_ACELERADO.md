# RB-008_DRAWDOWN_ACELERADO — Runbook para Drawdown Acelerado

**ID:** `RM-006` | **Fase:** #phase/3 | **Owner:** Risk Manager | **Status:** #status/active

---

## 1. OBJETIVO

Definir procedimento para lidar com drawdown acelerado (queda rápida de bankroll).

---

## 2. DEFINIÇÃO

Drawdown acelerado = queda > 10% em < 24 horas

---

## 3. DETEÇÃO

```python
def detect_accelerated_drawdown():
    """
    Deteta drawdown acelerado.
    
    Returns:
        Boolean se drawdown acelerado detetado
    """
    # PnL últimas 24h
    pnl_last_24h = get_pnl_last_hours(24)
    
    # Calcular drawdown
    initial_bankroll = get_initial_bankroll()
    current_bankroll = initial_bankroll + pnl_last_24h
    
    drawdown_pct = 1 - (current_bankroll / initial_bankroll)
    
    if drawdown_pct > 0.10:
        logger.critical(f"Drawdown acelerado detetado: {drawdown_pct:.1%}")
        return True
    
    return False
```

---

## 4. AÇÕES IMEDIATAS

1. **Parar apostas** imediatamente
2. **Notificar** Risk Manager
3. **Investigar** causa
4. **Não retomar** sem aprovação

---

## 5. INVESTIGAÇÃO

```python
def investigate_drawdown():
    """
    Investiga causa do drawdown.
    
    Returns:
        Causa identificada
    """
    # 1. Verificar performance do modelo
    model_performance = check_model_performance_last_24h()
    
    # 2. Verificar se odds mudaram
    odds_changes = check_odds_volatility()
    
    # 3. Verificar erros de execução
    execution_errors = check_execution_errors()
    
    # 4. Verificar mudança de regime
    regime_change = detect_regime_change()
    
    return {
        'model_performance': model_performance,
        'odds_changes': odds_changes,
        'execution_errors': execution_errors,
        'regime_change': regime_change
    }
```

---

## 6. RECUPERAÇÃO

```python
def recovery_plan(cause):
    """
    Define plano de recuperação baseado na causa.
    
    Args:
        cause: Causa do drawdown
    """
    if cause == 'model_performance':
        # Retraining emergencial
        emergency_retrain()
        return "Retreinar modelo"
    
    elif cause == 'odds_changes':
        # Ajustar thresholds
        adjust_thresholds_for_volatility()
        return "Ajustar thresholds"
    
    elif cause == 'execution_errors':
        # Corrigir erros técnicos
        fix_execution_errors()
        return "Corrigir erros"
    
    else:
        return "Investigação adicional necessária"
```

---

## 7. CRITÉRIOS

- **Parar imediatamente** se drawdown > 10% em 24h
- **Investigar causa** antes de retomar
- **Aprovação** para retomar operações

---

## 8. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]]
- [[STOP_SYSTEMS]]
