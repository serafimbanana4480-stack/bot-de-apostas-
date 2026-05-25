# 02_Business_Model — INDEX

**ID:** `SEC-02` | **Fase:** #phase/3-10 | **Owner:** Product Owner | **Status:** #status/pending

---

## 1. OBJETIVO

Definir como o projeto gera receita, sustenta custos e cresce de MVP para operação sustentável. O modelo de negócio é **dual track**: tipster subscriptions financiam custos enquanto a banca própria gera lucro.

---

## 2. NOTAS FUNDAMENTAIS

- [[MODELO_TIPSTER]] — Estrutura de subscrição, tiers, pricing
- [[METRICAS_NEGOCIO]] — CAC, LTV, churn, MRR, ARPU
- [[EVOLUCAO_SAAS]] — De tipster simples a plataforma SaaS institucional
- [[AFILIADOS_E_PARCEIRIAS]] — Oportunidades de revenue share
- [[PLANO_FINANCEIRO_6_MESES]] — Projeções de cash flow, custos, break-even

---

## 3. MODELO DE RECEITA — FASES

### Fase 1-3 (Mês 1-3): Zero Receita
- Investimento próprio: 500-1000€ banca + 100€/mês infraestrutura
- Sem subscrições. Foco 100% em validação.

### Fase 4-5 (Mês 4-5): Tipster Beta Gratuito
- 5-10 subscritores beta gratuitos
- Objetivo: validar operacionalidade do envio de sinais
- Colecionar feedback de UX

### Fase 6 (Mês 6+): Tipster Pago
- **Único Tier:** 29€/mês — Todos os sinais via Telegram + edge estimado + CLV histórico
- **Máximo subscritores:** 100 (para garantir qualidade e exclusividade)
- **Pagamentos:** Stripe ou Paddle (geram IVA automaticamente)

---

## 4. ESTRUTURA DE CUSTOS

| Categoria | Mês 1-3 | Mês 4-6 | Mês 7-12 | Mês 12+ |
|-----------|---------|---------|----------|---------|
| VPS (4vCPU, 8GB) | 50€ | 50€ | 80€ | 150€ |
| Dados (gratuitos → premium) | 0€ | 0€ | 100€ | 300€ |
| APIs (Betfair) | 0€ | 0€ | 0€ | 50€ |
| Telegram/Comunicação | 0€ | 0€ | 20€ | 20€ |
| Ferramentas (Grafana, etc.) | 0€ | 0€ | 30€ | 50€ |
| Legal/Compliance | 0€ | 100€ | 100€ | 200€ |
| **TOTAL** | **50€** | **150€** | **330€** | **770€** |

---

## 5. PROJEÇÃO DE RECEITA

| Cenário | Subscritores Mês 6 | MRR Mês 6 | Subscritores Mês 12 | MRR Mês 12 |
|---------|-------------------|-----------|---------------------|------------|
| Pessimista | 20 | 580€ | 50 | 1.450€ |
| Realista | 50 | 1.450€ | 100 | 2.900€ |
| Otimista | 100 | 2.900€ | 100 (cap) | 2.900€ |

**Break-even:** 6 subscritores no Tier Base cobrem o VPS inicial.

---

## 6. RISCOS DE NEGÓCIO

| Risco | Prob | Impacto | Mitigação |
|-------|------|---------|-----------|
| Churn elevado devido a drawdowns | Alto | Alto | Transparência total de CLV; nunca prometer lucros |
| Regulamentação proíbe tipsters | Médio | Crítico | Disclaimer robusto; diversificar geograficamente |
| Concorrência de tipsters gratuitos | Alto | Médio | Diferenciação via transparência estatística e track record verificável |
| Custos de dados superam receita | Médio | Médio | Começar com dados gratuitos; reinvestir lucros incrementalmente |

---

## 7. BACKLOG DE NEGÓCIO

- [ ] Criar Terms of Service e Disclaimer de Risco (Fase 3)
- [ ] Implementar página pública de track record (Fase 3)
- [ ] Configurar pagamentos (Stripe/PayPal) para subscrições (Fase 5)
- [ ] Criar onboarding de subscritores via Telegram (Fase 4)
- [ ] Definir política de reembolso (Fase 5)
- [ ] Implementar sistema de referrals (Fase 8)

---

## 8. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Visão geral
- [[16_Compliance/INDEX]] → Restrições regulatórias
- [[17_Legal/INDEX]] → Documentos legais necessários
- [[35_Financial_Tracking/INDEX]] → Tracking de receitas e despesas
- [[24_Product_Roadmap/INDEX]] → Features do produto
