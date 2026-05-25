# 24_Product_Roadmap — INDEX

**ID:** `SEC-24` | **Fase:** #phase/1-15 | **Owner:** Product Owner | **Status:** #status/active

---

## 1. OBJETIVO

Definir as funcionalidades do produto (sistema de apostas + tipster SaaS) e o seu cronograma de entrega. Priorização baseada em valor para edge e valor para negócio.

**Visão:** Um sistema de apostas esportivas quantitativo completo, com capacidade de operação automática e modelo de negócio SaaS de distribuição de sinais.

---

## 2. ROADMAP POR FASE (24 MESES)

### FASE 1: Fundação de Dados (Meses 1-2)

**Objetivo:** Coletar e processar dados históricos para backtesting

| ID | Feature | Prioridade | Esforço | Impacto Edge | Impacto Negócio |
|----|---------|------------|---------|--------------|-----------------|
| PR-001 | Pipeline de dados NBA (histórico) | Critical | 2s | High | Medium |
| PR-002 | Pipeline de dados NBA (tempo real) | Critical | 2s | High | Medium |
| PR-003 | Armazenamento em PostgreSQL | Critical | 1s | High | Low |
| PR-004 | Sistema de validação de dados | High | 1s | High | Low |

**Entregáveis:**
- 3+ anos de dados NBA históricos
- Pipeline de dados em tempo real operacional
- Base de dados estruturada e validada
- Documentação de schema

**Critérios de Sucesso:**
- [ ] Dados de 3+ temporadas NBA carregados
- [ ] Pipeline em tempo real capturando dados
- [ ] < 1% de dados corrompidos/inválidos
- [ ] Latência de ingestão < 5 segundos

---

### FASE 2: Modelo Baseline (Meses 3-4)

**Objetivo:** Desenvolver e validar modelo de ML baseline

| ID | Feature | Prioridade | Esforço | Impacto Edge | Impacto Negócio |
|----|---------|------------|---------|--------------|-----------------|
| PR-005 | Motor XGBoost baseline | Critical | 2s | Critical | Low |
| PR-006 | Meta-labeling | High | 1s | High | Low |
| PR-007 | Calibração por regime | High | 1s | High | Low |
| PR-008 | Sistema de backtesting | Critical | 2s | High | Low |
| PR-009 | Validação walk-forward | High | 1s | High | Low |

**Entregáveis:**
- Modelo XGBoost treinado e validado
- Sistema de meta-labeling operacional
- Sistema de backtesting completo
- Backtest de 3 anos com resultados positivos

**Critérios de Sucesso:**
- [ ] Modelo com CLV esperado > 2% em backtest
- [ ] Sharpe ratio > 1.0 em backtest
- [ ] Meta-labeling reduzindo false positives > 30%
- [ ] Backtest validado com walk-forward

---

### FASE 3: Validação Operacional (Meses 5-6)

**Objetivo:** Validar sistema com paper trading e shadow mode

| ID | Feature | Prioridade | Esforço | Impacto Edge | Impacto Negócio |
|----|---------|------------|---------|--------------|-----------------|
| PR-010 | Telegram Bot sinais | High | 1s | Medium | High |
| PR-011 | Shadow mode multi-casa | High | 2s | High | Medium |
| PR-012 | Paper trading engine | Critical | 1s | High | Low |
| PR-013 | Sistema de alertas | Medium | 1s | Low | High |
| PR-014 | Dashboard básico | Medium | 1s | Low | High |

**Entregáveis:**
- Telegram bot funcionando
- Shadow mode multi-casa operacional
- Paper trading engine validado
- 30 dias de paper trading com 100+ sinais

**Critérios de Sucesso:**
- [ ] Paper trading CLV ≥ backtest CLV - 1%
- [ ] Shadow mode CLV médio > 1.5%
- [ ] Uptime do sistema > 95%
- [ ] Telegram bot entregando sinais < 2 min após geração

---

### FASE 4: Micro Banca (Meses 7-8)

