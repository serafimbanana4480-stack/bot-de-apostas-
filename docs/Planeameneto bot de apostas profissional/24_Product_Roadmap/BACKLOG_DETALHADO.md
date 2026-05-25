# BACKLOG_DETALHADO — Features Priorizadas e Estimadas

**ID:** `PR-001` | **Fase:** #phase/1-15 | **Owner:** Product Owner | **Status:** #status/pending

---

## 1. METODOLOGIA DE PRIORIZAÇÃO

### 1.1 Fórmula de Score

```
Score = (Impacto_Edge * 3) + (Impacto_Negocio * 2) - Esforço

Onde:
- Impacto_Edge: Critical=5, High=3, Medium=2, Low=1
- Impacto_Negocio: Critical=5, High=3, Medium=2, Low=1
- Esforço: 1s=1, 2s=2, 3s=3, 4s=4 (s = semanas)
```

### 1.2 Categorias de Prioridade

**Critical (Score > 12):** Bloqueador para próxima fase
- Deve ser feito na fase planeada
- Recursos alocados prioritariamente
- Não pode ser adiado

**High (Score 8-12):** Importante mas não bloqueador
- Deve ser feito na fase planeada
- Pode escorregar 1-2 semanas se necessário
- Alta prioridade de recursos

**Medium (Score 4-7):** Nice to have
- Pode ser adiado para fase seguinte
- Recursos apenas se disponíveis
- Revisão mensal

**Low (Score < 4):** Futuro
- Backlog para quando recursos disponíveis
- Não planeado para roadmap atual
- Revisão trimestral

---

## 2. BACKLOG POR FASE

### FASE 1: Fundação de Dados (Meses 1-2)

| ID | Feature | Descrição | Esforço | Impacto Edge | Impacto Negocio | Score | Prioridade |
|----|---------|-----------|---------|--------------|-----------------|-------|------------|
| PR-001 | Pipeline dados NBA histórico | Coleta de 3+ anos de dados NBA (jogos, odds, resultados) | 2s | High (3) | Medium (2) | 12 | Critical |
| PR-002 | Pipeline dados NBA tempo real | Coleta de dados em tempo real via APIs | 2s | High (3) | Medium (2) | 12 | Critical |
| PR-003 | Armazenamento PostgreSQL | Schema de BD e ingestão de dados | 1s | High (3) | Low (1) | 10 | High |
| PR-004 | Validação de dados | Sistema de validação e limpeza de dados | 1s | High (3) | Low (1) | 10 | High |
| PR-005 | Backup de dados | Sistema de backup automatizado | 0.5s | Medium (2) | Low (1) | 6 | Medium |
| PR-006 | Documentação de dados | Documentação de schema e dicionário de dados | 0.5s | Low (1) | Low (1) | 4 | Low |

**Total Fase 1:** 7 semanas de esforço
**Features Critical:** 2
**Features High:** 2
**Features Medium:** 1
**Features Low:** 1

---

### FASE 2: Modelo Baseline (Meses 3-4)

| ID | Feature | Descrição | Esforço | Impacto Edge | Impacto Negocio | Score | Prioridade |
|----|---------|-----------|---------|--------------|-----------------|-------|------------|
| PR-007 | Motor XGBoost baseline | Modelo ML baseline para NBA | 2s | Critical (5) | Low (1) | 16 | Critical |
| PR-008 | Meta-labeling | Sistema de meta-labeling para reduzir false positives | 1s | High (3) | Low (1) | 10 | High |
| PR-009 | Calibração por regime | Calibração de modelo por regime de mercado | 1s | High (3) | Low (1) | 10 | High |
| PR-010 | Sistema de backtesting | Framework completo de backtesting | 2s | High (3) | Low (1) | 10 | High |
| PR-011 | Validação walk-forward | Validação de modelo com walk-forward | 1s | High (3) | Low (1) | 10 | High |
| PR-012 | Feature engineering | Engenharia de features avançada | 1s | High (3) | Low (1) | 10 | High |
| PR-013 | Otimização de hiperparâmetros | Otimização automática de hiperparâmetros | 1s | Medium (2) | Low (1) | 7 | Medium |
| PR-014 | Visualização de backtest | Dashboard visual de resultados de backtest | 0.5s | Low (1) | Low (1) | 4 | Low |

