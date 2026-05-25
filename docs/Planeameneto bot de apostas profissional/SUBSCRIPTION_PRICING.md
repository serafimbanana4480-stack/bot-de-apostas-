# SUBSCRIPTION_PRICING — Preço de Subscrição

**ID:** `BM-005` | **Fase:** #phase/1 | **Owner:** Business Manager | **Status:** #status/active

---

## 1. OBJETIVO

Definir estratégia de preços para subscrições.

---

## 2. ESTRATÉGIA DE PREÇO

### Value-Based Pricing
Preço baseado no valor entregue ao cliente (ROI esperado).

### Competitor-Based Pricing
Preço competitivo com soluções similares no mercado.

### Cost-Plus Pricing
Preço baseado em custo + margem.

---

## 3. CÁLCULO DE PREÇO

```python
def calculate_subscription_pricing(roi_per_month, margin=0.3):
    """
    Calcula preço baseado em ROI.
    
    Args:
        roi_per_month: ROI médio mensal (€)
        margin: Margem desejada (30%)
    
    Returns:
        Preço de subscrição
    """
    # Cliente paga 10-20% do ROI
    price = roi_per_month * 0.15
    
    # Adicionar margem
    price_with_margin = price * (1 + margin)
    
    return round(price_with_margin, 0)

# Exemplo: ROI €1000/mês → Preço €195/mês
```

---

## 4. TABELA DE PREÇOS

| Tier | Preço | ROI esperado | Valor |
|------|-------|--------------|-------|
| Basic | €50/mês | €200/mês | 4x |
| Pro | €200/mês | €1000/mês | 5x |
| Enterprise | €500/mês | €3000/mês | 6x |

---

## 5. CRITÉRIOS

- **ROI/Preço > 4x** para todos os tiers
- **Competitivo** com mercado
- **Escalável** com volume

---

## 6. LINKS CRUZADOS

- [[02_Business_Model/INDEX]]
- [[SUBSCRICAO_MODELO]]
