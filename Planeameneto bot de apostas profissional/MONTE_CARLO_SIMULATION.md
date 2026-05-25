# MONTE_CARLO_SIMULATION — Simulação de Bankroll

**ID:** `QR-003` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Usar simulações Monte Carlo para entender a distribuição de resultados possíveis do sistema, estimar drawdowns, e calcular probabilidade de ruína.

---

## 2. CONCEITO

Monte Carlo gera milhares de cenários possíveis baseados nas probabilidades do modelo, simulando como o bankroll evoluiria ao longo do tempo.

---

## 3. IMPLEMENTAÇÃO

```python
import numpy as np

def monte_carlo_simulation(probs, odds, stakes, n_simulations=10000):
    """
    Simula n_simulations cenários de apostas.
    
    Args:
        probs: Array de probabilidades previstas
        odds: Array de odds decimais
        stakes: Array de stakes em unidades de bankroll
        n_simulations: Número de simulações
    
    Returns:
        Array de bankrolls finais para cada simulação
    """
    n_bets = len(probs)
    results = []
    
    for _ in range(n_simulations):
        bankroll = 1.0  # Começa com 100%
        
        for i in range(n_bets):
            # Simular resultado baseado na probabilidade
            outcome = np.random.random() < probs[i]
            
            if outcome:
                bankroll += stakes[i] * (odds[i] - 1)
            else:
                bankroll -= stakes[i]
        
        results.append(bankroll)
    
    return np.array(results)
```

---

## 4. MÉTRICAS EXTRAÍDAS

```python
def analyze_simulations(sim_results):
    """Analisa resultados das simulações."""
    return {
        "mean_bankroll": np.mean(sim_results),
        "median_bankroll": np.median(sim_results),
        "percentile_5": np.percentile(sim_results, 5),
        "percentile_95": np.percentile(sim_results, 95),
        "probability_profit": np.mean(sim_results > 1.0),
        "probability_ruin": np.mean(sim_results < 0.5),  # Perda > 50%
        "max_drawdown": 1.0 - np.min(sim_results)
    }
```

---

## 5. COMPARAÇÃO DE FRAÇÕES DE KELLY

Simular diferentes frações de Kelly para encontrar o ponto ótimo:

```python
kelly_fractions = [0.25, 0.5, 0.75, 1.0]
results_by_fraction = {}

for k in kelly_fractions:
    stakes = kelly_fractions * k  # Ajustar stakes pela fração
    sim_results = monte_carlo_simulation(probs, odds, stakes)
    results_by_fraction[k] = analyze_simulations(sim_results)
```

**Critério:** Escolher fração com menor probabilidade de ruína (< 1%) e maior probabilidade de lucro.

---

## 6. DRAWDOWN ANALYSIS

```python
def calculate_drawdowns(sim_results):
    """Calcula drawdown máximo médio."""
    max_drawdowns = []
    for sim in sim_results:
        # Converter para série temporal de bankroll
        # Calcular drawdown máximo
        max_dd = 1.0 - (np.min(sim) / np.max(sim))
        max_drawdowns.append(max_dd)
    
    return np.mean(max_drawdowns)
```

---

## 7. CRITÉRIOS DE SUCESSO

- Probabilidade de ruína < 1% com Kelly 0.5
- Probabilidade de lucro > 80% em 1000 apostas
- Drawdown máximo médio < 20%
- Bankroll final médio > 1.5x (50% crescimento)

---

## 8. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[08_Risk_Management/INDEX]] → Kelly Criterion
