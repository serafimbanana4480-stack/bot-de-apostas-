# VALIDAÇÃO CRUZADA E SIMULAÇÃO DE FLUXOS END-TO-END

**Data:** 2026-05-17
**Versão:** v4.0.1-FIXED
**Auditor:** System Architect AI
**Scope:** Validar consistência global após correções e simular fluxos end-to-end

---

## 1. VALIDAÇÃO CRUZADA DE DECISÕES

### 1.1 Consistência das Decisões Tomadas

| Decisão | Documentos Atualizados | Status de Consistência |
|---------|----------------------|------------------------|
| C-001: Frequência 2h | MASTER_PLAN (pendente), PLANO_DEFINITIVO (pendente), INTEGRATION_GUIDE (pendente) | ⚠️ PARCIAL - docker-compose corrigido, mas docs não atualizados |
| C-002: 80 features | MASTER_PLAN (já OK), PLANO_DEFINITIVO (pendente), INDEX.md (pendente) | ⚠️ PARCIAL - schema SQL consistente, mas docs não atualizados |
| C-003: 1 tier | INDEX.md (já OK), PLANO_FINANCEIRO (já OK), PLANO_DEFINITIVO (pendente) | ⚠️ PARCIAL - maioria consistente, PLANO_DEFINITIVO pendente |
| C-004: VPS 12€ | PLANO_FINANCEIRO (pendente), DEPLOYMENT_GUIDE (pendente), PLANO_DEFINITIVO (pendente) | ⚠️ PARCIAL - decisão tomada mas docs não atualizados |
| C-008: Betfair SP + Odds API | PLANO_FINANCEIRO (pendente), CLV_CLOSED_LINE_VALUE (pendente), INGESTAO_ODDS (pendente) | ⚠️ PARCIAL - decisão tomada mas docs não atualizados |
| C-006: Portas Prefect | docker-compose.yml (corrigido) | ✅ COMPLETO |
| C-007: Passwords defaults | docker-compose.yml (corrigido) | ✅ COMPLETO |
| C-011: MLflow service | docker-compose.yml (pendente - ainda não adicionado) | ❌ INCOMPLETO |

**Status Geral:** 50% das decisões implementadas, 50% pendente atualização de documentos

---

### 1.2 Consistência Entre Novos Documentos

| Documento Novo | Referências Cruzadas | Status |
|----------------|---------------------|--------|
| RESOLUCAO_INCONSISTENCIAS_CRITICAS.md | Refere MASTER_PLAN, PLANO_DEFINITIVO, etc. | ✅ OK |
| 25_SOPs/INDEX.md | Refere INDEX.md, Runbooks, Postmortems | ✅ OK |
| 26_Runbooks/INDEX.md | Refere INDEX.md, SOPs, Postmortems, Monitoring | ✅ OK |
| 28_Failure_Scenarios/INDEX.md | Refere INDEX.md, Runbooks, Postmortems, Security | ✅ OK |

**Status:** Novos documentos são consistentes entre si e com estrutura existente.

---

### 1.3 Validação de Dependências Entre Documentos

**Dependência Crítica:** SOPs → Runbooks → Failure Scenarios

- SOPs referem Runbooks para incidentes específicos ✅
- Runbooks referem Postmortems para análise pós-incidente ⚠️ (Postmortems não existe ainda)
- Failure Scenarios referem Runbooks para recovery ✅
- Failure Scenarios referem Security para prevenção ⚠️ (Security não existe ainda)

**Status:** Estrutura de dependências está correta, mas alguns documentos referenciados ainda não existem.

---

## 2. SIMULAÇÃO DE FLUXOS END-TO-END

### 2.1 Fluxo 1: Ingestão de Dados → Features → Modelo → Sinal

**Cenário:** Dia de jogo NBA, sistema operacional normal

**Passo 1: Ingestão de Dados (08:00)**
- [ ] Prefect flow "ingest_nba_data" é acionado automaticamente
- [ ] NBA API é chamada para obter jogos do dia
- [ ] Dados são inseridos em `bronze.raw_games`
- [ ] Pipeline ETL transforma para `silver.games_clean`
- [ ] Features são calculadas para `gold.features`

**Gaps Identificados:**
- ❌ Não está claro como Prefect flow é acionado (cron? manual?)
- ❌ Não está claro qual é o exato pipeline ETL (documento INGESTAO_ODDS existe mas não detalha passo-a-passo)
- ❌ Não está claro como features são calculadas (documento FEATURE_ENGINEERING_EXPANDED existe mas não detalha pipeline)

