# INDEX V5 STREAMLINED — VBQ-UNIFIED

**Versão:** `5.0.0-STREAMLINED`  
**Data:** `2026-05-18`  
**Baseado em:** INDEX v4.0.2 + OBSIDIAN_CLEANUP_PLAN v1.0  
**Foco:** Apenas secções essenciais para implementação (30 ligações ativas, zero quebradas).

---

## PROPÓSITO

Este documento substitui o `INDEX.md` v4 como ponto de entrada rápido para a vault.  
**Regra:** Se uma secção não é necessária para implementar as Fases 1–6, não está aqui.

Secções arquivadas (SOPs, runbooks, legal, future expansion) permanecem na vault mas foram removidas deste índice ativo para reduzir ruído.

---

## MAPA RÁPIDO — 30 LIGAÇÕES

### A. ESTRATÉGIA E NEGÓCIO

| # | Ligação | Descrição |
|---|---------|-----------|
| 1 | [[MASTER_PLAN_UNIFICADO]] | Plano mestre definitivo (arquitetura, stack, schema SQL, roadmap 12 meses) |
| 2 | [[01_Vision_And_Strategy/PLANO_DEFINITIVO]] | Visão, stack tecnológica, funcionamento passo a passo (6 meses) |
| 3 | [[01_Vision_And_Strategy/INDEX]] | Filosofia, princípios inalteráveis, decisões irreversíveis |
| 4 | [[02_Business_Model/INDEX]] | Modelo tipster, pricing, CAC/LTV, plano financeiro |
| 5 | [[24_Product_Roadmap/INDEX]] | Backlog detalhado, priorização de funcionalidades, milestones |

### B. PESQUISA QUANTITATIVA E DADOS

| # | Ligação | Descrição |
|---|---------|-----------|
| 6 | [[03_Quant_Research/INDEX]] | CLV, probabilidades implícitas, overround, Brier/ECE, Monte Carlo |
| 7 | [[04_Data_Engineering/INDEX]] | Pipelines ETL, ingestão, deduplicação, schema evolution |
| 8 | [[31_Data_Validation/INDEX]] | Great Expectations, regras de qualidade, late arrivals |
| 9 | [[32_Feature_Store/INDEX]] | Feature store, versioning, lineage, serving |
| 10 | [[14_APIs/INDEX]] | NBA API, Betfair API, odds gratuitas, rate limits |

### C. MACHINE LEARNING E MODELOS

| # | Ligação | Descrição |
|---|---------|-----------|
| 11 | [[05_Machine_Learning/INDEX]] | XGBoost/LightGBM, ensemble stacking, calibração isotónica |
| 12 | [[46_Meta_Labeling/INDEX]] | Meta-modelo secundário, filtro de falsos positivos |
| 13 | [[29_Experiment_Tracking/INDEX]] | MLflow/Optuna, experimentos, reprodutibilidade |
| 14 | [[11_MLOps/INDEX]] | Retraining automático, drift, shadow deploys |

### D. VALIDAÇÃO E BACKTEST

| # | Ligação | Descrição |
|---|---------|-----------|
| 15 | [[06_Backtesting/INDEX]] | Walk-forward, purged CV, slippage, comissões, overfitting |
| 16 | [[21_Paper_Trading/INDEX]] | Paper trading, latência, métricas de simulação |
| 17 | [[47_Shadow_Betting/INDEX]] | Shadow mode multi-casa, medição de True CLV |

### E. EXECUÇÃO E RISCO

| # | Ligação | Descrição |
|---|---------|-----------|
| 18 | [[07_Value_Detection/INDEX]] | Motor de edge, thresholds de oportunidade, normalização de odds |
| 19 | [[08_Risk_Management/INDEX]] | Kelly fracionado, drawdown, circuit breakers, bankroll survival |
| 20 | [[09_Execution_System/INDEX]] | Execução manual, one-click, automática, reconciliação |
| 21 | [[44_Exchange_Execution/INDEX]] | Betfair API, ordens, slippage, otimização de latência |
| 22 | [[22_Real_Money_Operations/INDEX]] | Micro banca, tracking de apostas, reconciliação diária |
| 23 | [[42_Player_Props/INDEX]] | Player props NBA, modelo dedicado, liquidez (Fase 6) |

### F. INFRAESTRUTURA E DEVOPS

| # | Ligação | Descrição |
|---|---------|-----------|
| 24 | [[13_Infrastructure/INDEX]] | VPS, networking, custos, escalabilidade |
| 25 | [[12_DevOps/INDEX]] | CI/CD, Git workflow, deploy, rollback |
| 26 | [[15_Database/INDEX]] | PostgreSQL, schema, partitioning, backups, Redis |
| 27 | [[34_Security/INDEX]] | Secrets management, ACLs, audit logging, hardening |

### G. MONITORIZAÇÃO E ALERTING

