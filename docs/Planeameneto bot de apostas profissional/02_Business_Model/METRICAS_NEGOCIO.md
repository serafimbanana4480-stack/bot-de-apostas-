# Métricas de Negócio

**ID:** BM-002 | **Fase:** Todas | **Owner:** Product Owner

---

## 1. OBJETIVO

Definir e documentar todas as métricas de negócio críticas para monitorizar a saúde do modelo tipster e do sistema de apostas.

---

## 2. CATEGORIAS DE MÉTRICAS

### 2.1 Métricas de Receita

| Métrica | Fórmula | Target | Frequência |
|---------|---------|--------|------------|
| MRR (Monthly Recurring Revenue) | Σ(subscrições ativas × preço) | Crescimento 15%/mês | Mensal |
| ARR (Annual Recurring Revenue) | MRR × 12 | > €100k (Mês 12) | Mensal |
| ARPU (Average Revenue Per User) | MRR / subscritores ativos | > €50 | Mensal |
| Revenue Churn | (MRR perdido por churn / MRR início do mês) | < 5% | Mensal |
| Expansion Revenue | Upsells + cross-sells | > 10% de MRR | Mensal |

### 2.2 Métricas de Aquisição

| Métrica | Fórmula | Target | Frequência |
|---------|---------|--------|------------|
| CAC (Customer Acquisition Cost) | Custos marketing e vendas / novos clientes | < €40 | Trimestral |
| CPL (Cost Per Lead) | Custos marketing / leads gerados | < €10 | Mensal |
| Lead → Paid Conversion | Clientes pagos / leads qualificados | > 10% | Mensal |
| Organic Traffic Growth | (Tráfego atual - Tráfeco anterior) / Tráfego anterior | +20%/mês | Mensal |
| Time to First Purchase | Média dias desde registo até primeira subscrição | < 7 dias | Mensal |

### 2.3 Métricas de Retenção

| Métrica | Fórmula | Target | Frequência |
|---------|---------|--------|------------|
| Churn Rate | Clientes perdidos / clientes início do período | < 5%/mês | Mensal |
| Retention Rate | 1 - Churn Rate | > 95%/mês | Mensal |
| Net Revenue Retention (NRR) | (MRR atual + expansion - churn) / MRR anterior | > 100% | Mensal |
| DAU/MAU Ratio | Daily Active Users / Monthly Active Users | > 30% | Mensal |
| Feature Adoption Rate | Utilizadores que usam feature X / total utilizadores | > 50% (features core) | Mensal |

### 2.4 Métricas de Produto

| Métrica | Fórmula | Target | Frequência |
|---------|---------|--------|------------|
| Signal Delivery Rate | Sinais entregues / sinais gerados | 100% | Diário |
| Signal Latency | Tempo desde geração até entrega | < 2 minutos | Diário |
| Uptime | Tempo sistema operacional / tempo total | > 99.5% | Contínuo |
| API Response Time | Média tempo resposta API | < 200ms | Contínuo |
| Error Rate | Erros / total requests | < 0.1% | Contínuo |

### 2.5 Métricas de Satisfação

| Métrica | Fórmula | Target | Frequência |
|---------|---------|--------|------------|
| NPS (Net Promoter Score) | % Promotores - % Detratores | > 50 | Trimestral |
| CSAT (Customer Satisfaction) | Média avaliações (1-5) | > 4.5/5 | Mensal |
| Support Response Time | Média tempo primeira resposta | < 2h | Mensal |
| Support Resolution Time | Média tempo resolução ticket | < 24h | Mensal |
| Feature Request Volume | Número de requests por mês | Monitorizar | Mensal |

### 2.6 Métricas Financeiras

| Métrica | Fórmula | Target | Frequência |
|---------|---------|--------|------------|
| Gross Margin | (Receita - COGS) / Receita | > 80% | Mensal |
| Net Margin | (Receita - Custos totais) / Receita | > 30% | Mensal |
| Burn Rate | Custos mensais operacionais | < €2k | Mensal |
| Runway | Cash / Burn Rate | > 12 meses | Mensal |
| Cash Flow | Cash in - Cash out | Positivo | Mensal |

---

## 3. DASHBOARDS

### 3.1 Dashboard Executivo (Diário)

