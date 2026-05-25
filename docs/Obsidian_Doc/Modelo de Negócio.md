# 💼 Modelo de Negócio

**Componente:** Business Model  
**Status:** ✅ Definido  
**Responsável:** Business Lead  
**Última atualização:** 2026-05-19

---

## 🎯 Visão do Negócio

Construir um negócio sustentável de tipster premium baseado em sinais quantitativos de value betting, começando com NBA e expandindo progressivamente, mantendo transparência e rigor estatístico.

---

## 💰 Streams de Receita

### 1. Subscrições Tipster (Principal)

#### Planos de Subscrição

| Plano | Preço | Features | Target |
|-------|-------|----------|--------|
| **Bronze** | 19€/mês | Sinais diários, estatísticas básicas | Recreativos |
| **Prata** | 49€/mês | Sinais + estatísticas detalhadas + relatórios | Semi-profissionais |
| **Ouro** | 99€/mês | Tudo acima + suporte prioritário + alertas customizados | Profissionais |

#### Projeção de Receita

**Mês 4 (Beta):**
- 10 beta testers @ 19€ = 190€

**Mês 5 (Lançamento):**
- 20 bronze @ 19€ = 380€
- 20 prata @ 49€ = 980€
- 10 ouro @ 99€ = 990€
- **Total: 2,350€**

**Mês 6 (Expansão):**
- 40 bronze @ 19€ = 760€
- 40 prata @ 49€ = 1,960€
- 20 ouro @ 99€ = 1,980€
- **Total: 4,700€**

**Mês 12 (Objetivo):**
- 100 bronze @ 19€ = 1,900€
- 100 prata @ 49€ = 4,900€
- 50 ouro @ 99€ = 4,950€
- **Total: 11,750€**

### 2. Apostas Próprias (Secundário)

#### Estratégia

- **Fase 1-3:** Sem apostas reais (shadow mode)
- **Fase 4:** 500-1000€ micro banca
- **Fase 5-6:** Escala gradual com lucro
- **Fase 7+:** Banca significativa

#### Projeção de Lucro

**Assumptions:**
- ROI: 3% mensal (conservador)
- Stake médio: 1% da banca
- Apostas por mês: 50

**Fase 4 (Mês 4):**
- Banca: 500€
- Stake médio: 5€
- Apostas: 50
- ROI esperado: 3%
- **Lucro: 15€**

**Fase 5 (Mês 5):**
- Banca: 1,000€
- Stake médio: 10€
- Apostas: 50
- ROI esperado: 3%
- **Lucro: 30€**

**Fase 6 (Mês 6):**
- Banca: 2,000€
- Stake médio: 20€
- Apostas: 50
- ROI esperado: 3%
- **Lucro: 60€**

### 3. Afiliados e Parcerias (Futuro)

#### Estratégia

- **Fase 7+:** Programa de afiliados
- **Comissão:** 20% recorrente
- **Target:** 10 afiliados ativos

#### Projeção

**Mês 12:**
- 10 afiliados
- 5 subscritores por afiliado
- 50 subscritores via afiliados
- Ticket médio: 49€
- Comissão: 20%
- **Receita: 490€**

---

## 📊 Custo Estrutura

### Custos Fixos Mensais

| Item | Custo | Notas |
|------|-------|-------|
| **VPS** | 20-50€ | DigitalOcean / AWS |
| **Database** | 15-30€ | PostgreSQL gerido |
| **Redis** | 10-20€ | Redis gerido |
| **MLflow** | 0€ | Self-hosted |
| **Monitoring** | 0€ | Prometheus/Grafana self-hosted |
| **Domain** | 10€ | Anual (0.83€/mês) |
| **Email** | 0€ | SendGrid free tier |
| **Telegram** | 0€ | Free |
| **Total** | **55-110€** | |

### Custos Variáveis

| Item | Custo | Notas |
|------|-------|-------|
| **Dados NBA API** | 0€ | Free |
| **Betfair API** | 0-100€ | Depende do volume |
| **Odds API** | 0€ | Free tier (500 req/mês) |
| **Transaction Fees** | 2-5% | Stripe/PayPal |
| **Legal** | 200-500€ | Consultoria (mensal) |
| **Total** | **Variable** | |

### Custos de Setup (One-time)

| Item | Custo | Notas |
|------|-------|-------|
| **Desenvolvimento** | 0€ | Internal |
| **Legal Setup** | 500-1,000€ | Documentos iniciais |
| **Marketing Launch** | 200-500€ | Ads básicos |
| **Total** | **700-1,500€** | |

---

## 📈 Análise de Unit Economics

### CAC (Customer Acquisition Cost)

**Canais:**
- **Orgânico (Telegram/Reddit):** 0€
- **Referrals:** 0€ + comissão
- **Paid Ads:** 10-20€ por subscrição
- **Content Marketing:** 5-10€ por subscrição

**CAC Médio Estimado:** 8-12€

### LTV (Lifetime Value)

**Assumptions:**
- Churn mensal: 5%
- Ticket médio: 49€
- Vida média: 20 meses

