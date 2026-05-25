# INDEX MESTRE — SISTEMA QUANTITATIVO DE VALUE BETTING

**ID do Sistema:** `VBQ-UNIFIED`  
**Versão:** `4.0.0-FINAL`  
**Data de Criação:** `2026-05-13`  
**Autor:** `Chief Systems Architect + Principal Quant Engineer`  
**Estado:** `PLANO DE EXECUÇÃO — PRONTO PARA IMPLEMENTAR`  
**Próxima Revisão:** `2026-06-13`  
**Documento Canónico:** [[MASTER_PLAN_UNIFICADO]] ← REFERÊNCIA DEFINITIVA  

---

## PROPÓSITO DESTE INDEX

Este documento é o **cérebro operacional** do projeto. Qualquer agente de IA, engenheiro, operador ou investidor deve começar aqui. Contém:

1. O mapa completo de todas as 50+ secções.
2. O roadmap de fases com critérios de entrada/saída.
3. Os princípios inalteráveis que governam todas as decisões.
4. Links diretos (backlinks) para cada subsistema.
5. O estado atual do projeto e blockers ativos.
6. Métricas de saúde do sistema.

**REGRA DE OURO:** Nunca modificar este ficheiro sem registo em [[LOG_ALTERACOES_INDEX]].

---

## 1. PRINCIPIOS INALTERAVEIS

Estes princípios têm prioridade absoluta sobre qualquer decisão técnica ou de negócio:

| # | Princípio | Implicação |
|---|-----------|------------|
| P1 | **Lucro comprovado antes de escala** | Nenhuma expansão de infraestrutura, mercado ou modelo sem ROI real > 3% e CLV > 2% com significância estatística. |
| P2 | **Um desporto, dois mercados** | NBA Moneyline + Spread são os únicos mercados até mês 6. Qualquer expansão requer backtest dedicado. |
| P3 | **Stack simples e barato** | Python 3.11+, PostgreSQL 15, Redis, XGBoost, FastAPI. Complexidade só quando o edge a sustenta. |
| P4 | **Execução progressiva** | Manual → One-click → Automática (Betfair). Nunca saltar etapas. |
| P5 | **Rigor estatístico desde o dia 1** | Purged CV, embargo periods, testes ADF/KPSS, multiple testing correction, calibração por regime. |
| P6 | **Meta-labeling desde o início** | Modelo secundário filtra falsos positivos do modelo primário. |
| P7 | **Tipster model desde a primeira aposta real** | Monetização paralela via subscrições Telegram desde o mês 4. |
| P8 | **Shadow mode multi-casa** | Simulação em 3+ casas antes de dinheiro real para medir True CLV. |
| P9 | **Nenhum segredo hardcoded** | Todas as credenciais em variáveis de ambiente. Nunca em repos. |
| P10 | **Documentação viva** | Cada alteração técnica ou de negócio regista-se no sistema Obsidian antes do commit Git. |

---

## 2. ROADMAP DE FASES — VISÃO GERAL (12 MESES)

```
FASE 1 — FUNDAÇÕES COM RIGOR CIENTÍFICO        [MÊS 1]  → Infra + Dados + Purged CV + 80 Features
FASE 2 — MODELO COM META-LABELING                [MÊS 2]  → Ensemble stacking + Calibração isotónica
FASE 3 — SHADOW MODE E TIPSTER BETA              [MÊS 3]  → Simulação 3 casas + Documentos legais
FASE 4 — MICRO BANCA E VALIDAÇÃO REAL            [MÊS 4]  → 500-1000€ Betfair + Tracking rigoroso
FASE 5 — ESTABILIZAÇÃO E LANÇAMENTO COMERCIAL    [MÊS 5]  → Automação relatórios + 50 subscritores
FASE 6 — EXPANSÃO E ONE-CLICK                    [MÊS 6]  → Player Props NBA + Deep links
FASE 7 — EXPANSÃO MULTI-DESPORTO                 [MÊS 7-9] → Football + UFC/MMA
FASE 8 — AUTOMAÇÃO E ESCALA                      [MÊS 10-12] → Execução automática + 200 subscritores
```

**Nota:** O plano completo com 12 meses, incluindo fases 7-8 (multi-desporto) e expansão institucional (fases 9-12, mês 13-24), está documentado em [[MASTER_PLAN_UNIFICADO]].