**KPIs Principais:**
- MRR atual
- Subscritores ativos
- Churn rate (últimos 30 dias)
- ROI médio dos sinais (últimos 30 dias)
- Uptime (últimas 24h)

### 3.2 Dashboard Produto (Semanal)

**KPIs Principais:**
- Signal delivery rate
- Signal latency
- Feature adoption rate
- Error rate
- Support tickets abertos

### 3.3 Dashboard Marketing (Mensal)

**KPIs Principais:**
- CAC por canal
- Lead conversion rate
- Organic traffic
- Social media engagement
- Email open rate

### 3.4 Dashboard Financeiro (Mensal)

**KPIs Principais:**
- Receita vs target
- Custos vs budget
- Margem bruta
- Margem líquida
- Cash flow

---

## 4. ALERTAS E THRESHOLDS

| Métrica | Threshold Warning | Threshold Critical | Ação |
|---------|-------------------|-------------------|------|
| Churn Rate | > 7% | > 10% | Investigar causas; campanha de retenção |
| Uptime | < 99% | < 95% | Investigar infraestrutura |
| Signal Delivery Rate | < 95% | < 90% | Investigar pipeline |
| CAC | > €50 | > €75 | Otimizar canais de aquisição |
| NPS | < 40 | < 20 | Survey detalhado; melhorias urgentes |
| Cash Flow | < €0 | < -€2k | Revisar custos; buscar financiamento |

---

## 5. ANÁLISE DE COHORT

### 5.1 Cohort Analysis por Mês de Aquisição

**Dimensões:**
- Retention por cohort
- Revenue por cohort
- Feature adoption por cohort
- LTV por cohort

**Frequência:** Mensal

**Objetivo:** Identificar padrões de comportamento e otimizar onboarding

### 5.2 Cohort Analysis por Tier

**Dimensões:**
- Upgrade rate (Base → Premium)
- Downgrade rate (Premium → Base)
- Churn por tier
- Feature usage por tier

**Frequência:** Trimestral

**Objetivo:** Otimizar pricing e features por tier

---

## 6. BENCHMARKS

### 6.1 Indústria SaaS B2C

| Métrica | Benchmark SaaS | Nosso Target |
|---------|----------------|--------------|
| Churn Rate | 5-7%/mês | < 5%/mês |
| LTV:CAC | 3:1 | > 40:1 |
| NPS | 30-50 | > 50 |
| ARPU | €50-100 | > €50 |
| Gross Margin | 70-80% | > 80% |

### 6.2 Indústria Tipster/Gambling

| Métrica | Benchmark | Nosso Target |
|---------|-----------|--------------|
| Signal Accuracy | 55-60% | > 55% |
| ROI Mensal | 3-5% | > 3% |
| Churn Rate | 10-15%/mês | < 5%/mês |
| Subscription Price | €20-100/mês | €29-299/mês |

---

## 7. REPORTING

### 7.1 Relatório Diário (Automático)

- MRR atual
- Subscritores ativos
- Sinais gerados/entregues
- ROI últimos 7 dias
- Uptime

### 7.2 Relatório Semanal (Manual)

- Análise de churn
- Feedback de clientes
- Performance de marketing
- Issues técnicos
- Planos para próxima semana

### 7.3 Relatório Mensal (Detalhado)

- Métricas financeiras completas
- Análise de cohorts
- Benchmark vs targets
- Roadmap update
- Riscos e oportunidades

### 7.4 Relatório Trimestral (Estratégico)

- Revisão de objetivos
- Análise de mercado
- Projeções atualizadas
- Decisões estratégicas

---

## 8. FERRAMENTAS

- **Google Analytics:** Web analytics
- **Mixpanel/Amplitude:** Product analytics
- **Stripe:** Payments e revenue analytics
- **Grafana:** Dashboards técnicos
- **Metabase:** Dashboards de negócio
- **Google Data Studio:** Relatórios visuais

---

## 9. LINKS CRUZADOS

- [[02_Business_Model/INDEX]] ← Índice principal
- [[02_Business_Model/MODELO_TIPSTER]] → Modelo de negócio tipster
- [[02_Business_Model/PLANO_FINANCEIRO_6_MESES]] → Projeções financeiras
- [[36_KPIs/INDEX]] → KPIs detalhados do sistema
