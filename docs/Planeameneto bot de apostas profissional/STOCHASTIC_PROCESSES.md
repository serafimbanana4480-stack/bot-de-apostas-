# STOCHASTIC_PROCESSES — Processos Estocásticos

**ID:** `QR-015` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar conceitos de processos estocásticos aplicados a apostas.

---

## 2. RANDOM WALK

Odds podem ser modeladas como random walk com drift:

```python
def random_walk_model(odds, steps=100, drift=0):
    """
    Modela odds como random walk.
    
    Args:
        odds: Odd inicial
        steps: Número de passos
        drift: Drift médio
    
    Returns:
        Série de odds simulada
    """
    import numpy as np
    
    returns = np.random.normal(drift, 0.02, steps)
    odds_series = odds * (1 + returns).cumprod()
    
    return odds_series
```

---

## 3. BROWNIAN MOTION

Modelo de Brownian motion para movimento de odds:

```python
def brownian_motion(odds, T=1, N=100, mu=0, sigma=0.02):
    """
    Simula Brownian motion para odds.
    
    Args:
        odds: Odd inicial
        T: Tempo total
        N: Número de passos
        mu: Drift
        sigma: Volatilidade
    
    Returns:
        Série de odds
    """
    dt = T / N
    t = np.linspace(0, T, N)
    
    W = np.random.standard_normal(size=N)
    W = np.cumsum(W) * np.sqrt(dt)
    
    X = (mu - 0.5 * sigma**2) * t + sigma * W
    odds_series = odds * np.exp(X)
    
    return odds_series
```

---

## 4. APLICAÇÕES

- **Simulação de odds** para backtesting
- **Análise de volatilidade**
- **Cálculo de probabilidade de movimento**

---

## 5. CRITÉRIOS

- **Usar para simulação** de cenários
- **Validar** com dados históricos
- **Calibrar parâmetros** regularmente

---

## 6. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[MONTE_CARLO_SIMULATION]]