**Critério Crítico para Avançar de Fase:** TODOS os milestones da fase anterior devem estar COMPLETOS e VERIFICADOS. Nenhuma exceção.

---

## 3. MAPA DE SECÇÕES — NAVEGAÇÃO COMPLETA

### A. ESTRATÉGIA E NEGÓCIO
- [[MASTER_PLAN_UNIFICADO]] — **PLANO MESTRE DEFINITIVO** (substitui todos os anteriores)
- [[AUTOMACAO_PIPELINE_OPERACOES]] — Automação completa do pipeline de operações com Prefect
- [[FASE_1_IMPLEMENTATION_CHECKLIST]] — Checklist passo-a-passo para implementar Fase 1
- [[GETTING_STARTED]] — Guia de setup para novos desenvolvedores
- [[ONBOARDING_GUIDE]] — Procedimentos de onboarding da equipa
- [[01_Vision_And_Strategy/INDEX]] — Visão, filosofia, princípios de decisão
- [[01_Vision_And_Strategy/PLANO_DEFINITIVO]] — Plano híbrido de referência
- [[02_Business_Model/INDEX]] — Modelo de negócio, pricing, CAC, LTV, tipster tiers
- [[24_Product_Roadmap/INDEX]] — Roadmap de produto, features, priorização
- [[41_Future_Expansion/INDEX]] — Expansão futura, novos mercados, tecnologias *(Fase 7+)*

### B. PESQUISA QUANTITATIVA E DADOS
- [[03_Quant_Research/INDEX]] — Probabilidades implícitas, overround, CLV, Brier, ECE, Monte Carlo
- [[04_Data_Engineering/INDEX]] — Pipelines ETL, ingestão, deduplicação, schema evolution
- [[31_Data_Validation/INDEX]] — Validação de dados, observabilidade, late arrivals
- [[32_Feature_Store/INDEX]] — Feature store, versioning, lineage, serving
- [[48_Data_Drift/INDEX]] — Deteção de drift, análise de regime, adaptação

### C. MACHINE LEARNING E MODELOS
- [[05_Machine_Learning/INDEX]] — XGBoost, LightGBM, stacking, calibração, walk-forward
- [[46_Meta_Labeling/INDEX]] — Meta-labeling, modelo secundário, filtro de qualidade
- [[29_Experiment_Tracking/INDEX]] — MLflow/Optuna, experimentos, reprodutibilidade
- [[30_Model_Registry/INDEX]] — Registo de modelos, versioning, staging, rollback

### D. BACKTESTING E VALIDAÇÃO
- [[06_Backtesting/INDEX]] — Walk-forward, purged CV, slippage, comissões, overfitting
- [[47_Shadow_Betting/INDEX]] — Shadow mode, multi-casa, True CLV, simulação
- [[21_Paper_Trading/INDEX]] — Paper trading, operacionalidade, latência

### E. SISTEMA DE APOSTAS
- [[07_Value_Detection/INDEX]] — Motor de edge, thresholds, oportunidades
- [[08_Risk_Management/INDEX]] — Kelly, drawdown, circuit breakers, bankroll survival
- [[09_Execution_System/INDEX]] — Execução manual, one-click, automática, reconciliação
- [[22_Real_Money_Operations/INDEX]] — Operações com dinheiro real, micro banca
- [[42_Player_Props/INDEX]] — Player props NBA, modelo dedicado, validação *(Fase 6+)*
- [[43_Multi_Sport_Expansion/INDEX]] — NFL, Tennis, Esports *(Fase 7+)*
- [[44_Exchange_Execution/INDEX]] — Betfair API, ordens, slippage, latência
- [[45_Bookmaker_Analysis/INDEX]] — Análise de casas, odds, liquidez

### F. INFRAESTRUTURA E DEVOPS
- [[13_Infrastructure/INDEX]] — VPS, networking, custos, escalabilidade
- [[12_DevOps/INDEX]] — CI/CD, Git workflow, deploy, rollback
- [[11_MLOps/INDEX]] — Retraining, orchestration, feature drift, shadow deploys
- [[14_APIs/INDEX]] — APIs internas, NBA API, Betfair API, rate limits
- [[15_Database/INDEX]] — PostgreSQL, schema, partitioning, backups, Redis
- [[15_Database/BACKUP_RECOVERY]] — Estratégia de backup e recovery, DR plan
- [[34_Security/INDEX]] — Segurança, secrets, ACLs, audit logging

