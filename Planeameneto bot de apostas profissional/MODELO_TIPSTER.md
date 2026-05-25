# MODELO_TIPSTER — Modelo Tipster

**ID:** `QR-019` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Documentar modelo para integração de sinais de tipsters externos.

---

## 2. AVALIAÇÃO DE TIPSTERS

| Métrica | Cálculo | Threshold |
|---------|---------|-----------|
| Accuracy | Win rate | > 52% |
| CLV | CLV médio | > 1% |
| Consistência | Variância de CLV | < 0.5% |
| Volume | N de sinais/mês | > 50 |

---

## 3. CÁLCULO DE CLV DO TIPSTER

```python
def calculate_tipster_clv(tipster_picks):
    """
    Calcula CLV de um tipster.
    
    Args:
        tipster_picks: Lista de picks do tipster
    
    Returns:
        CLV médio do tipster
    """
    clv_list = []
    
    for pick in tipster_picks:
        prob = 1 / pick['odd']  # Probabilidade implícita
        if pick['won']:
            clv = (pick['odd'] - 1) * prob - (1 - prob)
        else:
            clv = -prob
        clv_list.append(clv)
    
    return np.mean(clv_list)
```

---

## 4. INTEGRAÇÃO COM SISTEMA

```python
def integrate_tipster_signal(tipster_id, pick):
    """
    Integra sinal de tipster no sistema.
    
    Args:
        tipster_id: ID do tipster
        pick: Pick do tipster
    
    Returns:
        Sinal integrado ou None se rejeitado
    """
    # 1. Verificar se tipster é válido
    tipster = get_tipster(tipster_id)
    if not tipster['validated']:
        return None
    
    # 2. Calcular edge do tipster
    edge = calculate_tipster_edge(tipster_id)
    
    # 3. Se edge > threshold, integrar
    if edge > 0.02:
        signal = {
            'game_id': pick['game_id'],
            'prob': 1 / pick['odd'],
            'odd': pick['odd'],
            'edge': edge,
            'source': f'tipster_{tipster_id}'
        }
        return signal
    
    return None
```

---

## 5. CRITÉRIOS

- **Validar tipsters** antes de integração
- **CLV > 1%** para considerar
- **Mínimo 50 sinais** para avaliação

---

## 6. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[SINAI_GENERATION]]
