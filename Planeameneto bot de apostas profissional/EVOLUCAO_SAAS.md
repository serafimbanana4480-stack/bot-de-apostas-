# EVOLUCAO_SAAS — Evolução para SaaS

**ID:** `BM-007` | **Fase:** #phase/1 | **Owner:** Business Manager | **Status:** #status/active

---

## 1. OBJETIVO

Definir roadmap para evolução do sistema para modelo SaaS.

---

## 2. FASES DE EVOLUÇÃO

| Fase | Descrição | Timeline |
|------|-----------|----------|
| Fase 0 | Sistema interno | Atual |
| Fase 1 | Beta com amigos | 3 meses |
| Fase 2 | Early adopters | 6 meses |
| Fase 3 | Público geral | 12 meses |

---

## 3. REQUISITOS POR FASE

### Fase 0 (Interno)
- Sistema operacional
- ROI positivo
- Documentação completa

### Fase 1 (Beta)
- UI básica
- Autenticação simples
- Suporte manual

### Fase 2 (Early Adopters)
- UI robusta
- Pagamentos integrados
- Suporte prioritário

### Fase 3 (Público)
- Escalável
- Marketing ativo
- Suporte 24/7

---

## 4. PRICING SaaS

```python
def calculate_saas_pricing(tier, users):
    """
    Calcula pricing SaaS.
    
    Args:
        tier: Tier (basic/pro/enterprise)
        users: Número de utilizadores
    
    Returns:
        Preço mensal
    """
    base_prices = {
        'basic': 50,
        'pro': 200,
        'enterprise': 500
    }
    
    return base_prices[tier] * users
```

---

## 5. CRITÉRIOS

- **ROI positivo** antes de lançar
- **Beta test** com 10-20 utilizadores
- **Escalável** antes de público geral

---

## 6. LINKS CRUZADOS

- [[02_Business_Model/INDEX]]
- [[SUBSCRICAO_MODELO]]
