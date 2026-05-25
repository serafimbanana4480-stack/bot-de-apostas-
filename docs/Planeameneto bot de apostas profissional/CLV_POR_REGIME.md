# CLV_POR_REGIME — Análise de CLV por Regime

**ID:** `QR-011` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Analisar CLV (Closed Line Value) por regime de odds para identificar onde o modelo tem mais edge.

---

## 2. REGIMES DE ODDS

| Regime | Definição | Odds típicas |
|--------|-----------|--------------|
| Favorito | Home team favorito | 1.20 - 1.80 |
| Equilibrado | Equipas similares | 1.80 - 2.20 |
| Underdog | Home team underdog | 2.20 - 5.00 |

---

## 3. CÁLCULO POR REGIME

```python
def clv_by_regime(probs, odds, outcomes, regimes):
    """
    Calcula CLV médio por regime.
    
    Args:
        probs: Probabilidades previstas
        odds: Odds reais
        outcomes: Resultados reais
        regimes: Array de regimes ['favorite', 'balanced', 'underdog']
    
    Returns:
        Dict com CLV por regime
    """
    results = {}
    
    for regime in ['favorite', 'balanced', 'underdog']:
        mask = regimes == regime
        
        if np.sum(mask) > 0:
            edges = (probs[mask] * odds[mask]) - 1
            clv = np.where(outcomes[mask] == 1, edges, -1)
            results[regime] = {
                'clv_mean': np.mean(clv),
                'clv_std': np.std(clv),
                'n_bets': np.sum(mask)
            }
    
    return results
```

---

## 4. ANÁLISE

```python
def analyze_regime_performance(clv_by_regime):
    """Analisa performance por regime."""
    print("CLV por Regime:")
    print("-" * 40)
    
    for regime, metrics in clv_by_regime.items():
        print(f"{regime}:")
        print(f"  CLV: {metrics['clv_mean']:.2%}")
        print(f"  Std: {metrics['clv_std']:.2%}")
        print(f"  Apostas: {metrics['n_bets']}")
        print()
```

---

## 5. DECISÕES

- Se CLV negativo em regime, **desativar** esse regime
- Se CLV muito alto, **investigar** (possível overfitting)
- Focar em regimes com CLV positivo consistente

---

## 6. CRITÉRIOS

- **CLV > 0%** em todos os regimes ativos
- **CLV > 2%** no regime principal
- **Mínimo 50 apostas** por regime para análise válida

---

## 7. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[EDGE_DECAY_REGIME]]
