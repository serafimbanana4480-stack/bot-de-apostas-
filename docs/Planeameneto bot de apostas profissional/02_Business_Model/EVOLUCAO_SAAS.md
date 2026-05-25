# Evolução SaaS

**ID:** BM-003 | **Fase:** Todas | **Owner:** Product Owner

---

## 1. OBJETIVO

Definir a evolução do produto SaaS desde MVP até plataforma madura, alinhado com a validação progressiva do sistema de apostas.

---

## 2. FILOSOFIA DE EVOLUÇÃO

**Princípios:**
1. **Validação Antes de Escala:** Cada fase valida antes de expandir
2. **Pragmatismo:** Funcionalidades core primeiro; nice-to-have depois
3. **Feedback Loop:** Cliente input direciona roadmap
4. **Progressão Natural:** Features desbloqueiam com validação de edge

---

## 3. FASES DE EVOLUÇÃO

### FASE 0: Pre-Launch (Mês 0)

**Objetivo:** Preparar lançamento beta

**Atividades:**
- [ ] Criar landing page básica
- [ ] Configurar lista de espera (email capture)
- [ ] Criar conta Stripe
- [ ] Configurar domínio e SSL
- [ ] Setup infraestrutura básica (VPS, PostgreSQL)
- [ ] Criar conta Telegram bot
- [ ] Draft de Terms of Service e Privacy Policy

**Deliverables:**
- Landing page online
- Lista de espera com 50+ leads
- Infraestrutura operacional

---

### FASE 1: MVP Beta (Mês 1-2)

**Objetivo:** Validar product-market fit com 10 beta users

**Features:**
- Registo de utilizador (email, password)
- Dashboard básico (últimos 30 sinais)
- Entrega de sinais via Telegram (manual)
- Pagamento Stripe (Tier Base apenas)
- Suporte por email

**Critérios de Sucesso:**
- [ ] 10 beta users ativos
- [ ] 80%+ taxa de entrega de sinais
- [ ] Feedback positivo de 70%+ users
- [ ] Zero bugs críticos

**Próximo Passo:** Se aprovado → Fase 2

---

### FASE 2: Public Launch (Mês 3-4)

**Objetivo:** Lançamento público com Tier Base

**Features Novas:**
- Tier Base e Premium disponíveis
- Dashboard avançado (analytics básico)
- Sistema de gestão de subscrições (upgrade/downgrade)
- FAQ e Help Center
- Notificações por email
- Integrar sistema de tracking de apostas

**Marketing:**
- SEO/Content marketing iniciado
- Social media presence
- Referral program (beta)

**Critérios de Sucesso:**
- [ ] 50+ subscritores ativos
- [ ] MRR > €1,500
- [ ] Churn rate < 10%
- [ ] NPS > 30

**Próximo Passo:** Se aprovado → Fase 3

---

### FASE 3: Feature Expansion (Mês 5-6)

**Objetivo:** Adicionar features premium e one-click betting

**Features Novas:**
- One-click betting (Betfair API sandbox)
- Acesso a todos os mercados (Totals, Player Props)
- Analytics avançado (CLV por regime, feature importance)
- Sistema de referências/afiliados
- Push notifications
- Suporte prioritário (Telegram)

**Critérios de Sucesso:**
- [ ] 100+ subscritores ativos
- [ ] 30%+ em Tier Premium
- [ ] MRR > €4,000
- [ ] Churn rate < 7%

**Próximo Passo:** Se aprovado → Fase 4

---

### FASE 4: Auto-Execution (Mês 7-9)

**Objetivo:** Ativar execução automática e Tier Enterprise

**Features Novas:**
- One-click betting em produção (Betfair API)
- Tier Enterprise (API dedicada, white-label)
- API pública para integrações
- Relatórios mensais detalhados
- Gamification (badges, rankings)
- Comunidade (canal Telegram público)

**Critérios de Sucesso:**
- [ ] 200+ subscritores ativos
- [ ] 5+ clientes Enterprise
- [ ] MRR > €10,000
- [ ] Churn rate < 5%

**Próximo Passo:** Se aprovado → Fase 5

---

### FASE 5: Platform Maturity (Mês 10-12)

**Objetivo:** Plataforma madura com multi-sport

**Features Novas:**
- Multi-sport (NBA + NFL)
- Mobile app (iOS/Android)
- Advanced analytics (ML explainability)
- Custom alerts
- A/B testing de features
- Marketplace de estratégias (future)