**Total Fase 2:** 9.5 semanas de esforço
**Features Critical:** 1
**Features High:** 5
**Features Medium:** 1
**Features Low:** 1

---

### FASE 3: Validação Operacional (Meses 5-6)

| ID | Feature | Descrição | Esforço | Impacto Edge | Impacto Negocio | Score | Prioridade |
|----|---------|-----------|---------|--------------|-----------------|-------|------------|
| PR-015 | Telegram Bot sinais | Bot Telegram para entrega de sinais | 1s | Medium (2) | High (3) | 11 | High |
| PR-016 | Shadow mode multi-casa | Simulação multi-casa para validação de CLV | 2s | High (3) | Medium (2) | 13 | Critical |
| PR-017 | Paper trading engine | Motor de paper trading completo | 1s | High (3) | Low (1) | 10 | High |
| PR-018 | Sistema de alertas | Sistema de alertas por email/Telegram | 1s | Low (1) | High (3) | 8 | High |
| PR-019 | Dashboard básico | Dashboard básico de monitorização | 1s | Low (1) | High (3) | 8 | High |
| PR-020 | Logging avançado | Sistema de logging estruturado | 0.5s | Medium (2) | Low (1) | 6 | Medium |
| PR-021 | Monitorização de uptime | Monitorização de uptime do sistema | 0.5s | Medium (2) | Low (1) | 6 | Medium |

**Total Fase 3:** 7 semanas de esforço
**Features Critical:** 1
**Features High:** 4
**Features Medium:** 2
**Features Low:** 0

---

### FASE 4: Micro Banca (Meses 7-8)

| ID | Feature | Descrição | Esforço | Impacto Edge | Impacto Negocio | Score | Prioridade |
|----|---------|-----------|---------|--------------|-----------------|-------|------------|
| PR-022 | Tracking apostas | Sistema de tracking de apostas detalhado | 1s | Low (1) | High (3) | 8 | High |
| PR-023 | Reconciliação diária | Sistema de reconciliação diária automatizada | 1s | Low (1) | High (3) | 8 | High |
| PR-024 | Gestão banca (Kelly) | Implementação de Kelly criterion | 1s | High (3) | Low (1) | 10 | High |
| PR-025 | Dashboard PnL detalhado | Dashboard avançado de PnL e métricas | 1s | Low (1) | High (3) | 8 | High |
| PR-026 | Protocolo micro banca | Documentação e implementação de protocolo | 0.5s | High (3) | Low (1) | 10 | High |
| PR-027 | Exportação de dados | Exportação de dados para Excel/CSV | 0.5s | Low (1) | Medium (2) | 5 | Medium |
| PR-028 | Relatórios automáticos | Geração automática de relatórios diários | 0.5s | Low (1) | Medium (2) | 5 | Medium |

**Total Fase 4:** 5.5 semanas de esforço
**Features Critical:** 0
**Features High:** 5
**Features Medium:** 2
**Features Low:** 0

---

### FASE 5: Lançamento SaaS Beta (Meses 9-10)

| ID | Feature | Descrição | Esforço | Impacto Edge | Impacto Negocio | Score | Prioridade |
|----|---------|-----------|---------|--------------|-----------------|-------|------------|
| PR-029 | Landing page | Landing page de produto | 1s | Low (1) | High (3) | 8 | High |
| PR-030 | Registo utilizadores | Sistema de registo e autenticação | 1s | Low (1) | High (3) | 8 | High |
| PR-031 | Dashboard subscritor | Dashboard para subscritores | 1s | Low (1) | High (3) | 8 | High |
| PR-032 | Entrega sinais | Sistema de entrega de sinais a subscritores | 1s | Medium (2) | High (3) | 11 | High |
| PR-033 | Analytics básico | Analytics básico para subscritores | 1s | Low (1) | Medium (2) | 5 | Medium |
| PR-034 | Email marketing | Sistema de email marketing | 0.5s | Low (1) | Medium (2) | 5 | Medium |
| PR-035 | FAQ e suporte | FAQ e sistema de suporte básico | 0.5s | Low (1) | Medium (2) | 5 | Medium |

**Total Fase 5:** 6 semanas de esforço
**Features Critical:** 0
**Features High:** 4
**Features Medium:** 3
**Features Low:** 0

---

### FASE 6: Pagamentos e One-Click (Meses 11-12)

