# RELIABILITY_DIAGRAMS — Diagramas de Calibração

**ID:** `QR-008` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Visualizar calibração de probabilidades comparando previsões vs resultados reais em bins de probabilidade.

---

## 2. CONCEITO

Reliability diagram divide probabilidades em bins (ex: 0-10%, 10-20%, etc.) e mostra a taxa de vitória real em cada bin. Modelo perfeitamente calibrado mostra linha diagonal.

---

## 3. IMPLEMENTAÇÃO

```python
import numpy as np
import matplotlib.pyplot as plt

def reliability_diagram(probs, outcomes, n_bins=10):
    """
    Gera reliability diagram.
    
    Args:
        probs: Array de probabilidades previstas
        outcomes: Array de resultados (0 ou 1)
        n_bins: Número de bins
    
    Returns:
        bin_edges, observed_freqs, predicted_freqs
    """
    bin_edges = np.linspace(0, 1, n_bins + 1)
    observed_freqs = []
    predicted_freqs = []
    
    for i in range(n_bins):
        # Apostas neste bin
        mask = (probs >= bin_edges[i]) & (probs < bin_edges[i + 1])
        
        if np.sum(mask) > 0:
            obs_rate = np.mean(outcomes[mask])
            pred_rate = np.mean(probs[mask])
            
            observed_freqs.append(obs_rate_rate)
            predicted_freqs.append(pred_rate)
        else:
            observed_freqs.append(np.nan)
            predicted_freqs.append(np.nan)
    
    return bin_edges, observed_freqs, predicted_freqs

# Plotar
bin_edges, observed, predicted = reliability_diagram(probs, outcomes)

plt.figure(figsize=(8, 6))
plt.plot(predicted, observed, 'bo-', label='Modelo')
plt.plot([0, 1], [0, 1], 'k--', label='Perfeito')
plt.xlabel('Probabilidade Prevista')
plt.ylabel('Taxa de Vitória Real')
plt.legend()
plt.title('Reliability Diagram')
plt.show()
```

---

## 4. INTERPRETAÇÃO

| Padrão | Significado | Ação |
|--------|-------------|------|
| Pontos na diagonal | Bem calibrado | Bom |
| Pontos acima diagonal | Underconfident | Probabilidades muito baixas |
| Pontos abaixo diagonal | Overconfident | Probabilidades muito altas |

---

## 5. POR REGIME

Calcular separadamente por regime (favorito, equilibrado, underdog):

```python
def reliability_by_regime(probs, outcomes, regimes):
    """Reliability diagram por regime."""
    results = {}
    for regime in ['favorite', 'balanced', 'underdog']:
        mask = regimes == regime
        if np.sum(mask) > 0:
            results[regime] = reliability_diagram(probs[mask], outcomes[mask])
    return results
```

---

## 6. CRITÉRIOS

- **Pontos próximos da diagonal** - calibração boa
- **Desvio máximo < 0.05** em qualquer bin
- **Calibração consistente** por regime

---

## 7. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[ECE_MCE_CALIBRATION]]