| # | Ligação | Descrição |
|---|---------|-----------|
| 28 | [[10_Monitoring/INDEX]] | Prometheus, Grafana, dashboards técnicos, métricas de sistema |
| 29 | [[20_Dashboarding/INDEX]] | Dashboards executivos, operacionais e de negócio |
| 30 | [[33_Alerting/INDEX]] | Alertas Telegram, thresholds, playbooks de resposta, escalation |

### H. OPERAÇÕES E DISTRIBUIÇÃO

| # | Ligação | Descrição |
|---|---------|-----------|
| 31 | [[18_Operations/INDEX]] | Rotina diária, checklists operacionais, turnos |
| 32 | [[19_Telegram_System/INDEX]] | Bot de sinais, subscrições, templates de mensagem |
| 33 | [[35_Financial_Tracking/INDEX]] | PnL, impostos, reporting financeiro, gestão de banca |

### I. SUPORTE DOCUMENTAL

| # | Ligação | Descrição |
|---|---------|-----------|
| 34 | [[99_Templates/INDEX]] | Templates de notas, model cards, experimentos, incidentes |

---

## FLUXO DE TRABALHO POR FASE

```
FASE 1 — FUNDAÇÕES (Mês 1)
  → 13_Infrastructure → 15_Database → 14_APIs → 04_Data_Engineering
  → 03_Quant_Research → 31_Data_Validation → 32_Feature_Store

FASE 2 — MODELO (Mês 2)
  → 05_Machine_Learning → 46_Meta_Labeling → 29_Experiment_Tracking
  → 06_Backtesting → 21_Paper_Trading

FASE 3 — SHADOW & TIPSTER BETA (Mês 3)
  → 47_Shadow_Betting → 19_Telegram_System → 02_Business_Model
  → 24_Product_Roadmap

FASE 4 — DINHEIRO REAL (Mês 4)
  → 08_Risk_Management → 09_Execution_System → 22_Real_Money_Operations
  → 35_Financial_Tracking → 18_Operations

FASE 5 — ESTABILIZAÇÃO (Mês 5)
  → 10_Monitoring → 20_Dashboarding → 33_Alerting → 11_MLOps

FASE 6 — EXPANSÃO (Mês 6)
  → 42_Player_Props → 44_Exchange_Execution → 07_Value_Detection
```

---

## PRINCÍPIOS INALTERÁVEIS (Resumo)

1. **Lucro comprovado antes de escala** — ROI real > 3%, CLV > 2%, significância estatística.
2. **Um desporto, dois mercados** — NBA Moneyline + Spread até mês 6.
3. **Stack simples e barato** — Python 3.11+, PostgreSQL, Redis, XGBoost, FastAPI.
4. **Execução progressiva** — Manual → One-click → Automática (Betfair).
5. **Rigor estatístico desde o dia 1** — Purged CV, embargo periods, calibração por regime.
6. **Meta-labeling desde o início** — Modelo secundário filtra falsos positivos.
7. **Shadow mode multi-casa** — 3+ casas antes de dinheiro real.
8. **Nenhum segredo hardcoded** — Todas as credenciais em variáveis de ambiente.
9. **Documentação viva** — Alterações registadas no Obsidian antes do commit Git.

---

## LIGAÇÕES REMOVIDAS DESTE ÍNDICE (VER OBSIDIAN_CLEANUP_PLAN)

As seguintes secções foram arquivadas ou fundidas. Os ficheiros físicos permanecem na vault mas não fazem parte do índice ativo de implementação:

- `00_SETUP_ZERO` → arquivado (setup local, não planeamento)
- `10_Infrastructure` → fundir em `13_Infrastructure`
- `16_Compliance`, `17_Legal` → arquivados (operacionais)
- `23_Scaling` → arquivado (prematuro)
- `25_SOPs`, `26_Runbooks`, `27_Postmortems`, `28_Failure_Scenarios` → arquivados
- `30_Model_Registry` → integrado em `29_Experiment_Tracking` / `11_MLOps`
- `36_KPIs`, `37_CLV_Analytics` → arquivados (métricas já cobertas nos dashboards)
- `38_Betting_Psychology` → arquivado
- `39_Automation` → fundir em `04_Data_Engineering`
- `40_AI_Agents` → removido (especulativo)
- `41_Future_Expansion`, `43_Multi_Sport_Expansion` → arquivados
- `45_Bookmaker_Analysis` → arquivado
- `48_Data_Drift` → integrado em `11_MLOps`
- `49_Continuous_Improvement`, `50_Appendices` → arquivados

---

**ÚLTIMA ATUALIZAÇÃO:** `2026-05-18`  
**PRÓXIMA REVISÃO:** Após conclusão da Fase 1  
**PLANO DE LIMPEZA COMPLETO:** [[OBSIDIAN_CLEANUP_PLAN]]