| ID | Feature | Descrição | Esforço | Impacto Edge | Impacto Negocio | Score | Prioridade |
|----|---------|-----------|---------|--------------|-----------------|-------|------------|
| PR-036 | Integração Stripe | Integração completa com Stripe | 2s | Low (1) | Critical (5) | 13 | Critical |
| PR-037 | Sistema subscrição | Sistema de gestão de subscrições | 1s | Low (1) | Critical (5) | 13 | Critical |
| PR-038 | One-click betting | One-click betting via Betfair | 2s | Low (1) | High (3) | 9 | High |
| PR-039 | Player Props model | Modelo para NBA Player Props | 3s | High (3) | Medium (2) | 11 | High |
| PR-040 | Expansão NBA Totals | Expansão para NBA Totals | 1s | Medium (2) | Medium (2) | 8 | High |
| PR-041 | Gestão de pagamentos | Dashboard de gestão de pagamentos | 0.5s | Low (1) | Medium (2) | 5 | Medium |
| PR-042 | Faturação automática | Sistema de faturação automática | 0.5s | Low (1) | Medium (2) | 5 | Medium |

**Total Fase 6:** 10 semanas de esforço
**Features Critical:** 2
**Features High:** 3
**Features Medium:** 2
**Features Low:** 0

---

### FASE 7: Execução Automática (Meses 13-15)

| ID | Feature | Descrição | Esforço | Impacto Edge | Impacto Negocio | Score | Prioridade |
|----|---------|-----------|---------|--------------|-----------------|-------|------------|
| PR-043 | Betfair API execution | Integração completa com Betfair API | 3s | Medium (2) | High (3) | 11 | High |
| PR-044 | Gestão ordens automática | Sistema de gestão de ordens automática | 2s | Medium (2) | High (3) | 10 | High |
| PR-045 | Reconciliação automática | Reconciliação automática de apostas | 1s | Low (1) | High (3) | 8 | High |
| PR-046 | Monitorização execução | Monitorização detalhada de execução | 1s | Medium (2) | High (3) | 11 | High |
| PR-047 | Latency optimization | Otimização de latência de execução | 2s | Medium (2) | Medium (2) | 8 | High |
| PR-048 | Error handling avançado | Sistema avançado de tratamento de erros | 1s | Medium (2) | Medium (2) | 8 | High |
| PR-049 | Circuit breakers | Circuit breakers para execução automática | 0.5s | High (3) | Low (1) | 10 | High |

**Total Fase 7:** 10.5 semanas de esforço
**Features Critical:** 0
**Features High:** 7
**Features Medium:** 0
**Features Low:** 0

---

### FASE 8: Premium e Escala (Meses 16-18)

| ID | Feature | Descrição | Esforço | Impacto Edge | Impacto Negocio | Score | Prioridade |
|----|---------|-----------|---------|--------------|-----------------|-------|------------|
| PR-050 | Tier Premium features | Features do tier Premium | 2s | Low (1) | High (3) | 9 | High |
| PR-051 | Analytics avançado | Analytics avançado para subscritores | 2s | Low (1) | High (3) | 9 | High |
| PR-052 | Multi-casa operacional | Operação em múltiplas casas | 3s | High (3) | Medium (2) | 11 | High |
| PR-053 | Escala banca 5k+ | Escala de banca para 5.000€+ | 1s | Medium (2) | High (3) | 10 | High |
| PR-054 | Alertas avançados | Sistema de alertas avançado | 1s | Low (1) | Medium (2) | 5 | Medium |
| PR-055 | Personalização | Personalização de dashboard | 1s | Low (1) | Medium (2) | 5 | Medium |
| PR-056 | API pública beta | API pública beta para developers | 2s | Low (1) | Medium (2) | 5 | Medium |

**Total Fase 8:** 12 semanas de esforço
**Features Critical:** 0
**Features High:** 4
**Features Medium:** 3
**Features Low:** 0

---

### FASE 9: Expansão NFL (Meses 19-21)

