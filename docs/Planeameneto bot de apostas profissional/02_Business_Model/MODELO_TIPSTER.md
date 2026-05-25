# Modelo Tipster

**ID:** BM-001 | **Fase:** Todas | **Owner:** Product Owner

---

## 1. OBJETIVO

Definir o modelo de negócio tipster que financia os custos operacionais do sistema de apostas e gera receita adicional.

---

## 2. VISÃO GERAL

O modelo tipster é um serviço de SaaS onde subscritores pagam uma mensalidade para receber sinais de apostas validados pelo sistema quantitativo. Este modelo serve duas funções:

1. **Financiamento:** Receitas de subscrições cobrem custos operacionais (VPS, dados, legal)
2. **Validação Social:** Base de subscritores valida a qualidade dos sinais através de track record público

---

## 3. TIERS DE SUBSCRIÇÃO

### 3.1 Tier Base (€29/mês)

**Inclui:**
- Sinais em tempo real via Telegram
- Dashboard básico de performance
- Histórico de sinais últimos 30 dias
- Suporte por email

**Limitações:**
- Máximo 20 sinais/dia
- Acesso a mercados principais (NBA Moneyline, Spread)
- Sem one-click betting

### 3.2 Tier Premium (€79/mês)

**Inclui tudo do Base +:**
- Sinais ilimitados
- Acesso a todos os mercados (Totals, Player Props)
- Dashboard avançado com analytics
- One-click betting (Betfair API)
- Notificações push
- Suporte prioritário (Telegram)
- Acesso a relatórios mensais detalhados

### 3.3 Tier Enterprise (€299/mês)

**Inclui tudo do Premium +:**
- API dedicada para integração customizada
- White-label option (rebranding)
- Consultoria mensal 1h
- Acesso antecipado a features beta
- SLA garantido
- Suporte 24/7

---

## 4. FLUXO DE ONBOARDING

```
1. Lead visita landing page
2. Lead regista email para lista de espera
3. Lead recebe convite para beta (fase inicial)
4. Lead cria conta (email, password, país)
5. Lead seleciona tier
6. Lead completa KYC (opcional, apenas para Enterprise)
7. Lead configura método de pagamento (Stripe)
8. Pagamento confirmado → acesso ativado
9. Lead recebe boas-vindas + onboarding guide
10. Lead começa a receber sinais
```

---

## 5. RETENÇÃO E CHURN

### 5.1 Estratégias de Retenção

- **Track Record Transparente:** Todos os sinais públicos com ROI real
- **Comunidade:** Canal Telegram para discussão e partilha
- **Conteúdo Educativo:** Artigos semanais sobre betting quantitativo
- **Feedback Loop:** Surveys mensais para melhorias
- **Gamification:** Badges, rankings, metas

### 5.2 Prevenção de Churn

- **Alerta de Churn Risk:** Se subscritor não segue > 70% dos sinais por 2 semanas
- **Oferta de Upgrade:** Desconto temporário para Premium/Enterprise
- **Pauses Flexíveis:** Permitir pausa de subscrição por 1-3 meses
- **Re-engagement:** Campanhas de email reativadoras

---

## 6. CAC E LTV

### 6.1 CAC Estimado

| Canal | CAC Estimado | % de Aquisição |
|-------|--------------|----------------|
| Organic/Referral | €15 | 40% |
| SEO/Content | €25 | 30% |
| Paid Social | €50 | 20% |
| Affiliate | €40 | 10% |

**CAC Médio:** €28

### 6.2 LTV Estimado

| Tier | LTV (12 meses) | LTV (24 meses) |
|------|----------------|----------------|
| Base | €348 | €696 |
| Premium | €948 | €1,896 |
| Enterprise | €3,588 | €7,176 |

**LTV Médio:** €1,628 (assumindo mix: 50% Base, 40% Premium, 10% Enterprise)

### 6.3 LTV:CAC Ratio

- **LTV/CAC Médio:** 58x
- **Break-even:** 1.1 meses
- **Target:** > 40x

---

## 7. COMPLIANCE LEGAL

### 7.1 Disclaimers Obrigatórios

- "Apostas envolvem risco financeiro. Aposte apenas o que pode perder."
- "Sinais são para fins informativos. Não garantimos lucros."
- "Rendimento passado não garante rendimento futuro."
- "Não somos consultores financeiros."

### 7.2 Regulamentação

- **SRIJ (Portugal):** Licença de jogo online não necessária para tipster (serviço de informação)
- **GDPR:** Consentimento explícito para processamento de dados pessoais
- **Consumidor:** Direito de cancelamento em 14 dias (EU)

---

## 8. MÉTRICAS DE SUCESSO

| Métrica | Tier | Preço/Mês | Conteúdo |
|------|-----------|----------|
| Único | 29€ | Todos os sinais via Telegram + edge estimado + CLV histórico |
| CAC | < €40 | Trimestral |
| LTV:CAC | > 40x | Trimestral |
| Taxa de Conversão Lead → Paid | > 10% | Mensal |

---

## 9. BACKLOG DE PRODUTO

- [ ] Criar landing page com copywriting otimizado
- [ ] Implementar sistema de registo de utilizadores
- [ ] Integrar Stripe para pagamentos
- [ ] Desenvolver dashboard de subscritor
- [ ] Configurar bot Telegram para entrega de sinais
- [ ] Criar sistema de gestão de subscrições
- [ ] Implementar analytics básico (Google Analytics)
- [ ] Desenvolver sistema de referências/afiliados
- [ ] Criar centro de ajuda/FAQ
- [ ] Implementar sistema de tickets de suporte

---

## 10. RISCOS E MITIGAÇÃO

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Regulação proíbe tipsters | Baixa | Crítico | Estrutura jurídica defensiva; diversificação geográfica |
| Alta taxa de churn | Média | Alto | Melhorar retenção; conteúdo educativo |
| Concorrência copia modelo | Alta | Médio | Comunidade; velocidade de execução; marca pessoal |
| Sinais com ROI negativo | Média | Crítico | Parar escala; investigar modelo; comunicar transparência |
| Problemas técnicos (downtime) | Média | Alto | SLA; redundância; comunicação proativa |

---

## 11. LINKS CRUZADOS

- [[02_Business_Model/INDEX]] ← Índice principal
- [[02_Business_Model/PLANO_FINANCEIRO_6_MESES]] → Projeções financeiras
- [[17_Legal/INDEX]] → Documentos legais
- [[16_Compliance/INDEX]] → Compliance e regulamentação
