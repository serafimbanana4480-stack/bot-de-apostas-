# PROBABILIDADES_IMPLICITAS — De Odds para Probabilidades

**ID:** `QR-001` | **Fase:** #phase/1 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Explicar como converter odds de apostas em probabilidades implícitas, remover overround (vig), e normalizar para uso em modelos ML.

---

## 2. CONCEITO

Odds de apostas representam a cotação, não a probabilidade real. O bookmaker adiciona margem (overround) para garantir lucro. Para comparar com o modelo, precisamos remover essa margem.

---

## 3. CÁLCULO BÁSICO

### 3.1 Decimal Odds para Probabilidade Implícita

```python
def decimal_to_implied_prob(odds_decimal):
    """Converte odds decimal para probabilidade implícita."""
    return 1 / odds_decimal

# Exemplo
odds = 2.10
prob_implied = 1 / 2.10  # 0.476 = 47.6%
```

### 3.2 Overround (Vig)

```python
def calculate_overround(odds_list):
    """Soma das probabilidades implícitas de um mercado."""
    return sum(1 / odd for odd in odds_list)

# Exemplo Moneyline
odds_home = 1.80
odds_away = 2.10
overround = (1/1.80) + (1/2.10)  # 0.556 + 0.476 = 1.032 = 3.2% vig
```

---

## 4. REMOÇÃO DE OVERROUND

### 4.1 Normalização Simples (Divisão)

```python
def normalize_odds(odds_list):
    """Remove overround dividindo pela soma."""
    probs = [1 / odd for odd in odds_list]
    total = sum(probs)
    normalized = [p / total for p in probs]
    return normalized
```

### 4.2 Método de Shin (Recomendado)

O método de Shin é mais sofisticado e assume que o overround não é distribuído uniformemente entre resultados.

```python
from scipy.optimize import fsolve
import numpy as np

def shin_method(odds_list):
    """
    Método de Shin para remover overround.
    Assume que o mercado é eficiente e a margem é distribuída proporcionalmente.
    """
    def equations(z):
        # z é o parâmetro de Shin
        return [(np.sqrt(1 - 4*z*(1/odd - 1)) - 1) / (2*z - 1/odd) for odd in odds_list]
    
    # Resolver numericamente
    z_guess = 0.01
    z = fsolve(lambda z: sum(equations(z)) - 1, z_guess)[0]
    
    true_probs = equations(z)
    return true_probs
```

**Quando usar:** Sempre que possível. Shin é mais preciso para mercados com odds assimétricas.

---

## 5. PROBABILIDADES POR REGIME

Diferentes regimes de odds (favorito vs underdog) têm diferentes padrões de overround:

| Regime | Overround típico | Normalização |
|--------|------------------|--------------|
| Favorito forte (odds < 1.50) | 2-4% | Shin method |
| Equilibrado (odds 1.80-2.20) | 3-5% | Divisão simples |
| Underdog forte (odds > 3.00) | 4-7% | Shin method |

---

## 6. VALIDAÇÃO

Após normalização, verificar:
- Soma das probabilidades = 1.0 (± 0.001)
- Todas as probabilidades em [0, 1]
- Probabilidades são monotônicas com odds (odd mais baixa = probabilidade mais alta)

---

## 7. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[OVERROUND_VIG]] → Detalhes sobre vigorish