**Objetivo:** Primeira operação com dinheiro real (500-1000€)

| ID | Feature | Prioridade | Esforço | Impacto Edge | Impacto Negócio |
|----|---------|------------|---------|--------------|-----------------|
| PR-015 | Sistema de tracking de apostas | Critical | 1s | Low | High |
| PR-016 | Reconciliação diária | Critical | 1s | Low | High |
| PR-017 | Gestão de banca (Kelly) | Critical | 1s | High | Low |
| PR-018 | Dashboard PnL detalhado | Medium | 1s | Low | High |
| PR-019 | Protocolo de micro banca | High | 0.5s | High | Low |

**Entregáveis:**
- Sistema de tracking completo
- Reconciliação diária automatizada
- 50 primeiras apostas com dinheiro real
- ROI positivo validado

**Critérios de Sucesso:**
- [ ] 50 apostas executadas
- [ ] ROI real > 0%
- [ ] CLV real ≥ CLV paper - 1%
- [ ] Reconciliação 100% precisa

---

### FASE 5: Lançamento SaaS Beta (Meses 9-10)

**Objetivo:** Primeiros subscritores beta (gratuito)

| ID | Feature | Prioridade | Esforço | Impacto Edge | Impacto Negócio |
|----|---------|------------|---------|--------------|-----------------|
| PR-020 | Landing page | High | 1s | Low | High |
| PR-021 | Sistema de registo de utilizadores | High | 1s | Low | High |
| PR-022 | Dashboard de subscritor | Medium | 1s | Low | High |
| PR-023 | Sistema de entrega de sinais | High | 1s | Medium | High |
| PR-024 | Analytics básico | Medium | 1s | Low | Medium |

**Entregáveis:**
- Landing page funcional
- Sistema de registo operacional
- Dashboard de subscritor básico
- 10 subscritores beta

**Critérios de Sucesso:**
- [ ] Landing page online
- [ ] 10 subscritores beta registados
- [ ] Sinais entregues a 100% dos subscritores
- [ ] Feedback positivo de 80%+ dos beta users

---

### FASE 6: Pagamentos e One-Click (Meses 11-12)

**Objetivo:** Monetização e melhoria de UX

| ID | Feature | Prioridade | Esforço | Impacto Edge | Impacto Negócio |
|----|---------|------------|---------|--------------|-----------------|
| PR-025 | Integração Stripe | Critical | 2s | Low | Critical |
| PR-026 | Sistema de subscrição | Critical | 1s | Low | Critical |
| PR-027 | One-click betting (Betfair) | Medium | 2s | Low | High |
| PR-028 | Player Props model | Medium | 3s | High | Medium |
| PR-029 | Expansão para NBA Totals | High | 1s | Medium | Medium |

**Entregáveis:**
- Sistema de pagamentos funcional
- Subscrições ativas (Tier Base)
- One-click betting beta
- Modelo de Player Props operacional

**Critérios de Sucesso:**
- [ ] Primeira subscrição paga
- [ ] 50 subscritores ativos
- [ ] One-click betting funcionando para beta users
- [ ] Player Props com CLV > 1.5% em backtest

---

### FASE 7: Execução Automática (Meses 13-15)

**Objetivo:** API Betfair para execução automática

| ID | Feature | Prioridade | Esforço | Impacto Edge | Impacto Negócio |
|----|---------|------------|---------|--------------|-----------------|
| PR-030 | Betfair API execution | High | 3s | Medium | High |
| PR-031 | Gestão de ordens automática | High | 2s | Medium | High |
| PR-032 | Sistema de reconciliação automática | High | 1s | Low | High |
| PR-033 | Monitorização de execução | Critical | 1s | Medium | High |
| PR-034 | Latency optimization | Medium | 2s | Medium | Medium |

**Entregáveis:**
- API Betfair integrada
- Execução automática funcional
- Sistema de monitorização
- Latência < 500ms

