# ODDS_NORMALIZACAO — Normalização de Odds

**ID:** `DE-005` | **Fase:** #phase/2 | **Owner:** Data Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Normalizar odds de diferentes bookmakers para comparação consistente.

---

## 2. MÉTODOS DE NORMALIZAÇÃO

### Decimal para Probabilidade Implícita

```python
def odd_to_probability(odd):
    """
    Converte odd decimal para probabilidade implícita.
    
    Args:
        odd: Odd decimal (ex: 2.50)
    
    Returns:
        Probabilidade implícita
    """
    return 1 / odd
```

### Remoção de Overround

```python
def remove_overround(probabilities):
    """
    Remove overround para normalizar probabilidades.
    
    Args:
        probabilities: Lista de probabilidades implícitas
    
    Returns:
        Probabilidades normalizadas (soma = 1)
    """
    total = sum(probabilities)
    normalized = [p / total for p in probabilities]
    
    return normalized
```

---

## 3. NORMALIZAÇÃO ENTRE BOOKMAKERS

```python
def normalize_bookmaker_odds(odds_dict):
    """
    Normaliza odds de múltiplos bookmakers.
    
    Args:
        odds_dict: Dict {bookmaker: odd}
    
    Returns:
        Odds normalizadas para comparação
    """
    # Converter para probabilidades
    probs = {bk: odd_to_probability(odd) for bk, odd in odds_dict.items()}
    
    # Média ponderada por volume (se disponível)
    avg_prob = np.mean(list(probs.values()))
    
    return avg_prob
```

---

## 4. CRITÉRIOS

- **Converter para probabilidade** antes de comparação
- **Remover overround** para cálculo de edge
- **Usar média** se múltiplos bookmakers

---

## 5. LINKS CRUZADOS

- [[04_Data_Engineering/INDEX]]
- [[PROBABILIDADES_IMPLICITAS]]
