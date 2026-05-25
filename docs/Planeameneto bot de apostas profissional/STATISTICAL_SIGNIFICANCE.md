# STATISTICAL_SIGNIFICANCE — Testes de Hipótese

**ID:** `QR-007` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Determinar se o edge observado é estatisticamente significativo (não devido ao acaso) usando testes de hipótese.

---

## 2. TESTE T-ONE SAMPLE

Testar se ROI médio é significativamente diferente de zero:

```python
from scipy import stats

def test_roi_significance(roi_series, null_hypothesis=0.0):
    """
    Teste t para ROI médio.
    
    Returns:
        t_statistic, p_value
    """
    t_stat, p_value = stats.ttest_1samp(roi_series, null_hypothesis)
    return t_stat, p_value

# Exemplo
roi_series = [0.05, 0.03, -0.02, 0.07, 0.04]  # ROI por aposta
t_stat, p_value = test_roi_significance(roi_series)

if p_value < 0.05:
    print("ROI significativamente diferente de zero (p < 0.05)")
```

---

## 3. TESTE Z-PROPORÇÃO

Testar se taxa de vitória é significativamente maior que a do mercado:

```python
def test_winrate_significance(wins, total_bets, expected_winrate):
    """
    Teste Z para proporção.
    """
    observed_rate = wins / total_bets
    se = np.sqrt(expected_winrate * (1 - expected_winrate) / total_bets)
    z_stat = (observed_rate - expected_winrate) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    return z_stat, p_value
```

---

## 4. BOOTSTRAP CONFIDENCE INTERVAL

Usar bootstrap para calcular IC de métricas:

```python
def bootstrap_significance(metric_series, n_bootstrap=10000):
    """Bootstrap para significância."""
    bootstrap_means = []
    
    for _ in range(n_bootstrap):
        sample = np.random.choice(metric_series, size=len(metric_series), replace=True)
        bootstrap_means.append(np.mean(sample))
    
    ci_lower, ci_upper = np.percentile(bootstrap_means, [2.5, 97.5])
    
    return ci_lower, ci_upper

# Se IC não inclui 0, significativo
ci_lower, ci_upper = bootstrap_significance(clv_series)
if ci_lower > 0:
    print("CLV significativamente positivo")
```

---

## 5. CRITÉRIOS

- **p-value < 0.05** para significância estatística
- **IC 95% não incluir 0** para edge
- **Mínimo 100 apostas** para testes terem poder estatístico

---

## 6. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[BOOTSTRAP_BLOCK_RESAMPLING]]