**Critérios de Sucesso:**
- [ ] 100% das apostas executadas via API
- [ ] Latência média < 500ms
- [ ] Fill rate > 90%
- [ ] Zero erros críticos em 30 dias

---

### FASE 8: Premium e Escala (Meses 16-18)

**Objetivo:** Tier Premium e escala de banca

| ID | Feature | Prioridade | Esforço | Impacto Edge | Impacto Negócio |
|----|---------|------------|---------|--------------|-----------------|
| PR-035 | Tier Premium (features) | High | 2s | Low | High |
| PR-036 | Analytics avançado | Medium | 2s | Low | High |
| PR-037 | Multi-casa operacional | High | 3s | High | Medium |
| PR-038 | Escala de banca (5.000€+) | High | 1s | Medium | High |
| PR-039 | Sistema de alertas avançado | Medium | 1s | Low | Medium |

**Entregáveis:**
- Tier Premium lançado
- Multi-casa operacional
- Banca escalada para 5.000€+
- 200 subscritores totais

**Critérios de Sucesso:**
- [ ] 50 subscritores Premium
- [ ] Operação em 3+ casas
- [ ] Banca > 5.000€
- [ ] MRR > 5.000€

---

### FASE 9: Expansão NFL (Meses 19-21)

**Objetivo:** Adicionar NFL ao portfólio

| ID | Feature | Prioridade | Esforço | Impacto Edge | Impacto Negócio |
|----|---------|------------|---------|--------------|-----------------|
| PR-040 | Pipeline de dados NFL | High | 2s | High | Medium |
| PR-041 | Modelo NFL | High | 2s | High | Medium |
| PR-042 | Backtest NFL | High | 1s | High | Low |
| PR-043 | Paper trading NFL | High | 1s | High | Low |
| PR-044 | Lançamento NFL | Medium | 0.5s | Medium | High |

**Entregáveis:**
- Dados NFL históricos (3+ anos)
- Modelo NFL validado
- NFL em produção

**Critérios de Sucesso:**
- [ ] NFL CLV > 2% em backtest
- [ ] 50 apostas NFL em paper trading
- [ ] NFL em produção
- [ ] Diversificação de portfólio

---

### FASE 10: Enterprise e Institucional (Meses 22-24)

**Objetivo:** Tier Enterprise e operação institucional

| ID | Feature | Prioridade | Esforço | Impacto Edge | Impacto Negócio |
|----|---------|------------|---------|--------------|-----------------|
| PR-045 | API enterprise | High | 4s | Low | High |
| PR-046 | White-label option | Medium | 3s | Low | High |
| PR-047 | Operação institucional (50k€+) | High | 2s | High | High |
| PR-048 | Compliance e documentação | Critical | 2s | Low | High |
| PR-049 | Suporte 24/7 | Medium | 1s | Low | High |

**Entregáveis:**
- API enterprise funcional
- Operação institucional
- Documentação de compliance
- 5+ clientes enterprise

**Critérios de Sucesso:**
- [ ] API enterprise entregue
- [ ] Banca > 50.000€
- [ ] 5 clientes enterprise
- [ ] MRR > 20.000€

---

## 3. BACKLOG DE PRODUTO RESUMIDO

| ID | Feature | Prioridade | Fase | Esforço | Impacto Edge | Impacto Negócio |
|----|---------|------------|------|---------|--------------|-----------------|
| PR-001 | Pipeline dados NBA | Critical | 1 | 2s | High | Medium |
| PR-002 | Pipeline dados NBA RT | Critical | 1 | 2s | High | Medium |
| PR-005 | XGBoost baseline | Critical | 2 | 2s | Critical | Low |
| PR-008 | Backtesting system | Critical | 2 | 2s | High | Low |
| PR-010 | Telegram Bot | High | 3 | 1s | Medium | High |
| PR-011 | Shadow mode | High | 3 | 2s | High | Medium |
| PR-012 | Paper trading | Critical | 3 | 1s | High | Low |
| PR-015 | Tracking apostas | Critical | 4 | 1s | Low | High |
| PR-016 | Reconciliação | Critical | 4 | 1s | Low | High |
| PR-025 | Stripe integration | Critical | 6 | 2s | Low | Critical |
| PR-026 | Subscrição system | Critical | 6 | 1s | Low | Critical |
| PR-030 | Betfair API exec | High | 7 | 3s | Medium | High |
| PR-035 | Tier Premium | High | 8 | 2s | Low | High |
| PR-037 | Multi-casa | High | 8 | 3s | High | Medium |
| PR-045 | API enterprise | High | 10 | 4s | Low | High |
| PR-047 | Operação institucional | High | 10 | 2s | High | High |

