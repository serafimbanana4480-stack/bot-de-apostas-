# AFILIADOS_E_PARCEIRIAS — Afiliados e Parcerias

**ID:** `BM-008` | **Fase:** #phase/1 | **Owner:** Business Manager | **Status:** #status/active

---

## 1. OBJETIVO

Definir estratégia de afiliados e parcerias para expansão do negócio.

---

## 2. TIPOS DE PARCERIAS

| Tipo | Descrição | Comissão |
|------|-----------|----------|
| Bookmaker | Acesso a odds e liquidez | Share de PnL |
| Data Provider | Acesso a dados | Mensal fixo |
| Tipster Network | Sinais externos | Performance |
| Tecnologia | Infraestrutura | Mensal fixo |

---

## 3. CONTRATOS DE AFILIADOS

```python
def calculate_affiliate_commission(affiliate_type, pnl):
    """
    Calcula comissão de afiliado.
    
    Args:
        affiliate_type: Tipo de afiliado
        pnl: PnL gerado
    
    Returns:
        Comissão
    """
    commission_rates = {
        'bookmaker': 0.10,  # 10% do PnL
        'data_provider': 500,  # €500/mês fixo
        'tipster': 0.20,  # 20% do PnL
        'technology': 1000  # €1000/mês fixo
    }
    
    if affiliate_type in ['bookmaker', 'tipster']:
        return pnl * commission_rates[affiliate_type]
    else:
        return commission_rates[affiliate_type]
```

---

## 4. ONBOARDING

### Fase 1: Contacto
- Identificar parceiros potenciais
- Proposta de valor
- NDA se necessário

### Fase 2: Negociação
- Termos de contrato
- Comissões e SLAs
- Timeline de implementação

### Fase 3: Integração
- Integração técnica
- Testes piloto
- Lançamento

---

## 5. CRITÉRIOS

- **Contrato escrito** para todas as parcerias
- **SLA definido** para serviços
- **Review trimestral** de performance

---

## 6. LINKS CRUZADOS

- [[02_Business_Model/INDEX]]
- [[EVOLUCAO_SAAS]]
