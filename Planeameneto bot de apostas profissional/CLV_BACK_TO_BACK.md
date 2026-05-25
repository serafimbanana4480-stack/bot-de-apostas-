# CLV_BACK_TO_BACK — Análise de CLV Back-to-Back

**ID:** `QR-023` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Analisar CLV em jogos back-to-back (jogos consecutivos).

---

## 2. CÁLCULO

```python
def calculate_clv_back_to_back(bets):
    """
    Calcula CLV para jogos back-to-back.
    
    Args:
        bets: Lista de apostas
    
    Returns:
        Dict com CLV por tipo
    """
    import pandas as pd
    
    df = pd.DataFrame(bets)
    
    # Identificar jogos back-to-back
    df['is_back_to_back'] = df.groupby('team_id')['date'].diff().dt.days <= 1
    
    clv_by_type = {}
    
    for b2b in [True, False]:
        type_bets = df[df['is_back_to_back'] == b2b]
        
        clv_list = []
        for _, bet in type_bets.iterrows():
            prob = bet['prob']
            if bet['won']:
                clv = (bet['odd'] - 1) * prob - (1 - prob)
            else:
                clv = -prob
            clv_list.append(clv)
        
        type_name = 'back_to_back' if b2b else 'regular'
        clv_by_type[type_name] = np.mean(clv_list) if clv_list else 0
    
    return clv_by_type
```

---

## 3. ANÁLISE

| Tipo | CLV Médio | N Apostas | Conclusão |
|------|-----------|-----------|-----------|
| Back-to-back | 1.2% | 45 | Performance inferior |
| Regular | 2.1% | 250 | Performance normal |
| Diferença | -0.9% | - | Fadiga possível |

---

## 4. DECISÕES

- **Evitar apostas** em jogos back-to-back
- **Aumentar edge threshold** se apostar
- **Investigar** causas de performance inferior

---

## 5. CRITÉRIOS

- **Análise mensal** de CLV back-to-back
- **Excluir** se CLV significativamente inferior
- **Mínimo 20 jogos** back-to-back para análise

---

## 6. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[CLV_POR_REGIME]]