*(s = semanas de trabalho a tempo inteiro)*

---

## 4. CRITÉRIOS DE PRIORIZAÇÃO

### 4.1 Fórmula de Score

```
Score = (Impacto_Edge * 3) + (Impacto_Negocio * 2) - Esforço

Onde:
- Impacto_Edge: Critical=5, High=3, Medium=2, Low=1
- Impacto_Negocio: Critical=5, High=3, Medium=2, Low=1
- Esforço: 1s=1, 2s=2, 3s=3, 4s=4
```

### 4.2 Categorias de Prioridade

**Critical:** Bloqueador para próxima fase
- Deve ser feito na fase planeada
- Recursos alocados prioritariamente

**High:** Importante mas não bloqueador
- Deve ser feito na fase planeada
- Pode escorregar 1-2 semanas se necessário

**Medium:** Nice to have
- Pode ser adiado para fase seguinte
- Recursos apenas se disponíveis

**Low:** Futuro
- Backlog para quando recursos disponíveis
- Não planeado para roadmap atual

---

## 5. MÉTRICAS DE PRODUTO

### 5.1 Métricas de Edge

| Métrica | Target | Frequência |
|---------|--------|------------|
| CLV médio | > 2% | Diário |
| ROI mensal | > 3% | Mensal |
| Sharpe ratio | > 1.0 | Mensal |
| Max drawdown | < 15% | Contínuo |
| Fill rate | > 90% | Diário |

### 5.2 Métricas de Negócio

| Métrica | Target | Frequência |
|---------|--------|------------|
| Subscritores ativos | Crescimento 10%/mês | Mensal |
| Churn rate | < 5% | Mensal |
| MRR | Crescimento 15%/mês | Mensal |
| CAC | < 3x LTV | Trimestral |
| NPS | > 50 | Trimestral |

### 5.3 Métricas de Produto

| Métrica | Target | Frequência |
|---------|--------|------------|
| Uptime | > 99.5% | Contínuo |
| Latência de sinais | < 2 min | Diário |
| Taxa de entrega | 100% | Diário |
| Satisfação user | > 4/5 | Mensal |

---

## 6. RISCOS E MITIGAÇÃO

### 6.1 Riscos de Produto

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Modelo degrada | Média | Crítico | Monitorização CLV contínua |
| API Betfair limita | Baixa | Alto | Multi-casa como backup |
| Regulação muda | Baixa | Crítico | Diversificar jurisdições |
| Competição aumenta | Alta | Médio | Focar em qualidade e UX |
| Churn alto | Média | Alto | Melhorar retenção e suporte |

### 6.2 Planos de Contingência

**Se modelo degrada:**
- Parar escala imediatamente
- Retornar ao backtest
- Retreinar modelo
- Reduzir banca até validação

**Se API Betfair limita:**
- Ativar multi-casa
- Reduzir volume
- Negociar com Betfair
- Considerar exchange alternativas

**Se regulação muda:**
- Consultar legal
- Adaptar a requisitos
- Diversificar jurisdições
- Comunicar com subscritores

---

## 7. ROADMAP DETALHADO 6 MESES (FOCO OPERACIONAL)

### 7.1 Visão Geral

Este roadmap detalha os primeiros 6 meses de operação, focando em:
- Validação com paper trading (Mês 1-2)
- Micro banca 500-1000€ (Mês 3-4)
- Escala progressiva (Mês 5-6)

