# BRIER_SCORE — Métrica de Calibração de Probabilidades

**ID:** `QR-002` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar o Brier Score como métrica de calibração de probabilidades. O Brier Score mede o quão próximas as probabilidades previstas estão dos resultados reais.

---

## 2. FÓRMULA

```
Brier Score = (1/N) * Σ (p_i - o_i)²
```

Onde:
- `p_i` = probabilidade prevista para o evento i
- `o_i` = resultado real (1 se ocorreu, 0 se não)
- `N` = número de previsões

**Interpretação:** Brier Score ∈ [0, 0.25] para binary classification. Menor é melhor. 0 = perfeito, 0.25 = aleatório.

---

## 3. COMPARAÇÃO COM MERCADO

O objetivo é ter Brier Score < Brier Score do mercado (probabilidades implícitas das odds).

```python
def brier_score(probs, outcomes):
    """Calcula Brier Score."""
    return np.mean((probs - outcomes) ** 2)

# Exemplo
model_probs = [0.6, 0.7, 0.4, 0.55]
outcomes = [1, 1, 0, 0]
model_brier = brier_score(model_probs, outcomes)

market_probs = [0.55, 0.65, 0.45, 0.5]
market_brier = brier_score(market_probs, outcomes)

if model_brier < market_brier:
    print("Modelo supera mercado em calibração")
```

---

## 4. BRIER SCORE POR REGIME

Calcular separadamente por regime (favorito, equilibrado, underdog):

```python
def brier_by_regime(probs, outcomes, regimes):
    """Calcula Brier Score por regime."""
    results = {}
    for regime in ['favorite', 'balanced', 'underdog']:
        mask = regimes == regime
        results[regime] = brier_score(probs[mask], outcomes[mask])
    return results
```

---

## 5. RELAÇÃO COM OUTRAS MÉTRICAS

| Métrica | O que mede | Relação com Brier |
|---------|-------------|-------------------|
| Brier Score | Calibração absoluta | Base para calibração |
| Log Loss | Calibração com penalização log | Similar mas mais sensível a outliers |
| ECE | Calibração em bins | Complementar ao Brier |
| Accuracy | Classificação correta | Pode ser boa com Brier ruim (overconfident) |

---

## 6. CRITÉRIOS DE SUCESSO

- Brier Score modelo < Brier Score mercado (mínimo)
- Melhoria > 10% vs mercado é excelente
- Brier Score < 0.15 em regime favorito é bom
- Brier Score < 0.20 em regime underdog é bom

---

## 7. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[ECE_MCE_CALIBRATION]] → Calibration por bins
