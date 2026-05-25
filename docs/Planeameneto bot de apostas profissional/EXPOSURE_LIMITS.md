# EXPOSURE_LIMITS — Limites de Exposição

**ID:** `RM-002` | **Fase:** #phase/3 | **Owner:** Risk Manager | **Status:** #status/active

---

## 1. OBJETIVO

Definir limites de exposição para controlar drawdowns e gerir risco de bancarrota.

---

## 2. LIMITES POR APOSTA

```python
MAX_STAKE_PCT = 0.05  # Máximo 5% por aposta

def check_stake_limit(stake, bankroll):
    """Verifica se stake respeita limite."""
    stake_pct = stake / bankroll
    return stake_pct <= MAX_STAKE_PCT
```

---

## 3. LIMITES POR DIA

```python
MAX_DAILY_EXPOSURE_PCT = 0.10  # Máximo 10% por dia

def check_daily_exposure(signals, bankroll):
    """Verifica exposição diária total."""
    daily_stake = signals['stake'].sum()
    exposure_pct = daily_stake / bankroll
    
    if exposure_pct > MAX_DAILY_EXPOSURE_PCT:
        # Reduzir stakes proporcionalmente
        reduction_factor = MAX_DAILY_EXPOSURE_PCT / exposure_pct
        signals['stake'] *= reduction_factor
    
    return signals
```

---

## 4. LIMITES POR EQUIPA

```python
MAX_TEAM_EXPOSURE_PCT = 0.15  # Máximo 15% por equipa

def check_team_exposure(signals, bankroll):
    """Verifica exposição por equipa."""
    for team in signals['team'].unique():
        team_stake = signals[signals['team'] == team]['stake'].sum()
        exposure_pct = team_stake / bankroll
        
        if exposure_pct > MAX_TEAM_EXPOSURE_PCT:
            # Reduzir stakes desta equipa
            team_mask = signals['team'] == team
            reduction_factor = MAX_TEAM_EXPOSURE_PCT / exposure_pct
            signals.loc[team_mask, 'stake'] *= reduction_factor
    
    return signals
```

---

## 5. LIMITES POR MERCADO

```python
MAX_MARKET_EXPOSURE_PCT = 0.20  # Máximo 20% por mercado (Moneyline, Spread)

def check_market_exposure(signals, bankroll):
    """Verifica exposição por mercado."""
    for market in signals['market'].unique():
        market_stake = signals[signals['market'] == market]['stake'].sum()
        exposure_pct = market_stake / bankroll
        
        if exposure_pct > MAX_MARKET_EXPOSURE_PCT:
            market_mask = signals['market'] == market
            reduction_factor = MAX_MARKET_EXPOSURE_PCT / exposure_pct
            signals.loc[market_mask, 'stake'] *= reduction_factor
    
    return signals
```

---

## 6. PIPELINE COMPLETO

```python
def apply_all_exposure_limits(signals, bankroll):
    """Aplica todos os limites de exposição."""
    signals = check_daily_exposure(signals, bankroll)
    signals = check_team_exposure(signals, bankroll)
    signals = check_market_exposure(signals, bankroll)
    
    return signals
```

---

## 7. CRITÉRIOS

- **Máximo 5%** por aposta
- **Máximo 10%** por dia
- **Máximo 15%** por equipa
- **Máximo 20%** por mercado

---

## 8. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]]
- [[STAKE_CALCULATOR]]
