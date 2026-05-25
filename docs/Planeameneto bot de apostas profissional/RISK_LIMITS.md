# RISK_LIMITS — Limites de Risco

**ID:** `RM-003` | **Fase:** #phase/3 | **Owner:** Risk Manager | **Status:** #status/active

---

## 1. OBJETIVO

Definir limites de risco para proteger o bankroll de drawdowns excessivos.

---

## 2. DRAWDOWN MÁXIMO

```python
MAX_DRAWDOWN_PCT = 0.20  # Parar se drawdown > 20%

def check_drawdown_limit(current_bankroll, initial_bankroll):
    """Verifica se drawdown excede limite."""
    drawdown_pct = 1 - (current_bankroll / initial_bankroll)
    
    if drawdown_pct > MAX_DRAWDOWN_PCT:
        return False  # Parar apostas
    
    return True
```

---

## 3. PERDA MÁXIMA CONSECUTIVA

```python
MAX_CONSECUTIVE_LOSSES = 10  # Parar após 10 perdas consecutivas

def check_consecutive_losses(results):
    """Verifica perdas consecutivas."""
    consecutive = 0
    
    for result in results[-20:]:  # Últimas 20 apostas
        if result < 0:
            consecutive += 1
            if consecutive >= MAX_CONSECUTIVE_LOSSES:
                return False
        else:
            consecutive = 0
    
    return True
```

---

## 4. DRAWDOWN MÁXIMO DIÁRIO

```python
MAX_DAILY_DRAWDOWN_PCT = 0.05  # Parar se drawdown diário > 5%

def check_daily_drawdown(pnl_today, bankroll_start):
    """Verifica drawdown diário."""
    drawdown_pct = abs(pnl_today) / bankroll_start
    
    if drawdown_pct > MAX_DAILY_DRAWDOWN_PCT:
        return False  # Parar apostas hoje
    
    return True
```

---

## 5. REDUÇÃO DE STAKE EM DRAWDOWN

```python
def reduce_stake_on_drawdown(current_bankroll, initial_bankroll, base_stake):
    """
    Reduz stake proporcionalmente ao drawdown.
    
    Se drawdown de 10%, reduzir stake em 10%.
    """
    drawdown_pct = 1 - (current_bankroll / initial_bankroll)
    
    if drawdown_pct > 0.10:
        reduction_factor = 1 - drawdown_pct
        return base_stake * reduction_factor
    
    return base_stake
```

---

## 6. CHECKLIST ANTES DE APOSTAR

```python
def pre_bet_check(bankroll, initial_bankroll, recent_results, pnl_today):
    """Checklist completo antes de apostar."""
    checks = {
        'drawdown_ok': check_drawdown_limit(bankroll, initial_bankroll),
        'consecutive_ok': check_consecutive_losses(recent_results),
        'daily_ok': check_daily_drawdown(pnl_today, initial_bankroll)
    }
    
    return all(checks.values()), checks
```

---

## 7. CRITÉRIOS

- **Parar se drawdown > 20%**
- **Parar após 10 perdas consecutivas**
- **Parar se drawdown diário > 5%**
- **Reduzir stake se drawdown > 10%**

---

## 8. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]]
- [[EXPOSURE_LIMITS]]