**Passo 2: Modelação (08:30)**
- [ ] Modelo XGBoost carregado do MLflow
- [ ] Features do dia são passadas ao modelo
- [ ] Probabilidades são geradas
- [ ] Calibração isotónica é aplicada
- [ ] Edge é calculado

**Gaps Identificados:**
- ❌ Não está claro quando o modelo é carregado (uma vez por dia? a cada batch?)
- ❌ Não está claro como calibração é aplicada (documento CALIBRACAO_ISOTONICA existe mas não integra com pipeline)
- ❌ Não está claro como edge é calculado (documento MOTOR_EDGE existe mas não especifica fórmula exata)

**Passo 3: Meta-Modelo (08:35)**
- [ ] Meta-modelo filtra previsões
- [ ] Se prob_meta > 0.60, sinal é aprovado
- [ ] Se prob_meta < 0.60, sinal é rejeitado

**Gaps Identificados:**
- ❌ Meta-modelo não está implementado no docker-compose.yml
- ❌ Não está claro como meta-modelo é integrado com pipeline
- ❌ Documento 46_Meta_Labeling/INDEX.md não existe

**Passo 4: Geração de Sinal (08:40)**
- [ ] Sinal aprovado é formatado
- [ ] Telegram Bot envia sinal para subscritores
- [ ] Sinal é registado em `gold.signals`

**Gaps Identificados:**
- ❌ Formato exato do sinal não está especificado (EXECUCAO_MANUAL tem exemplo mas não é definitivo)
- ❌ Não está claro como Telegram Bot envia para múltiplos subscritores (documento 19_Telegram_System/INDEX.md não existe)

**Conclusão do Fluxo 1:** ⚠️ Fluxo está conceitualmente correto mas tem gaps de implementação que impedem execução.

---

### 2.2 Fluxo 2: Execução de Aposta Manual

**Cenário:** Operador recebe sinal via Telegram e coloca aposta manualmente

**Passo 1: Receber Sinal**
- [ ] Telegram Bot envia sinal para operador
- [ ] Operador lê sinal (game, odd, edge, stake)

**Gaps Identificados:**
- ❌ Não está claro se operador é subscritor ou admin
- ❌ Não está claro como operador é autenticado

**Passo 2: Colocar Aposta**
- [ ] Operador abre Betfair
- [ ] Encontra jogo e mercado
- [ ] Coloca aposta com stake especificado
- [ ] Verifica que odd é ≥ odd mínima

**Gaps Identificados:**
- ❌ Não há checklist SOP para este processo
- ❌ Não está claro o que fazer se odd mudou antes de execução

**Passo 3: Confirmar Aposta**
- [ ] Operador confirma aposta no Telegram Bot
- [ ] Sistema regista aposta em `gold.bets`
- [ ] Sistema reconcilia aposta com sinal original

**Gaps Identificados:**
- ❌ Não está claro como operador confirma (comando? screenshot?)
- ❌ Reconciliação não está detalhada (documento RECONCILIACAO não existe)

**Conclusão do Fluxo 2:** ⚠️ Fluxo está conceitualmente correto mas falta detalhe operacional.

---

### 2.3 Fluxo 3: Circuit Breaker Ativado

**Cenário:** 5 perdas consecutivas, circuit breaker Beta ativado

**Passo 1: Detecção**
- [ ] Sistema detecta 5 perdas consecutivas
- [ ] Circuit breaker Beta é ativado automaticamente
- [ ] Alerta é enviado para Telegram + Email

**Gaps Identificados:**
- ❌ Não está claro onde esta lógica vive (API? Serviço separado?)
- ❌ Não está claro como "perda consecutiva" é definida (temporalmente?)

**Passo 2: Ação Automática**
- [ ] Sistema pausa novas apostas
- [ ] Operador é notificado
- [ ] Revisão manual é obrigatória

**Gaps Identificados:**
- ❌ Não está claro como pausa é implementada (flag na database? variável de ambiente?)
- ❌ Não está claro como revisão manual é documentada

**Passo 3: Recovery**
- [ ] Operador investiga causa
- [ ] Se causa identificada e corrigida, operador reativa sistema
- [ ] Se causa não identificada, sistema permanece em pausa

**Gaps Identificados:**
- ❌ Não está claro como operador reativa (comando? UI?)
- ❌ Não está claro o que fazer se causa não for identificada

**Conclusão do Fluxo 3:** ⚠️ Fluxo está conceitualmente correto mas falta implementação detalhada.

---

### 2.4 Fluxo 4: Backup e Restore

**Cenário:** VPS falha, need restore de backup

