# SWITCHING_COSTS — Custos de Switching

**ID:** `BM-004` | **Fase:** #phase/1 | **Owner:** Business Manager | **Status:** #status/active

---

## 1. OBJETIVO

Documentar custos associados a mudar de bookmaker ou sistema.

---

## 2. TIPOS DE CUSTOS

| Tipo | Descrição | Estimativa |
|------|-----------|------------|
| Técnico | Integração nova API | 40h |
| Dados | Migração histórica | 20h |
| Treino | Treino equipa | 10h |
| Oportunidade | Downtime durante mudança | Varia |
| Risco | Erros durante transição | Alto |

---

## 3. CÁLCULO DE CUSTO

```python
def calculate_switching_cost(hours, hourly_rate=100):
    """
    Calcula custo de switching.
    
    Args:
        hours: Horas estimadas
        hourly_rate: Taxa horária
    
    Returns:
        Custo total
    """
    return hours * hourly_rate

# Exemplo
total_hours = 40 + 20 + 10  # 70h
switching_cost = calculate_switching_cost(total_hours)  # €7,000
```

---

## 4. MITIGAÇÃO

- **Documentação** detalhada do processo
- **Testes** em ambiente de staging
- **Rollback** plan disponível
- **Mudança gradual** (paralelo)

---

## 5. CRITÉRIOS

- **Benefício > custo** para mudar
- **Mudança planeada** com antecedência
- **Minimizar downtime**

---

## 6. LINKS CRUZADOS

- [[02_Business_Model/INDEX]]
- [[TEAM_ROLES]]