### 7.2 Mês 1: Fundação e Paper Trading

**Objetivo:** Estabelecer infraestrutura e iniciar paper trading

**Semana 1-2: Setup de Infraestrutura**
- Configurar servidor VPS (4vCPU, 8GB RAM)
- Instalar PostgreSQL, Redis, Python
- Configurar pipelines de dados NBA
- Implementar coleta de dados históricos

**Semana 3-4: Modelo Baseline**
- Desenvolver modelo XGBoost baseline
- Implementar meta-labeling
- Criar sistema de backtesting
- Validar com 3 anos de dados

**Semana 5-6: Paper Trading Setup**
- Implementar motor de paper trading
- Configurar sistema de notificações Telegram
- Criar dashboard básico
- Iniciar paper trading

**Entregáveis:**
- Infraestrutura operacional
- Modelo com CLV > 2% em backtest
- Paper trading iniciado

**Critérios de Sucesso:**
- [ ] 3+ anos de dados carregados
- [ ] Modelo com CLV > 2% em backtest
- [ ] Paper trading capturando sinais
- [ ] Uptime > 95%

### 7.3 Mês 2: Validação e Shadow Mode

**Objetivo:** Validar sistema com paper trading e shadow mode

**Semana 1-2: Paper Trading Contínuo**
- Coletar 50+ sinais de paper trading
- Analisar CLV paper vs backtest
- Identificar problemas operacionais
- Ajustar filtros se necessário

**Semana 3-4: Shadow Mode**
- Implementar shadow mode multi-casa
- Configurar captura em Betfair, Pinnacle, Smarkets
- Analisar True CLV
- Identificar melhor casa para execução

**Semana 5-6: Análise e Decisão**
- Completar 100+ sinais de paper trading
- Analisar métricas de validação
- Decisão: avançar para micro banca ou revisar
- Se aprovado: preparar depósito

**Entregáveis:**
- 100+ sinais de paper trading
- Relatório de validação completo
- Shadow mode operacional
- Decisão sobre micro banca

**Critérios de Sucesso:**
- [ ] 100+ sinais de paper trading
- [ ] CLV paper ≥ CLV backtest - 1%
- [ ] True CLV > 1.5%
- [ ] Uptime > 95%
- [ ] Sem erros críticos

### 7.4 Mês 3: Micro Banca Inicial

**Objetivo:** Primeira operação com dinheiro real (500€)

**Semana 1: Preparação**
- Verificar conta Betfair Exchange
- Configurar 2FA
- Depositar 500€
- Configurar sistema de tracking

**Semana 2: Primeiras 20 Apostas**
- Execução manual de sinais
- Registro meticuloso de cada aposta
- Monitorização de slippage real
- Ajuste de processo se necessário

**Semana 3-4: Próximas 30 Apostas**
- Continuar execução manual
- Analisar CLV real vs paper
- Validar slippage aceitável
- Verificar psicologia do operador

**Semana 5-6: Análise Após 50 Apostas**
- Comparar métricas reais vs paper
- Decisão: continuar ou parar
- Se continuar: planejar aumento para 1000€
- Se parar: investigar e corrigir

**Entregáveis:**
- 50 apostas com dinheiro real executadas
- Sistema de tracking operacional
- Relatório de comparação real vs paper
- Decisão sobre continuação

**Critérios de Sucesso:**
- [ ] 50 apostas executadas
- [ ] ROI real > 0%
- [ ] CLV real ≥ CLV paper - 1%
- [ ] Slippage < 2%
- [ ] Sem erros críticos

### 7.5 Mês 4: Consolidação e Primeiro Aumento

**Objetivo:** Consolidar operação e primeiro aumento para 1000€

**Semana 1-2: Continuação (50-100 Apostas)**
- Executar mais 50 apostas
- Atingir 100 apostas totais
- Analisar consistência de performance
- Validar operação estável