**Passo 1: Backup Automático**
- [ ] Script de backup roda diariamente às 3 AM
- [ ] PostgreSQL dump é criado
- [ ] Redis dump é criado
- [ ] Backups são comprimidos e enviados para S3 (opcional)

**Gaps Identificados:**
- ❌ Script de backup existe no DEPLOYMENT_GUIDE mas não está no repositório
- ❌ Não está claro se backup para S3 está implementado
- ❌ Não está claro como restore é testado

**Passo 2: Restore**
- [ ] VPS é re-provisionado
- [ ] Docker compose é iniciado
- [ ] Backup é restaurado
- [ ] Sistema é verificado

**Gaps Identificados:**
- ❌ Procedimento de restore está parcialmente documentado mas não testado
- ❌ Não está claro quanto tempo restore demora

**Conclusão do Fluxo 4:** ⚠️ Fluxo está parcialmente documentado mas não testado.

---

## 3. VALIDAÇÃO DE DEPENDÊNCIAS TÉCNICAS

### 3.1 Dependências de Docker Compose

**Serviços Atuais (9):**
1. PostgreSQL ✅
2. Redis ✅
3. API ✅
4. Prefect UI ✅
5. Prefect API ✅
6. MLflow ⚠️ (adicionado no plano mas não no docker-compose.yml)
7. Grafana ✅
8. Prometheus ✅
9. Node Exporter ✅

**Dependências:**
- API depende de PostgreSQL (healthy) ✅
- API depende de Redis (healthy) ✅
- Prefect UI depende de Prefect API (healthy) ✅
- Prefect API depende de PostgreSQL (healthy) ✅
- Grafana depende de Prometheus (started) ✅

**Gaps:**
- ❌ MLflow não está no docker-compose.yml (dependência para experiment tracking)
- ❌ Não há serviço de logging centralizado (Loki, ELK, etc.)
- ❌ Não há serviço de tracing (Jaeger, Zipkin, etc.)

---

### 3.2 Dependências de Documentos

**Documentos que Referenciam Outros que Não Existem:**

INDEX.md refere:
- ❌ 24_Product_Roadmap/INDEX.md
- ❌ 31_Data_Validation/INDEX.md
- ❌ 32_Feature_Store/INDEX.md
- ❌ 33_Alerting/INDEX.md
- ❌ 34_Security/INDEX.md
- ❌ 35_Financial_Tracking/INDEX.md
- ❌ 36_KPIs/INDEX.md
- ❌ 46_Meta_Labeling/INDEX.md
- ❌ 48_Data_Drift/INDEX.md
- ❌ 49_Continuous_Improvement/INDEX.md
- ❌ 50_Appendices/INDEX.md
- ❌ 99_Templates/INDEX.md
- ❌ GETTING_STARTED.md
- ❌ ONBOARDING_GUIDE.md

**Impacto:** Links quebrados, confusão para implementadores, sistema incompleto.

---

## 4. VALIDAÇÃO DE CONSISTÊNCIA NUMÉRICA

### 4.1 Consistência de Custos

| Item | PLANO_FINANCEIRO | DEPLOYMENT_GUIDE | Decisão Tomada | Status |
|------|------------------|-----------------|----------------|--------|
| VPS (4vCPU, 8GB) | 15€ | 50-60€ | 12€ (Hetzner CPX31) | ⚠️ 3 valores diferentes |
| Dados premium | 50€ (Mês 6) | Não mencionado | 8€/mês (Odds API) | ⚠️ Inconsistente |
| Total 6 meses | 400€ | Não especificado | ~448€ (com Odds API) | ⚠️ PLANO_FINANCEIRO não atualizado |

**Status:** Inconsistência não resolvida - PLANO_FINANCEIRO precisa ser atualizado.

---

### 4.2 Consistência de Features

| Documento | Número de Features | Status |
|-----------|-------------------|--------|
| Schema SQL | 80 | ✅ Fonte de verdade |
| PLANO_DEFINITIVO | 40-55 | ❌ Não atualizado |
| INDEX.md checklist | 40-50 | ❌ Não atualizado |
| FASE_1_CHECKLIST | 80 | ✅ Consistente |

**Status:** Parcialmente consistente - schema e checklist OK, mas PLANO_DEFINITIVO e INDEX.md não atualizados.

---

### 4.3 Consistência de Circuit Breakers

| Documento | Número de Breakers | Status |
|-----------|-------------------|--------|
| RISK_MANAGEMENT/INDEX.md | 6 (Alpha-Zeta) | ✅ |
| MASTER_PLAN_UNIFICADO.md | 5 (Alpha-Epsilon) | ❌ Falta Zeta |
| .env.example | 5 variáveis | ❌ Falta Zeta |

