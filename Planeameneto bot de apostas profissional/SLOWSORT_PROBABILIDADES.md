# SLOWSORT_PROBABILIDADES — Probabilidades Slow Sort

**ID:** `QR-016` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Ordenar probabilidades de forma lenta (slow sort) para priorizar sinais de maior edge.

---

## 2. CONCEITO

Slow sort ordena sinais por edge descendente, priorizando apostas com maior valor esperado.

---

## 3. IMPLEMENTAÇÃO

```python
def slow_sort_signals(signals):
    """
    Ordena sinais por edge descendente.
    
    Args:
        signals: Lista de sinais com edge
    
    Returns:
        Sinais ordenados por edge
    """
    # Ordenar por edge descendente
    sorted_signals = sorted(
        signals,
        key=lambda x: x['edge'],
        reverse=True
    )
    
    return sorted_signals
```

---

## 4. APLICAÇÃO

```python
def prioritize_signals(signals, max_bets=10):
    """
    Prioriza sinais baseado em edge.
    
    Args:
        signals: Lista de sinais
        max_bets: Máximo de apostas por dia
    
    Returns:
        Sinais priorizados
    """
    sorted_signals = slow_sort_signals(signals)
    
    # Retornar top N
    return sorted_signals[:max_bets]
```

---

## 5. CRITÉRIOS

- **Ordenar por edge** descendente
- **Limitar a N apostas** por dia
- **Mínimo edge 4%** para considerar

---

## 6. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[SINAI_GENERATION]]
