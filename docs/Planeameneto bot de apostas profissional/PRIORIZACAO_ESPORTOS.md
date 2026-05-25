# PRIORIZACAO_ESPORTOS — Priorização de Desportos

**ID:** `QR-018` | **Fase:** #phase/2 | **Owner:** Principal Quant Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir priorização de desportos para desenvolvimento do sistema.

---

## 2. MATRIZ DE PRIORIZAÇÃO

| Desporto | Liquidez | Dados | Complexidade | Prioridade |
|----------|----------|-------|--------------|------------|
| NBA | Alta | Excelente | Média | 1 |
| NFL | Alta | Excelente | Alta | 2 |
| MLB | Média | Excelente | Alta | 3 |
| Soccer | Alta | Boa | Alta | 4 |

---

## 3. CRITÉRIOS DE PRIORIZAÇÃO

| Critério | Peso |
|----------|------|
| Liquidez | 40% |
| Disponibilidade de dados | 30% |
| Complexidade de modelagem | 20% |
| Volume de apostas | 10% |

---

## 4. SCORE

```python
def calculate_sport_score(sport):
    """
    Calcula score de prioridade para um desporto.
    
    Args:
        sport: Nome do desporto
    
    Returns:
        Score (0-100)
    """
    scores = {
        'liquidity': get_liquidity_score(sport) * 0.4,
        'data': get_data_availability(sport) * 0.3,
        'complexity': (1 - get_complexity(sport)) * 0.2,
        'volume': get_betting_volume(sport) * 0.1
    }
    
    total_score = sum(scores.values()) * 100
    
    return total_score
```

---

## 5. ESTRATÉGIA

- **Fase 1:** NBA (prioridade máxima)
- **Fase 2:** Adicionar NFL se NBA bem-sucedido
- **Fase 3:** Expandir para outros desportos

---

## 6. CRITÉRIOS

- **Focar em 1 desporto** inicialmente
- **NBA prioridade** por liquidez e dados
- **Expandir gradualmente** após validação

---

## 7. LINKS CRUZADOS

- [[03_Quant_Research/INDEX]]
- [[TAXA_CLIQUES]]
