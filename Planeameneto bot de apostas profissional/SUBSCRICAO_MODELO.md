# SUBSCRICAO_MODELO — Modelo de Subscrição

**ID:** `BM-003` | **Fase:** #phase/1 | **Owner:** Business Manager | **Status:** #status/active

---

## 1. OBJETIVO

Documentar modelo de subscrição para uso do sistema (se aplicável).

---

## 2. TIPOS DE SUBSCRIÇÃO

| Tipo | Preço | Features |
|------|-------|----------|
| Basic | €50/mês | Sinais básicos |
| Pro | €200/mês | Sinais + dashboard |
| Enterprise | €500/mês | Sinais + dashboard + API |

---

## 3. FEATURES POR TIER

### Basic
- Sinais diários (até 5)
- Email de sinais
- Acesso a relatórios mensais

### Pro
- Sinais ilimitados
- Dashboard em tempo real
- Telegram alerts
- Suporte prioritário

### Enterprise
- Tudo do Pro
- API access
- Consultoria personalizada
- SLA garantido

---

## 4. MODELO DE PREÇO

```python
def calculate_subscription_price(tier, users=1):
    """
    Calcula preço de subscrição.
    
    Args:
        tier: Tipo de subscrição
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

- **Preço competitivo** com mercado
- **Escalável** por utilizador
- **Upgrade/downgrade** fácil

---

## 6. LINKS CRUZADOS

- [[02_Business_Model/INDEX]]
- [[SUBSCRIPTION_PRICING]]