**Cálculo:**
```
LTV = Ticket Médio × Vida Média
LTV = 49€ × 20 = 980€
```

### LTV:CAC Ratio

```
LTV:CAC = 980€ / 10€ = 98:1
```

**Análise:** Excelente (objetivo > 3:1)

### Payback Period

```
Payback = CAC / (Ticket × Margem)
Payback = 10€ / (49€ × 0.8) = 0.25 meses
```

**Análise:** Excelente (< 1 mês)

---

## 🎯 Go-to-Market Strategy

### Fase 1: Shadow Mode (Mês 1-3)
- **Objetivo:** Validar edge
- **Ações:**
  - Desenvolver sistema
  - Shadow betting
  - Documentar resultados
- **Marketing:** Nenhum

### Fase 2: Beta Testing (Mês 3-4)
- **Objetivo:** Validar produto
- **Ações:**
  - Recrutar 10 beta testers
  - Coletar feedback
  - Refinar produto
- **Marketing:**
  - Reddit (r/sportsbetting)
  - Telegram communities
  - Referrals pessoais

### Fase 3: Lançamento (Mês 5)
- **Objetivo:** 50 subscritores
- **Ações:**
  - Lançamento oficial
  - Conteúdo educacional
  - Testemunhos beta
- **Marketing:**
  - Reddit (pago)
  - Twitter/X
  - SEO (blog)
  - Email marketing

### Fase 4: Crescimento (Mês 6+)
- **Objetivo:** 100+ subscritores
- **Ações:**
  - Programa de afiliados
  - Expansão de conteúdo
  - Parcerias
- **Marketing:**
  - Ads escalados
  - Influencers (micro)
  - Community building

---

## 📊 Projeção Financeira 6 Meses

### Resumo

| Mês | Receita | Custos | Lucro | Subscritores |
|-----|---------|--------|-------|--------------|
| **Mês 1** | 0€ | 55€ | -55€ | 0 |
| **Mês 2** | 0€ | 55€ | -55€ | 0 |
| **Mês 3** | 190€ | 55€ | 135€ | 10 |
| **Mês 4** | 2,350€ | 155€ | 2,195€ | 50 |
| **Mês 5** | 2,350€ | 155€ | 2,195€ | 50 |
| **Mês 6** | 4,700€ | 155€ | 4,545€ | 100 |
| **Total** | **9,590€** | **625€** | **8,965€** | - |

### Análise

- **Break-even:** Mês 3
- **Lucro acumulado:** 8,965€
- **ROI do projeto:** 1,434% (8,965€ / 625€)
- **Custo por subscritor:** 6.25€ (625€ / 100)

---

## 🎯 KPIs de Negócio

### KPIs de Aquisição
- **Novos subscritores por mês**
- **CAC por canal**
- **Conversion rate (free → paid)**

### KPIs de Retenção
- **Churn rate**
- **MRR Churn**
- **NPS (Net Promoter Score)**

### KPIs de Receita
- **MRR (Monthly Recurring Revenue)**
- **ARPU (Average Revenue Per User)**
- **LTV:CAC ratio**

### KPIs de Produto
- **Engagement (sinais abertos)**
- **Satisfação (feedback)**
- **Adoção de features**

---

## 🚨 Riscos de Negócio

### 1. Regulamentação
**Probabilidade:** Média  
**Impacto:** Alto  
**Mitigação:**
- Compliance desde o início
- Jurisdições favoráveis
- Consultoria legal

### 2. Churn Alto
**Probabilidade:** Média  
**Impacto:** Médio  
**Mitigação:**
- Produto de qualidade
- Comunicação transparente
- Comunidade ativa

### 3. Concorrência
**Probabilidade:** Alta  
**Impacto:** Médio  
**Mitigação:**
- Edge real (comprovado)
- Transparência estatística
- Diferenciação pela qualidade

### 4. Edge Desaparece
**Probabilidade:** Média  
**Impacto:** Crítico  
**Mitigação:**
- Melhoria contínua de modelos
- Diversificação de mercados
- Monitorização de CLV

---

## 📝 Próximos Passos de Negócio

### Imediatos (1-2 semanas)
- [ ] Preparar documentos legais
- [ ] Setup Stripe/PayPal
- [ ] Criar landing page básica
- [ ] Recrutar beta testers

### Curto Prazo (1-2 meses)
- [ ] Lançar beta testing
- [ ] Coletar feedback
- [ ] Refinar pricing
- [ ] Preparar lançamento

### Médio Prazo (3-6 meses)
- [ ] Lançamento oficial
- [ ] Escalar marketing
- [ ] Implementar afiliados
- [ ] Expandir mercados

---

## 🔗 Links Relacionados

- [[Visão e Estratégia]] - Filosofia e princípios
- [[Índice Mestre]] - Documentação completa
- [[Plano Financeiro]] - Detalhes financeiros
- [[Compliance]] - Aspectos legais

---

**Última atualização:** 2026-05-19  
**Responsável:** Business Lead  
**Status:** ✅ Definido