**Critérios de Sucesso:**
- [ ] 500+ subscritores ativos
- [ ] 10+ clientes Enterprise
- [ ] MRR > €25,000
- [ ] Churn rate < 4%

**Próximo Passo:** Se aprovado → Fase 6

---

### FASE 6: Scale & Expansion (Mês 13-24)

**Objetivo:** Escala global e novos modelos de negócio

**Features Novas:**
- Multi-jurisdição (licenças internacionais)
- White-label completo (B2B)
- Marketplace de tipsters
- Social features (copiar apostas de top users)
- AI assistant personalizado
- Consultoria e treinamento

**Critérios de Sucesso:**
- [ ] 2,000+ subscritores ativos
- [ ] 50+ clientes Enterprise/B2B
- [ ] MRR > €100,000
- [ ] Churn rate < 3%

---

## 4. MATRIZ DE FEATURE RELEASE

| Feature | Fase 1 | Fase 2 | Fase 3 | Fase 4 | Fase 5 | Fase 6 |
|---------|--------|--------|--------|--------|--------|--------|
| Registo/Login | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dashboard Básico | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Telegram Sinais | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Stripe Pagamentos | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tier Base | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tier Premium | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dashboard Avançado | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Analytics Básico | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sistema Upgrade/Downgrade | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| FAQ/Help Center | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| One-Click Betting | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Multi-Markets | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Analytics Avançado | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Referral Program | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Push Notifications | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Suporte Telegram | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Tier Enterprise | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| API Pública | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Relatórios Mensais | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Gamification | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Comunidade | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Multi-Sport | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Mobile App | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| ML Explainability | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Custom Alerts | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| A/B Testing | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Multi-Jurisdição | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| White-Label B2B | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Marketplace Tipsters | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Social Features | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| AI Assistant | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Consultoria | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 5. DEPENDÊNCIAS POR FASE

### Fase 1 Dependências
- Sistema de paper trading validado
- Modelo com CLV > 2% em backtest
- Infraestrutura básica operacional

### Fase 2 Dependências
- Fase 1 aprovada
- 30 dias de paper trading com 100+ sinais
- Shadow mode operacional

### Fase 3 Dependências
- Fase 2 aprovada
- 50 apostas reais com ROI positivo
- Micro banca validada

### Fase 4 Dependências
- Fase 3 aprovada
- Banca escalada para €1,000+
- Auto-execução testada em sandbox

### Fase 5 Dependências
- Fase 4 aprovada
- Auto-execução 100% operacional
- Multi-sport validado (NFL)

### Fase 6 Dependências
- Fase 5 aprovada
- Banca > €10,000
- Track record de 12+ meses

---

## 6. RISCOS DE EVOLUÇÃO

| Risco | Fase | Mitigação |
|-------|------|-----------|
| Modelo não valida edge | 1-2 | Parar escala; investigar; comunicar transparência |
| Churn alto early adopters | 2-3 | Onboarding melhorado; suporte intensivo |
| One-click betting bugs | 3-4 | Testes extensivos; rollback rápido |
| API Betfair limita | 4-5 | Multi-casa; negociação com Betfair |
| Escala sobrecarrega infraestrutura | 5-6 | Arquitetura cloud-native; auto-scaling |
| Regulação muda | 6 | Diversificar jurisdições; compliance proativo |

---

## 7. KPIs POR FASE

| Fase | Subscritores | MRR | Churn | NPS |
|------|--------------|-----|-------|-----|
| Fase 1 | 10 | €290 | N/A | > 30 |
| Fase 2 | 50 | €1,500 | < 10% | > 30 |
| Fase 3 | 100 | €4,000 | < 7% | > 40 |
| Fase 4 | 200 | €10,000 | < 5% | > 50 |
| Fase 5 | 500 | €25,000 | < 4% | > 50 |
| Fase 6 | 2,000 | €100,000 | < 3% | > 50 |

---

## 8. LINKS CRUZADOS

- [[02_Business_Model/INDEX]] ← Índice principal
- [[02_Business_Model/MODELO_TIPSTER]] → Modelo de negócio tipster
- [[24_Product_Roadmap/INDEX]] → Roadmap detalhado de produto
- [[01_Vision_And_Strategy/FILOSOFIA_MVP]] → Filosofia MVP
