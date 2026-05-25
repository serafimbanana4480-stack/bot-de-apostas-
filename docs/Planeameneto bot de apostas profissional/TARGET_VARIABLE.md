# TARGET_VARIABLE — Variável Alvo

**ID:** `ML-010` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir a variável alvo (target) para o modelo - o outcome que estamos a prever.

---

## 2. TARGET PARA MONEYLINE

```python
# Binary classification: vitória da equipa A (1) ou não (0)
target_moneyline = {
    0: "Away win",
    1: "Home win"
}

# Ou invertido, dependendo da perspectiva
```

---

## 3. TARGET PARA SPREAD

```python
# Binary classification: cobrir spread (1) ou não (0)
target_spread = {
    0: "Não cobriu",
    1: "Cobriu"
}

# Exemplo: Lakers -5.5
# Se Lakers ganham por ≥6 = 1 (cobriu)
# Se Lakers ganham por ≤5 = 0 (não cobriu)
```

---

## 4. CÁLCULO DO TARGET

```python
def calculate_target_moneyline(home_score, away_score):
    """Calcula target para Moneyline."""
    return 1 if home_score > away_score else 0

def calculate_target_spread(home_score, away_score, spread):
    """Calcula target para Spread."""
    margin = home_score - away_score
    return 1 if margin > spread else 0
```

---

## 5. META-TARGET (Meta-Labeling)

Para meta-modelo:

```python
# Meta-target: CLV ex-post > 0
meta_target = {
    0: "Negative CLV",
    1: "Positive CLV"
}

def calculate_clv_target(prob, odd, outcome):
    """Calcula se aposta teve CLV positivo."""
    edge = (prob * odd) - 1
    clv = edge if outcome == 1 else -1
    return 1 if clv > 0 else 0
```

---

## 6. BALANCEAMENTO

Target deve estar balanceado (30-70% split):

```python
def check_target_balance(y):
    """Verifica balanceamento do target."""
    pos_ratio = np.mean(y)
    
    if pos_ratio < 0.3 or pos_ratio > 0.7:
        print(f"Target desbalanceado: {pos_ratio:.2%}")
        return False
    
    return True
```

---

## 7. LINKS CRUZADOS

- [[05_Machine_Learning/INDEX]]
- [[46_Meta_Labeling/INDEX]]