### G. MONITORIZAÇÃO E ALERTING
- [[10_Monitoring/INDEX]] — Prometheus, Grafana, dashboards, métricas
- [[20_Dashboarding/INDEX]] — Dashboards de negócio, operacionais, técnicos
- [[33_Alerting/INDEX]] — Alertas Telegram, thresholds, escalation
- [[36_KPIs/INDEX]] — KPIs de negócio, modelo, operação
- [[37_CLV_Analytics/INDEX]] — Análise de CLV por regime, decomposição de PnL

### H. GESTÃO E OPERACIONAL
- [[18_Operations/INDEX]] — Operações diárias, checklists, turnos
- [[25_SOPs/INDEX]] — Standard Operating Procedures, passo a passo
- [[26_Runbooks/INDEX]] — Runbooks para incidentes, debugging, recovery
- [[27_Postmortems/INDEX]] — Análise pós-incidente, lições aprendidas
- [[28_Failure_Scenarios/INDEX]] — Cenários de falha, mitigação, DR
- [[38_Betting_Psychology/INDEX]] — Psicologia, tilt, disciplina, emotional overrides
- [[39_Automation/INDEX]] — Automações, scripts, cron, Prefect
- [[40_AI_Agents/INDEX]] — Agentes de IA, assistentes, auto-análise

### I. COMPLIANCE E LEGAL
- [[16_Compliance/INDEX]] — Compliance, regulamentação, SRIJ, audit
- [[17_Legal/INDEX]] — Documentos legais, termos, disclaimers, jurisdição

### J. SISTEMAS ESPECÍFICOS
- [[19_Telegram_System/INDEX]] — Bot Telegram, subscrições, envio de sinais
- [[35_Financial_Tracking/INDEX]] — Tracking financeiro, PnL, impostos, reporting

### K. MELHORIA CONTÍNUA
- [[49_Continuous_Improvement/INDEX]] — Processos de melhoria, revisões, benchmarks
- [[50_Appendices/INDEX]] — Glossário, referências, recursos externos
- [[99_Templates/INDEX]] — Templates de notas, model cards, experimentos

---

## 4. ESTADO ATUAL DO PROJETO

```
FASE ATUAL: FASE 1 — FUNDAÇÕES COM RIGOR CIENTÍFICO
STATUS: EM PREPARAÇÃO
PLANO REFERÊNCIA: MASTER_PLAN_UNIFICADO v4.0.0-FINAL
BLOCKERS ATIVOS: Nenhum
```

### 4.1 Checklist de Fase 1 (Mês 1)

- [ ] Semana 1-2: Infraestrutura base (VPS, PostgreSQL, Redis, Git)
- [ ] Semana 1-2: Ingestão de dados históricos NBA (5 épocas)
- [ ] Semana 1-2: Implementar Purged Walk-Forward CV com embargo de 2 dias
- [ ] Semana 1-2: Testes ADF e KPSS em features candidatas
- [x] Semana 3-4: Pipeline de feature engineering (80 features: 15 forma + 12 mercado + 18 contexto + 20 jogadores + 15 interacoes)
- [ ] Semana 3-4: Módulo A: Forma recente com half-life decay
- [ ] Semana 3-4: Módulo B: Features de mercado
- [ ] Semana 3-4: Módulo C: Features de contexto e calendário
- [ ] Semana 3-4: Módulo D: Features de interação
- [ ] Semana 3-4: Normalização de odds e remoção de overround

### 4.2 Métricas de Saúde do Projeto

| Métrica | Target Atual | Valor Real | Estado |
|---------|--------------|------------|--------|
| Dados históricos disponíveis | 5 épocas NBA | 0 | 🔴 |
| Pipeline de features funcional | Sim | Não | 🔴 |
| Purged CV implementado | Sim | Não | 🔴 |
| Testes ADF/KPSS passando | 100% features | 0% | 🔴 |
| Primeiro modelo treinado | Fim Mês 2 | N/A | ⏳ |

---

## 5. SISTEMA DE NAMING E CONVENÇÕES

### 5.1 IDs Únicos
Cada nota, decisão arquitetural, SOP e runbook tem um ID único:

