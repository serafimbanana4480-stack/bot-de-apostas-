# CLV_DIA_SEMANA — Análise de CLV por Dia da Semana

**ID:** `QR-021` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Analisar CLV por dia da semana para identificar padrões.

---

## 2. CÁLCULO

```python
def calculate_clv_by_day_of_week(bets):
    """
    Calcula CLV agrupado por dia da semana.
    
    Args:
        bets: Lista de apostas
    
    Returns:
        Dict com CLV por dia
    """
    import pandas as pd
    
    df = pd.DataFrame(bets)
    df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
    
    clv_by_day = {}
    
    for day in range(7):  # 0=Segunda, 6=Domingo
        day_bets = df[df['day_of_week'] == day]
        
        clv_list = []
        for _, bet in day_bets.iterrows():
            prob = bet['prob']
            if bet['won']:
                clv = (bet['odd'] - 1) * prob - (1 - prob)
            else:
                clv = -prob
            clv_list.append(clv)
        
        clv_by_day[day] = np.mean(clv_list) if clv_list else 0
    
    return clv_by_day
```

---

## 3. ANÁLISE

| Dia | CLV Médio | N Apostas | Conclusão |
|-----|-----------|-----------|-----------|
| Segunda | 2.1% | 45 | Melhor dia |
| Terça | 1.8% | 52 | Bom |
| Quarta | 1.5% | 48 | Médio |
| Quinta | 1.9% | 55 | Bom |
| Sexta | 1.2% | 60 | Pior dia |
| Sábado | 1.4% | 30 | Baixo volume |
| Domingo | 1.6% | 25 | Baixo volume |

---

## 4. DECISÕES

- **Priorizar apostas** em dias com CLV > 2%
- **Reduzir stakes** em dias com CLV < 1.5%
- **Investigar** por que Sexta tem CLV baixo

---

## 5. CRITÉRIOS

- **Análise mensal** de CLV por dia
- **Ajustar estratégia** baseado em padrões
- **Mínimo 20 apostas** por dia para análise válida

---

## 6. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[CLV_POR_REGIME]]