**Semana 3: Avaliação de Aumento**
- Verificar critérios de aumento
- ROI > 3% últimos 30 dias
- CLV real > 2%
- Drawdown < 15%

**Semana 4: Aumento para 1000€**
- Depositar 500€ adicionais
- Atualizar limites de stake
- Recalcular Kelly fraction
- Ajustar exposição diária

**Semana 5-6: Monitorização Pós-Aumento**
- Monitorizar intensivamente
- Métricas diárias
- Se drawdown > 10%: considerar rollback
- Validar que performance mantida

**Entregáveis:**
- 100 apostas totais executadas
- Banca aumentada para 1000€
- Sistema operacional em nova escala
- 30 dias de monitorização pós-aumento

**Critérios de Sucesso:**
- [ ] 100 apostas totais
- [ ] ROI > 3% últimos 30 dias
- [ ] Banca aumentada para 1000€
- [ ] Performance mantida após aumento
- [ ] Drawdown < 10% pós-aumento

### 7.6 Mês 5: Escala e Otimização

**Objetivo:** Otimizar operação e preparar para expansão

**Semana 1-2: Otimização de Operação**
- Automatizar processos manuais
- Implementar reconciliação automática
- Otimizar filtros de liquidez
- Reduzir slippage

**Semana 3-4: Expansão de Mercados**
- Adicionar NBA Totals
- Backtest Totals
- Paper trading Totals (30 dias)
- Shadow mode Totals

**Semana 5-6: Preparação para Auto-Execução**
- Configurar API Betfair
- Implementar sistema de execução automática
- Testar em modo sandbox
- Preparar para ativação

**Entregáveis:**
- Operação otimizada
- NBA Totals adicionado
- API Betfair configurada
- Sistema de auto-execução testado

**Critérios de Sucesso:**
- [ ] Operação 80% automatizada
- [ ] NBA Totals validado
- [ ] API Betfair funcional
- [ ] Auto-execução testada

### 7.7 Mês 6: Auto-Execução e Lançamento Beta

**Objetivo:** Ativar auto-execução e lançar beta SaaS

**Semana 1-2: Ativação de Auto-Execução**
- Ativar execução automática (10% do volume)
- Monitorizar intensivamente
- Comparar auto vs manual
- Aumentar gradualmente para 100%

**Semana 3-4: Lançamento SaaS Beta**
- Criar landing page
- Configurar sistema de registo
- Convidar 10 beta users
- Coletar feedback

**Semana 5-6: Avaliação e Planeamento**
- Avaliar performance completa (6 meses)
- Calcular métricas globais
- Planear próximos 6 meses
- Decisão sobre escala para 5000€

**Entregáveis:**
- Auto-execução 100% operacional
- 10 beta users ativos
- 6 meses de track record
- Plano para próximos 6 meses

**Critérios de Sucesso:**
- [ ] Auto-execução 100% operacional
- [ ] Latência < 500ms
- [ ] 10 beta users registados
- [ ] ROI > 3% em 6 meses
- [ ] Track record validado

### 7.8 Resumo de Milestones

| Milestone | Data | Critério |
|-----------|------|----------|
| Infraestrutura pronta | Fim Mês 1 | Sistema operacional |
| Paper trading iniciado | Fim Mês 1 | 50+ sinais capturados |
| Paper trading validado | Fim Mês 2 | 100+ sinais, CLV validado |
| Micro banca iniciada | Fim Mês 3 | 50 apostas reais |
| Primeiro aumento | Fim Mês 4 | Banca 1000€ |
| Auto-execução testada | Fim Mês 5 | API funcional |
| Auto-execução ativa | Fim Mês 6 | 100% automático |
| Beta SaaS lançado | Fim Mês 6 | 10 users |

---

## 8. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[02_Business_Model/INDEX]] → Modelo de negócio que financia features
- [[24_Product_Roadmap/BACKLOG_DETALHADO]] → Backlog priorizado e estimado
- [[23_Scaling/INDEX]] → Estratégias de escala de produto