| ID | Feature | Descrição | Esforço | Impacto Edge | Impacto Negocio | Score | Prioridade |
|----|---------|-----------|---------|--------------|-----------------|-------|------------|
| PR-057 | Pipeline dados NFL | Coleta de dados NFL históricos e tempo real | 2s | High (3) | Medium (2) | 13 | Critical |
| PR-058 | Modelo NFL | Modelo ML para NFL | 2s | High (3) | Medium (2) | 13 | Critical |
| PR-059 | Backtest NFL | Backtesting de modelo NFL | 1s | High (3) | Low (1) | 10 | High |
| PR-060 | Paper trading NFL | Paper trading de NFL | 1s | High (3) | Low (1) | 10 | High |
| PR-061 | Lançamento NFL | Lançamento de NFL em produção | 0.5s | Medium (2) | High (3) | 10 | High |
| PR-062 | Dashboard NFL | Dashboard específico para NFL | 0.5s | Low (1) | Medium (2) | 5 | Medium |

**Total Fase 9:** 7 semanas de esforço
**Features Critical:** 2
**Features High:** 3
**Features Medium:** 1
**Features Low:** 0

---

### FASE 10: Enterprise e Institucional (Meses 22-24)

| ID | Feature | Descrição | Esforço | Impacto Edge | Impacto Negocio | Score | Prioridade |
|----|---------|-----------|---------|--------------|-----------------|-------|------------|
| PR-063 | API enterprise | API completa para clientes enterprise | 4s | Low (1) | High (3) | 9 | High |
| PR-064 | White-label option | Opção de white-label para grandes clientes | 3s | Low (1) | High (3) | 8 | High |
| PR-065 | Operação institucional | Operação institucional (50k€+) | 2s | High (3) | High (3) | 14 | Critical |
| PR-066 | Compliance documentação | Documentação de compliance | 2s | Low (1) | High (3) | 9 | High |
| PR-067 | Suporte 24/7 | Sistema de suporte 24/7 | 1s | Low (1) | High (3) | 8 | High |
| PR-068 | SLA enterprise | SLAs para clientes enterprise | 1s | Low (1) | Medium (2) | 5 | Medium |
| PR-069 | Multi-region | Infraestrutura multi-region | 2s | Medium (2) | Medium (2) | 8 | High |

**Total Fase 10:** 15 semanas de esforço
**Features Critical:** 1
**Features High:** 5
**Features Medium:** 1
**Features Low:** 0

---

## 3. BACKLOG ICEBERG (Futuro)

### Features Não Priorizadas (Fase 11+)

| ID | Feature | Descrição | Razão para Adiar |
|----|---------|-----------|------------------|
| PR-070 | Tennis ATP | Expansão para Tennis ATP | Recursos limitados, priorizar NFL primeiro |
| PR-071 | Esports | Expansão para Esports (LoL, CS:GO) | Dados premium caros, mercado menor |
| PR-072 | Soccer Premier League | Expansão para Soccer | Liquidez variável, complexidade alta |
| PR-073 | Mobile app native | App nativo iOS/Android | Web app suficiente por agora |
| PR-074 | Machine learning automático | AutoML para re-treino automático | Complexidade alta, ROI incerto |
| PR-075 | Social features | Features sociais (chat, fórum) | Não core ao produto |
| PR-076 | Gamification | Gamificação da experiência | Não core ao produto |
| PR-077 | Affiliate program | Programa de afiliados | Priorizar retenção primeiro |
| PR-078 | Marketplace de modelos | Marketplace para outros models | Foco no próprio modelo |
| PR-079 | Blockchain integration | Integração com blockchain | Não há benefício claro |

---

## 4. BACKLOG TÉCNICO

### Dívida Técnica

| ID | Issue | Prioridade | Esforço | Impacto |
|----|-------|------------|---------|---------|
| TECH-001 | Refactor código de backtesting | Medium | 2s | Manutenibilidade |
| TECH-002 | Melhorar testes unitários | High | 3s | Qualidade |
| TECH-003 | Otimizar queries de BD | Medium | 1s | Performance |
| TECH-004 | Migrar para Python 3.12 | Low | 1s | Manutenibilidade |
| TECH-005 | Implementar CI/CD completo | High | 2s | Qualidade |
| TECH-006 | Documentação de API | Medium | 1s | Usabilidade |
| TECH-007 | Security audit | High | 1s | Segurança |

---

## 5. BUGS CONHECIDOS

| ID | Bug | Severidade | Status | Prioridade |
|----|-----|------------|--------|------------|
| BUG-001 | Latência de sinais > 5min em picos | High | Open | Fase 3 |
| BUG-002 | Dashboard não carrega em Safari | Medium | Open | Fase 5 |
| BUG-003 | Reconciliação falha em apostas void | High | Open | Fase 4 |

