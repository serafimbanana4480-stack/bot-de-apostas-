# FILL_PROBABILITY — Probabilidade de Fill

**ID:** `BM-006` | **Fase:** #phase/3 | **Owner:** Business Manager | **Status:** #status/active

---

## 1. OBJETIVO

Estimar probabilidade de fill (execução) de aposta no bookmaker.

---

## 2. FATORES QUE AFETAM FILL

| Fator | Impacto |
|-------|---------|
| Liquidez do mercado | Alto |
| Stake size | Alto |
| Tempo antes do jogo | Alto |
| Volatilidade de odds | Médio |

---

## 3. MODELO DE FILL

```python
def estimate_fill_probability(odd, stake, liquidity, time_to_game):
    """
    Estima probabilidade de fill.
    
    Args:
        odd: Odd da aposta
        stake: Stake proposto
        liquidity: Liquidez do mercado
        time_to_game: Tempo até jogo em segundos
    
    Returns:
        Probabilidade de fill (0-1)
    """
    # Fator de liquidez (normalizado)
    liquidity_factor = min(liquidity / 100000, 1.0)
    
    # Fator de stake (stake menor = maior probabilidade)
    stake_factor = max(1 - stake / 1000, 0.1)
    
    # Fator de tempo (mais tempo = maior probabilidade)
    time_factor = min(time_to_game / 7200, 1.0)  # 2 horas max
    
    # Fator de odd (odds menores = maior probabilidade)
    odd_factor = 1 / odd
    
    # Probabilidade combinada
    fill_prob = (
        liquidity_factor * 0.4 +
        stake_factor * 0.3 +
        time_factor * 0.2 +
        odd_factor * 0.1
    )
    
    return fill_prob
```

---

## 4. APROVAÇÃO DE SINAL

```python
def approve_signal_based_on_fill(signal):
    """
    Aprova sinal se probabilidade de fill suficientemente alta.
    
    Args:
        signal: Sinal com odd, stake, etc.
    
    Returns:
        Boolean se aprovado
    """
    fill_prob = estimate_fill_probability(
        signal['odd'],
        signal['stake'],
        signal['liquidity'],
        signal['time_to_game']
    )
    
    if fill_prob < 0.7:
        logger.warning(f"Probabilidade de fill baixa: {fill_prob:.1%}")
        return False
    
    return True
```

---

## 5. CRITÉRIOS

- **Fill prob > 70%** para aprovar sinal
- **Ajustar stake** se fill prob baixa
- **Rejeitar** se fill prob < 50%

---

## 6. LINKS CRUZADOS

- [[02_Business_Model/INDEX]]
- [[TAXA_CLIQUES]]
