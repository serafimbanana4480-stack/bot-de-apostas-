# OVERROUND_VIG — Margem do Bookmaker

**ID:** `QR-006` | **Fase:** #phase/1 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar o overround (vig) - a margem que os bookmakers adicionam às odds para garantir lucro. Entender o overround é essencial para calcular edge real.

---

## 2. CONCEITO

Odds de apostas não são probabilidades puras - incluem uma margem (overround) que garante que o bookmaker lucra independentemente do resultado.

---

## 3. CÁLCULO

```python
def calculate_overround(odds_list):
    """Soma das probabilidades implícitas."""
    return sum(1 / odd for odd in odds_list)

# Exemplo Moneyline
odds_home = 1.85
odds_away = 2.10
overround = (1/1.85) + (1/2.10)  # 0.540 + 0.476 = 1.016 = 1.6% vig
```

**Interpretação:** Overround > 1.0 indica margem do bookmaker. 1.016 = 1.6% de vig.

---

## 4. VIG POR MERCADO

| Mercado | Overround típico | Implicações |
|---------|------------------|-------------|
| Moneyline | 1-3% | Margem baixa, mercado eficiente |
| Spread | 2-4% | Margem moderada |
| Totals | 2-4% | Margem moderada |
| Props | 5-10% | Margem alta, evite |
| Live | 3-6% | Margem mais alta |

---

## 5. IMPACTO NO EDGE

```python
def calculate_real_edge(model_prob, market_odd, overround):
    """
    Calcula edge ajustado pelo overround.
    
    Args:
        model_prob: Probabilidade do modelo [0,1]
        market_odd: Odd do mercado
        overround: Overround do mercado (ex: 1.02)
    """
    implied_prob = 1 / market_odd
    normalized_prob = implied_prob / overround  # Remove overround
    
    edge = (model_prob * market_odd) - 1
    return edge
```

---

## 6. ESTRATÉGIAS

- **Focar em mercados de baixo overround** (Moneyline, Spread)
- **Evitar props** com overround > 5%
- **Comparar múltiplos bookmakers** para encontrar melhor odds (menor overround)

---

## 7. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[PROBABILIDADES_IMPLICITAS]]