---

## 6. PROCESSO DE GESTÃO DE BACKLOG

### 6.1 Revisão Mensal

- Revisar prioridades de features
- Adicionar novas features identificadas
- Remover features obsoletas
- Atualizar estimativas de esforço
- Revisar status de bugs e dívida técnica

### 6.2 Revisão Trimestral

- Revisão completa de roadmap
- Re-priorização baseada em mudanças de mercado
- Revisão de métricas de sucesso
- Ajuste de timeline se necessário

### 6.3 Critérios de Aceite

**Feature é considerada completa quando:**
- [ ] Implementação finalizada
- [ ] Testes unitários passando
- [ ] Testes de integração passando
- [ ] Documentação atualizada
- [ ] Code review aprovado
- [ ] Deploy em produção
- [ ] Monitorização ativa
- [ ] User acceptance (se aplicável)

---

## 7. MÉTRICAS DE BACKLOG

| Métrica | Target | Atual | Status |
|---------|--------|-------|--------|
| Features Critical por fase | 1-3 | - | - |
| Features High por fase | 3-5 | - | - |
| Esforço total por fase | 6-12 semanas | - | - |
| Features completas por mês | 2-4 | - | - |
| Bugs abertos | < 5 | 3 | ✓ |
| Dívida técnica | < 20 itens | 7 | ✓ |

---

## 8. BACKLOG PRIORIZADO 6 MESES

### 8.1 Mês 1: Fundação (Prioridade Crítica)

| ID | Feature | Descrição | Esforço | Prioridade | Fase |
|----|---------|-----------|---------|------------|------|
| PR-101 | Setup VPS | Configurar servidor VPS 4vCPU/8GB | 0.5s | Critical | Mês 1 |
| PR-102 | PostgreSQL setup | Instalar e configurar PostgreSQL | 0.5s | Critical | Mês 1 |
| PR-103 | Redis setup | Instalar e configurar Redis para cache | 0.5s | Critical | Mês 1 |
| PR-104 | Pipeline dados NBA | Coleta de dados históricos e tempo real | 2s | Critical | Mês 1 |
| PR-105 | Schema BD | Definir schema de base de dados | 1s | Critical | Mês 1 |
| PR-106 | Modelo XGBoost baseline | Modelo ML baseline para NBA | 2s | Critical | Mês 1 |
| PR-107 | Meta-labeling | Sistema de meta-labeling | 1s | High | Mês 1 |
| PR-108 | Backtesting framework | Framework completo de backtesting | 2s | Critical | Mês 1 |

### 8.2 Mês 2: Validação (Prioridade Alta)

| ID | Feature | Descrição | Esforço | Prioridade | Fase |
|----|---------|-----------|---------|------------|------|
| PR-109 | Paper trading engine | Motor de paper trading completo | 1s | Critical | Mês 2 |
| PR-110 | Telegram bot | Bot para entrega de sinais | 1s | High | Mês 2 |
| PR-111 | Shadow mode multi-casa | Simulação multi-casa | 2s | Critical | Mês 2 |
| PR-112 | Dashboard básico | Dashboard de monitorização | 1s | High | Mês 2 |
| PR-113 | Sistema de alertas | Alertas por email/Telegram | 0.5s | Medium | Mês 2 |
| PR-114 | Análise CLV | Sistema de análise de CLV | 1s | High | Mês 2 |
| PR-115 | Relatórios automáticos | Geração de relatórios diários | 0.5s | Medium | Mês 2 |

### 8.3 Mês 3: Micro Banca (Prioridade Crítica)

| ID | Feature | Descrição | Esforço | Prioridade | Fase |
|----|---------|-----------|---------|------------|------|
| PR-116 | Sistema tracking apostas | Sistema de tracking detalhado | 1s | Critical | Mês 3 |
| PR-117 | Reconciliação diária | Sistema de reconciliação automatizada | 1s | Critical | Mês 3 |
| PR-118 | Gestão banca Kelly | Implementação de Kelly criterion | 0.5s | Critical | Mês 3 |
| PR-119 | Dashboard PnL | Dashboard avançado de PnL | 1s | High | Mês 3 |
| PR-120 | Protocolo micro banca | Documentação e implementação | 0.5s | Critical | Mês 3 |
| PR-121 | Conta Betfair setup | Configuração conta Betfair | 0.5s | Critical | Mês 3 |
| PR-122 | Validação depósito | Processo de validação de depósito | 0.5s | Critical | Mês 3 |

