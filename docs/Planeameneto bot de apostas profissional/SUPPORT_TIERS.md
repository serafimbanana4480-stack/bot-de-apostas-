# SUPPORT_TIERS — Níveis de Suporte

**ID:** `ORG-002` | **Fase:** #phase/1 | **Owner:** Project Manager | **Status:** #status/active

---

## 1. OBJETIVO

Definir níveis de suporte e procedimentos de escalonamento.

---

## 2. TIERS DE SUPORTE

| Tier | Responsável | Tempo de resposta | Escalonamento |
|------|--------------|-------------------|---------------|
| Tier 1 | Operations Engineer | 15 min | Para Tier 2 após 30 min |
| Tier 2 | Principal Quant | 1 hora | Para Tier 3 após 2 horas |
| Tier 3 | System Architect | 4 horas | N/A |

---

## 3. PROCEDIMENTO DE ESCALONAMENTO

```python
def escalate_issue(issue, current_tier):
    """
    Escalona issue para próximo tier.
    
    Args:
        issue: Issue reportado
        current_tier: Tier atual (1, 2, 3)
    
    Returns:
        Novo tier
    """
    if current_tier == 1:
        # Escalonar para Tier 2
        notify_tier_2(issue)
        return 2
    elif current_tier == 2:
        # Escalonar para Tier 3
        notify_tier_3(issue)
        return 3
    else:
        # Tier 3 - não escalar mais
        return 3
```

---

## 4. CATEGORIAS DE ISSUES

| Categoria | Tier inicial | Escalonamento |
|-----------|--------------|---------------|
| Sistema offline | Tier 1 | Sim |
| Performance degradada | Tier 1 | Sim |
| Erro de modelo | Tier 2 | Sim |
| Erro de dados | Tier 2 | Sim |
| Arquitetura | Tier 3 | Não |

---

## 5. CRITÉRIOS

- **Responder dentro do SLA**
- **Documentar resolução**
- **Atualizar knowledge base**

---

## 6. LINKS CRUZADOS

- [[01_Vision_And_Strategy/INDEX]]
- [[SUPPORT_LEVELS]]
