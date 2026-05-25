# STAKE_CALCULATOR — Cálculo de Stake (Kelly)

**ID:** `RM-001` | **Fase:** #phase/3 | **Owner:** Risk Manager | **Status:** #status/active

---

## 1. OBJETIVO

Calcular stake ótimo usando Kelly Criterion para maximizar crescimento do bankroll enquanto controla risco.

---

## 2. KELLY CRITERION

```python
def kelly_fraction(prob, odds):
    """
    Calcula fração ótima de Kelly.
    
    Args:
        prob: Probabilidade prevista [0,1]
        odds: Odd decimal
    
    Returns:
        Fração de bankroll para apostar
    """
    edge = (prob * odds) - 1
    kelly = edge / (odds - 1)
    return max(0, kelly)  # Nunca apostar se edge negativo
```

---

## 3. FRAÇÃO DE KELLY

Kelly completo é muito agressivo. Usar fração:

```python
def fractional_kelly(prob, odds, kelly_fraction=0.5):
    """Kelly com fração conservadora."""
    full_kelly = kelly_fraction(prob, odds)
    return full_kelly * kelly_fraction
```

**Frações recomendadas:**
- **Kelly 0.25:** Muito conservador, drawdowns mínimos
- **Kelly 0.5:** Balanceado (recomendado)
- **Kelly 0.75:** Agressivo, maior risco
- **Kelly 1.0:** Completo (não recomendado)

---

## 4. LIMITES DE EXPOSIÇÃO

```python
def calculate_stake(prob, odds, bankroll, max_stake_pct=0.05):
    """
    Calcula stake com limites de exposição.
    
    Args:
        prob: Probabilidade prevista
        odds: Odd decimal
        bankroll: Bankroll atual
        max_stake_pct: Máximo % de bankroll por aposta
    """
    kelly_stake_pct = fractional_kelly(prob, odds, kelly_fraction=0.5)
    
    # Aplicar limite máximo
    stake_pct = min(kelly_stake_pct, max_stake_pct)
    
    stake = bankroll * stake_pct
    return stake
```

---

## 5. APLICAÇÃO

```python
# Exemplo
prob = 0.60  # Modelo prevê 60%
odds = 1.90   # Mercado oferece 1.90
bankroll = 1000

stake = calculate_stake(prob, odds, bankroll)
print(f"Stake: €{stake:.2f}")
```

---

## 6. CRITÉRIOS

- **Máximo 5% por aposta** para controlar drawdowns
- **Kelly 0.5** como default
- **Ajustar fração** se drawdowns forem muito altos

---

## 7. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]]
- [[EXPOSURE_LIMITS]]