**Status:** Inconsistente - RISK_MANAGEMENT tem 6, mas outros docs têm 5.

---

## 5. ANÁLISE DE GAPS DE IMPLEMENTAÇÃO

### 5.1 Gaps Críticos (Block Execution)

1. **MLflow service ausente do docker-compose.yml** - Experiment tracking não funcional
2. **Meta-modelo não implementado** - Filtragem de falsos positivos não funcional
3. **Telegram System não documentado** - Distribuição de sinais não especificada
4. **Reconciliação não detalhada** - Verificação de execução vs sinal não funcional
5. **Sistema de alertas não implementado** - Notificação de incidentes não funcional

### 5.2 Gaps Importantes (Hinder Operation)

1. **15+ documentos referenciados não existem** - Links quebrados, sistema incompleto
2. **Sistema de logging ausente** - Debugging impossível
3. **Sistema de tracing ausente** - Distributed tracing impossível
4. **Secrets management ausente** - Segurança comprometida
5. **Autenticação/autorização não especificada** - API exposta sem proteção

### 5.3 Gaps Menores (Reduce Quality)

1. **Documentos não atualizados com decisões** - Inconsistência persiste
2. **Formato de sinal não padronizado** - Confusão para operadores
3. **Procedimentos de recovery não testados** - Risco de falha em incidente real

---

## 6. SCORE DE VALIDAÇÃO CRUZADA

| Métrica | Score | Notas |
|---------|-------|-------|
| **Consistência de decisões** | 50% | 4/8 decisões implementadas completamente |
| **Consistência de documentos** | 70% | Novos docs consistentes, mas docs antigos não atualizados |
| **Consistência numérica** | 60% | Alguns números ainda inconsistentes |
| **Validação de dependências** | 65% | Dependências conceituais OK, mas implementação incompleta |
| **Simulação de fluxos** | 55% | Fluxos conceitualmente corretos, mas gaps de implementação |
| **Gaps de implementação** | 40% | Muitos gaps críticos e importantes |

**SCORE GLOBAL DE VALIDAÇÃO CRUZADA:** **57/100**

---

## 7. RECOMENDAÇÕES DE VALIDAÇÃO CRUZADA

### 7.1 IMMEDIATE (Before Execution)

1. **Adicionar MLflow ao docker-compose.yml** - Experiment tracking é crítico
2. **Atualizar documentos com decisões** - PLANO_DEFINITIVO, INDEX.md, PLANO_FINANCEIRO
3. **Criar documentos ausentes prioritários** - Pelo menos Security, Alerting, Telegram System
4. **Implementar sistema de logging básico** - JSON logs no mínimo
5. **Implementar sistema de alertas básico** - Telegram alerts no mínimo

### 7.2 SHORT-TERM (Week 1-2)

1. **Criar 15+ documentos ausentes** - Eliminar links quebrados
2. **Implementar meta-modelo** - Filtragem de falsos positivos
3. **Implementar sistema de reconciliação** - Verificação de execução
4. **Implementar autenticação básica na API** - Security mínima
5. **Testar fluxos end-to-end** - Simulação completa

### 7.3 MEDIUM-Term (Month 1-2)

1. **Implementar sistema de tracing** - Distributed tracing
2. **Implementar secrets management** - HashiCorp Vault ou similar
3. **Testar procedimentos de recovery** - Backup/restore, disaster recovery
4. **Criar dashboards de operação** - Monitorização completa
5. **Documentar todos os fluxos em detalhe** - Eliminar ambiguidades

---

## 8. CONCLUSÃO

A validação cruzada revela que:

**✅ Pontos Fortes:**
- Estrutura de documentos é bem concebida
- Novos documentos (SOPs, Runbooks, Failure Scenarios) são consistentes
- Fluxos estão conceitualmente corretos
- Decisões tomadas são logicamente sound

**⚠️ Pontos Fracos:**
- Muitos documentos ainda não atualizados com decisões
- 15+ documentos referenciados não existem
- Gaps de implementação críticos (MLflow, meta-modelo, Telegram)
- Sistema de logging/tracing/alertas ausente

**❌ Bloqueadores de Execução:**
1. MLflow service ausente do docker-compose.yml
2. Meta-modelo não implementado
3. Telegram System não documentado
4. Sistema de alertas não implementado
5. 15+ documentos ausentes

**Recomendação:** Não começar implementação até que bloqueadores críticos sejam resolvidos. Projeto precisa de 2-3 semanas adicionais de trabalho focado em implementação de gaps críticos.

---

**Fim da Validação Cruzada**