### 8.4 Mês 4: Consolidação (Prioridade Alta)

| ID | Feature | Descrição | Esforço | Prioridade | Fase |
|----|---------|-----------|---------|------------|------|
| PR-123 | Análise 50 apostas | Análise após primeiras 50 apostas | 0.5s | High | Mês 4 |
| PR-124 | Sistema aumento banca | Sistema automatizado de aumento | 1s | High | Mês 4 |
| PR-125 | Otimização filtros | Otimização de filtros de liquidez | 1s | Medium | Mês 4 |
| PR-126 | Redução slippage | Estratégias para reduzir slippage | 1s | Medium | Mês 4 |
| PR-127 | Monitorização avançada | Sistema de monitorização em tempo real | 1s | High | Mês 4 |
| PR-128 | Backup automatizado | Sistema de backup automatizado | 0.5s | High | Mês 4 |

### 8.5 Mês 5: Escala (Prioridade Média-Alta)

| ID | Feature | Descrição | Esforço | Prioridade | Fase |
|----|---------|-----------|---------|------------|------|
| PR-129 | NBA Totals model | Modelo para NBA Totals | 2s | High | Mês 5 |
| PR-130 | Backtest Totals | Backtest de NBA Totals | 1s | High | Mês 5 |
| PR-131 | Paper trading Totals | Paper trading de Totals | 1s | High | Mês 5 |
| PR-132 | API Betfair config | Configuração API Betfair | 1s | Critical | Mês 5 |
| PR-133 | Sistema execução auto | Sistema de execução automática | 2s | Critical | Mês 5 |
| PR-134 | Gestão ordens auto | Gestão automática de ordens | 1s | High | Mês 5 |
| PR-135 | Sandbox testing | Testes em modo sandbox | 1s | High | Mês 5 |

### 8.6 Mês 6: Lançamento (Prioridade Alta)

| ID | Feature | Descrição | Esforço | Prioridade | Fase |
|----|---------|-----------|---------|------------|------|
| PR-136 | Ativação auto-execução | Ativação de execução automática | 0.5s | Critical | Mês 6 |
| PR-137 | Monitorização intensiva | Monitorização 24/7 pós-ativação | 1s | Critical | Mês 6 |
| PR-138 | Landing page | Landing page de produto | 1s | High | Mês 6 |
| PR-139 | Sistema registo | Sistema de registo de utilizadores | 1s | High | Mês 6 |
| PR-140 | Dashboard subscritor | Dashboard para subscritores | 1s | High | Mês 6 |
| PR-141 | Entrega sinais | Sistema de entrega de sinais | 1s | Critical | Mês 6 |
| PR-142 | Beta user onboarding | Onboarding de 10 beta users | 1s | High | Mês 6 |
| PR-143 | Feedback system | Sistema de coleta de feedback | 0.5s | Medium | Mês 6 |
| PR-144 | Avaliação 6 meses | Avaliação completa de 6 meses | 1s | High | Mês 6 |

### 8.7 Resumo de Esforço por Mês

| Mês | Esforço Total | Features Critical | Features High | Features Medium |
|------|---------------|-------------------|----------------|------------------|
| Mês 1 | 10s | 6 | 2 | 0 |
| Mês 2 | 7s | 2 | 4 | 1 |
| Mês 3 | 5s | 5 | 1 | 0 |
| Mês 4 | 5.5s | 2 | 3 | 0 |
| Mês 5 | 9s | 2 | 5 | 0 |
| Mês 6 | 8s | 3 | 4 | 1 |
| **Total** | **44.5s** | **20** | **19** | **2** |

---

## 9. LINKS CRUZADOS

- [[24_Product_Roadmap/INDEX]] ← Seção mãe
- [[00_Master_Index/INDEX]] → Cérebro do sistema
- [[02_Business_Model/INDEX]] → Modelo de negócio

- [[24_Product_Roadmap/INDEX]] ← Secao mae
- [[02_Business_Model/INDEX]] → Modelo de negócio
- [[23_Scaling/INDEX]] → Estratégias de escala
