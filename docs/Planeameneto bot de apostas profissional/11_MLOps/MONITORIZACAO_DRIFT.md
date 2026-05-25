# MONITORIZACAO_DRIFT — Data e Prediction Drift

**ID:** `MLO-001` | **Fase:** #phase/6 | **Owner:** MLOps Engineer | **Status:** #status/pending

---

## 1. TIPOS DE DRIFT

| Tipo | Definicao | Teste | Threshold |
|------|-----------|-------|-----------|
| Feature Drift | Distribuicao das features muda | KS test, PSI | PSI > 0.20 |
| Prediction Drift | Distribuicao das predicoes muda | KS test nas probs | p < 0.01 |
| Target Drift | Distribuicao dos outcomes muda | Proporcao de vitorias | chi2 test |
| Concept Drift | Relacao feature-target muda | Performance degradation | CLV cai > 20% |

---

## 2. PSI (Population Stability Index)

```python
import numpy as np

def calculate_psi(expected, actual, buckets=10):
    """
    Calcula PSI entre duas distribuicoes.
    PSI < 0.1: insignificante
    PSI 0.1-0.2: moderado
    PSI > 0.2: significativo
    """
    def scale_range(input, min_val, max_val):
        return (input - min_val) / (max_val - min_val)
    
    breakpoints = np.linspace(0, 1, buckets + 1)
    breakpoints = np.percentile(expected, breakpoints * 100)
    breakpoints[0], breakpoints[-1] = expected.min() - 0.001, expected.max() + 0.001
    
    expected_percents = np.histogram(expected, breakpoints)[0] / len(expected)
    actual_percents = np.histogram(actual, breakpoints)[0] / len(actual)
    
    psi = np.sum((actual_percents - expected_percents) * 
                 np.log(actual_percents / (expected_percents + 1e-10) + 1e-10))
    return psi
```

---

## 3. RESPOSTA A DRIFT

| PSI | Accao |
|-----|-------|
| 0.00 - 0.10 | Nenhuma |
| 0.10 - 0.20 | Monitorizar de perto; preparar retraining |
| 0.20 - 0.30 | Retraining triggered; shadow mode |
| > 0.30 | Alerta CRITICAL; pausar apostas |

---

## 4. BACKLOG

- [ ] Implementar calculo PSI para top 10 features
- [ ] Criar alerta automatico quando PSI > 0.20
- [ ] Documentar resposta standard a cada nivel

---

## 5. LINKS CRUZADOS

- [[11_MLOps/INDEX]] ← Secao mae
- [[48_Data_Drift/INDEX]] → Detalhes de analise de drift
