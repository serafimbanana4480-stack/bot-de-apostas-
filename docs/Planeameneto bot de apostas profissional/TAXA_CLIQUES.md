# TAXA_CLIQUES — Taxas de Liquidez

**ID:** `BM-002` | **Fase:** #phase/3 | **Owner:** Business Manager | **Status:** #status/active

---

## 1. OBJETIVO

Documentar taxas de liquidez e slippage esperado na execução de apostas.

---

## 2. LIQUIDEZ POR MERCADO

| Mercado | Liquidez | Slippage esperado |
|---------|----------|-------------------|
| Moneyline NBA | Alta | < 0.5% |
| Spread NBA | Média | 1-2% |
| Props NBA | Baixa | 2-5% |

---

## 3. CÁLCULO DE SLIPPAGE

```python
def calculate_slippage(expected_odd, actual_odd):
    """
    Calcula slippage percentual.
    
    Args:
        expected_odd: Odd esperada
        actual_odd: Odd executada
    
    Returns:
        Slippage em %
    """
    if expected_odd == 0:
        return 0
    
    slippage = abs(actual_odd - expected_odd) / expected_odd
    return slippage
```

---

## 4. IMPACTO NO EDGE

```python
def adjust_edge_for_slippage(edge, slippage):
    """
    Ajusta edge considerando slippage.
    
    Args:
        edge: Edge original
        slippage: Slippage esperado
    
    Returns:
        Edge ajustado
    """
    return edge - slippage
```

---

## 5. CRITÉRIOS

- **Slippage < 1%** para Moneyline
- **Slippage < 3%** para Spread
- **Ajustar edge** nos cálculos de stake

---

## 6. LINKS CRUZADOS

- [[02_Business_Model/INDEX]]
- [[DIVERGENCIA_PNL]]