- `DEC-XXX` — Decisões arquiteturais (e.g., `DEC-001: Escolha de XGBoost sobre LightGBM como baseline`)
- `SOP-XXX` — Standard Operating Procedures
- `RB-XXX` — Runbooks
- `EXP-XXX` — Experimentos
- `MOD-XXX` — Modelos registados
- `FEA-XXX` — Features
- `RIS-XXX` — Riscos identificados
- `INC-XXX` — Incidentes

### 5.2 Tags Obrigatórias

```
#status/active #status/pending #status/blocked #status/completed
#priority/critical #priority/high #priority/medium #priority/low
#type/decision #type/sop #type/runbook #type/experiment #type/incident
#phase/1 #phase/2 #phase/3 #phase/4 #phase/5 #phase/6
#area/quant #area/ml #area/data #area/risk #area/exec #area/ops
#owner/eng #owner/quant #owner/ops #owner/legal
```

### 5.3 Formato de Backlinks

Sempre usar backlinks wikilink para conectar notas:
- `\[\[NOME_DA_NOTA\]\]` — link direto
- `\[\[NOME_DA_NOTA|texto alternativo\]\]` — link com texto alternativo

---

## 6. WORKFLOWS OPERACIONAIS CHAVE

### 6.1 Adicionar uma Nova Feature
1. Criar nota em [[32_Feature_Store/INDEX]] com ID `FEA-XXX`
2. Documentar: o que faz, porque existe, testes ADF/KPSS, regime de aplicação
3. Adicionar ao pipeline de treino
4. Correr purged CV com e sem a feature
5. Medir delta de CLV e Brier Score
6. Se delta > 0.1% e estatisticamente significativo (p < 0.05), aprovar
7. Registar decisão em [[32_Feature_Store/INDEX]]

### 6.2 Treinar um Novo Modelo
1. Criar experimento em [[29_Experiment_Tracking/INDEX]] com ID `EXP-XXX`
2. Documentar: hipótese, features, hiperparâmetros, janelas de CV
3. Correr purged walk-forward CV
4. Gerar reliability diagrams e ECE por regime
5. Comparar com modelo atual em produção (shadow mode)
6. Se supera em CLV e Sharpe com significância, promover a staging
7. Revisão obrigatória em [[30_Model_Registry/INDEX]] antes de produção

### 6.3 Responder a um Incidente
1. Abrir nota em [[27_Postmortems/INDEX]] com ID `INC-XXX`
2. Seguir [[26_Runbooks/INDEX]] de resposta a incidentes
3. Mitigar imediatamente (circuit breaker se necessário)
4. Coletar logs e métricas
5. Analisar root cause
6. Implementar fix
7. Validar em shadow mode
8. Fechar incidente com lições aprendidas

---

## 7. CONTACTOS E RESPONSABILIDADES

| Função | Responsabilidade | Backups |
|--------|------------------|---------|
| Chief Quant Engineer | Rigor estatístico, modelos, backtests | [[03_Quant_Research/INDEX]] |
| Lead Data Engineer | Pipelines, feature store, qualidade | [[04_Data_Engineering/INDEX]] |
| MLOps Engineer | Treino, deploy, monitorização, drift | [[11_MLOps/INDEX]] |
| Risk Manager | Sizing, circuit breakers, drawdown | [[08_Risk_Management/INDEX]] |
| Operations Lead | Execução diária, SOPs, alertas | [[18_Operations/INDEX]] |
| Compliance Officer | Legal, disclaimers, regulamentação | [[16_Compliance/INDEX]] |

---

## 8. CHANGE LOG DO INDEX

| Data | Versão | Alteração | Autor |
|------|--------|-----------|-------|
| 2026-05-13 | 4.0.0-FINAL | Unificacao de todos os planos anteriores | Chief Systems Architect |
| 2026-05-15 | 4.0.1-FIX | Correcao de inconsistencias (versões, custos, tiers, frequencia) | Cascade AI |
| 2026-05-17 | 4.0.2-AUDIT | Auditoria sistémica completa + criação de 11 documentos críticos (Alerting, Security, Meta-Labeling, Telegram, Data Validation, Feature Store, Financial Tracking, KPIs, Getting Started, Onboarding) + correção docker-compose.yml (MLflow) | Devin AI |

---

**ÚLTIMA ATUALIZAÇÃO:** `2026-05-17 16:26 UTC`  
**PRÓXIMA REVISÃO AGENDADA:** `2026-05-24`  
**LINK PARA DASHBOARD DE SAÚDE:** [[10_Monitoring/INDEX]]
