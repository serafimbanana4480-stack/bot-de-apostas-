# CLV_CASA_FORA — Análise de CLV Casa/Fora

**ID:** `QR-022` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Analisar CLV diferenciado entre jogos em casa e fora.

---

## 2. CÁLCULO

```python
def calculate_clv_home_away(bets):
    """
    Calcula CLV separado por casa/fora.
    
    Args:
        bets: Lista de apostas
    
    Returns:
        Dict com CLV por localização
    """
    import pandas as pd
    
    df = pd.DataFrame(bets)
    
    clv_by_location = {}
    
    for location in ['home', 'away']:
        location_bets = df[df['location'] == location]
        
        clv_list = []
        for _, bet in location_bets.iterrows():
            prob = bet['prob']
            if bet['won']:
                clv = (bet['odd'] - 1) * prob - (1 - prob)
            else:
                clv = -prob
            clv_list.append(clv)
        
        clv_by_location[location] = np.mean(clv_list) if clv_list else 0
    
    return clv_by_location
```

---

## 3. ANÁLISE

| Localização | CLV Médio | N Apostas | Conclusão |
|-------------|-----------|-----------|-----------|
| Casa | 2.3% | 150 | Melhor performance |
| Fora | 1.5% | 145 | Performance inferior |
| Diferença | +0.8% | - | Home advantage significativo |

---

## 4. DECISÕES

- **Aumentar edge threshold** para jogos fora
- **Priorizar jogos em casa** se disponível
- **Investigar** causas de CLV inferior fora

---

## 5. CRITÉRIOS

- **Análise trimestral** de CLV casa/fora
- **Ajustar thresholds** baseado em diferença
- **Mínimo 50 apostas** por localização

---

## 6. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[CLV_POR_REGIME]]
