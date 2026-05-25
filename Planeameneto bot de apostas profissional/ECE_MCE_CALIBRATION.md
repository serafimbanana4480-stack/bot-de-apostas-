# ECE_MCE_CALIBRATION — Expected Calibration Error

**ID:** `QR-009` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Calcular Expected Calibration Error (ECE) e Maximum Calibration Error (MCE) para quantificar calibração de probabilidades.

---

## 2. FÓRMULAS

```
ECE = Σ (n_i / N) * |obs_i - pred_i|
MCE = max |obs_i - pred_i|
```

Onde:
- `n_i` = número de apostas no bin i
- `N` = total de apostas
- `obs_i` = taxa de vitória real no bin i
- `pred_i` = probabilidade média prevista no bin i

---

## 3. IMPLEMENTAÇÃO

```python
def calculate_ece(probs, outcomes, n_bins=10):
    """
    Calcula Expected Calibration Error.
    
    Args:
        probs: Array de probabilidades previstas
        outcomes: Array de resultados (0 ou 1)
        n_bins: Número de bins
    
    Returns:
        ECE, MCE
    """
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    mce = 0.0
    n = len(probs)
    
    for i in range(n_bins):
        mask = (probs >= bin_edges[i]) & (probs < bin_edges[i + 1])
        n_i = np.sum(mask)
        
        if n_i > 0:
            obs_i = np.mean(outcomes[mask])
            pred_i = np.mean(probs[mask])
            
            bin_weight = n_i / n
            bin_error = abs(obs_i - pred_i)
            
            ece += bin_weight * bin_error
            mce = max(mce, bin_error)
    
    return ece, mce
```

---

## 4. INTERPRETAÇÃO

| ECE | Qualidade | Ação |
|-----|-----------|------|
| < 0.01 | Excelente | Manter |
| 0.01-0.05 | Bom | Aceitável |
| 0.05-0.10 | Moderado | Considerar calibração |
| > 0.10 | Ruim | Calibração necessária |

---

## 5. CALIBRAÇÃO ISOTÓNICA

Se ECE > 0.05, aplicar calibração:

```python
from sklearn.isotonic import IsotonicRegression

def calibrate_probabilities(probs_train, outcomes_train, probs_val):
    """
    Calibra probabilidades usando isotonic regression.
    """
    calibrator = IsotonicRegression(out_of_bounds='clip')
    calibrator.fit(probs_train, outcomes_train)
    
    calibrated_probs = calibrator.predict(probs_val)
    return calibrated_probs
```

---

## 6. POR REGIME

Calcular ECE separadamente por regime:

```python
def ece_by_regime(probs, outcomes, regimes):
    """ECE por regime."""
    results = {}
    for regime in ['favorite', 'balanced', 'underdog']:
        mask = regimes == regime
        if np.sum(mask) > 0:
            ece, mce = calculate_ece(probs[mask], outcomes[mask])
            results[regime] = {'ece': ece, 'mce': mce}
    return results
```

---

## 7. CRITÉRIOS

- **ECE < 0.05** para produção
- **MCE < 0.10** em qualquer bin
- **Calibração consistente** por regime

---

## 8. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[RELIABILITY_DIAGRAMS]]
