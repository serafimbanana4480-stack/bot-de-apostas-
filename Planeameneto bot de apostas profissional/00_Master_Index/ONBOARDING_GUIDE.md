# ONBOARDING_GUIDE — Guia para Novos Operadores

**ID:** `OB-001` | **Versão:** v4.0.1-FIXED | **Data:** 2026-05-17
**Público-Alvo:** Novos operadores, analistas, e membros da equipa

---

## 1. BEM-VINDO AO VBQ-UNIFIED

Este guia foi desenhado para ajudar novos operadores a familiarizarem-se com o sistema VBQ-UNIFIED. O objetivo é torná-lo produtivo em 1 semana, cobrindo todos os aspetos essenciais do sistema.

---

## 2. VISÃO GERAL DO SISTEMA

### 2.1 O Que É o VBQ-UNIFIED?

O VBQ-UNIFIED é um sistema quantitativo de value betting que:

- **Analisa dados NBA** (estatísticas de jogadores, equipas, jogos)
- **Treina modelos de ML** (XGBoost, LightGBM, CatBoost)
- **Calcula edge matemático** (vantagem sobre o mercado)
- **Gera sinais de apostas** (quando edge > 4%)
- **Distribui sinais** para subscritores via Telegram
- **Executa apostas** (manual → one-click → automática)

### 2.2 Pilares do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    PILAR 1: DADOS                            │
│  NBA API, Basketball-Reference, Odds, Features           │
├─────────────────────────────────────────────────────────────┤
│                    PILAR 2: MODELOS                           │
│  XGBoost + LightGBM + CatBoost → Ensemble → Meta-Modelo   │
├─────────────────────────────────────────────────────────────┤
│                    PILAR 3: VALIDAÇÃO                         │
│  Purged CV, Backtesting, SLippage, Comissões               │
├─────────────────────────────────────────────────────────────┤
│                    PILAR 4: RISCO                             │
│  Kelly Fracionado, Circuit Breakers, Drawdown Control      │
├─────────────────────────────────────────────────────────────┤
│                    PILAR 5: EXECUÇÃO                          │
│  Manual → One-Click → Automática, Reconciliação           │
├─────────────────────────────────────────────────────────────┤
│                    PILAR 6: MONITORIZAÇÃO                      │
│  Grafana, Prometheus, Alertas, Dashboards                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. ROTEIRO DE ONBOARDING (1 SEMANA)

### DIA 1: Visão Geral e Setup

**Manhã (3 horas):**
- [ ] Ler [[INDEX.md]] — Visão geral do sistema
- [ ] Ler [[01_Vision_And_Strategy/INDEX]] — Estratégia e princípios
- [ ] Ler [[02_Business_Model/INDEX]] — Modelo de negócio
- [ ] Ler [[GETTING_STARTED.md]] — Setup local do sistema
- [ ] Executar setup local (se aplicável)

**Tarde (3 horas):**
- [ ] Ler [[00_Master_Index/MASTER_PLAN_UNIFICADO.md]] — Plano mestre (secções 1-5)
- [ ] Ler [[04_Data_Engineering/INDEX]] — Pipeline de dados
- [ ] Ler [[05_Machine_Learning/INDEX]] — Modelos de ML
- [ ] Ler [[06_Backtesting/INDEX]] — Validação e backtest

**Objetivo do Dia 1:** Entender arquitetura global e setup básico.

---

### DIA 2: Operações Diárias

**Manhã (3 horas):**
- [ ] Ler [[18_Operations/INDEX]] — Operações do sistema
- [ ] Ler [[25_SOPs/INDEX]] — SOPs críticas
- [ ] Ler [[26_Runbooks/INDEX]] — Runbooks de incidentes
- [ ] Ler [[10_Monitoring/INDEX]] — Monitorização e alertas
- [ ] Acessar Grafana e explorar dashboards

**Tarde (3 horas):**
- [ ] Ler [[09_Execution_System/INDEX]] — Sistema de execução
- [ ] Ler [[08_Risk_Management/INDEX]] — Gestão de risco
- [ ] Ler [[07_Value_Detection/INDEX]] — Motor de edge
- [ ] Praticar SOP-001 (Abertura Diária) em ambiente de teste
- [ ] Praticar SOP-002 (Fecho Diário) em ambiente de teste

**Objetivo do Dia 2:** Entender operações diárias e monitorização.

---

### DIA 3: Dados e Modelos

**Manhã (3 horas):**
- [ ] Ler [[03_Quant_Research/INDEX]] — Pesquisa quantitativa
- [ ] Ler [[04_Data_Engineering/ESQUEMA_BASE_DADOS.md]] — Schema SQL
- [ ] Ler [[04_Data_Engineering/INGESTAO_ODDS.md]] — Ingestão de odds
- [ ] Ler [[05_Machine_Learning/XGBoost_BASELINE.md]] — Modelo baseline
- [ ] Ler [[46_Meta_Labeling/INDEX]] — Meta-modelo

**Tarde (3 horas):**
- [ ] Ler [[05_Machine_Learning/CALIBRACAO_ISOTONICA.md]] — Calibração
- [ ] Ler [[06_Backtesting/PURGED_CV.md]] — Purged CV
- [ ] Ler [[06_Backtesting/LEAKAGE_TEMPORAL.md]] — Leakage temporal
- [ ] Ler [[06_Backtesting/SLIPPAGE_COMISSOES.md]] — Slippage e comissões
- [ ] Explorar MLflow (http://localhost:5000)

**Objetivo do Dia 3:** Entender pipeline de dados e modelação.

---

### DIA 4: Execução e Risco

**Manhã (3 horas):**
- [ ] Ler [[09_Execution_System/EXECUCAO_MANUAL.md]] — Execução manual
- [ ] Ler [[09_Execution_System/RECONCILIACAO.md]] — Reconciliação
- [ ] Ler [[08_Risk_Management/KELLY_FRACIONADO.md]] — Kelly criterion
- [ ] Ler [[08_Risk_Management/CIRCUIT_BREAKERS.md]] — Circuit breakers
- [ ] Ler [[08_Risk_Management/DRAWDOWN_CONTROL.md]] — Drawdown control

**Tarde (3 horas):**
- [ ] Ler [[08_Risk_Management/EXPOSURE_LIMITS.md]] — Limites de exposição
- [ ] Ler [[08_Risk_Management/STOP_SYSTEMS.md]] — Stop systems
- [ ] Ler [[28_Failure_Scenarios/INDEX]] — Cenários de falha
- [ ] Praticar resposta a incidente (simulação)
- [ ] Praticar reconciliação de apostas (simulação)

**Objetivo do Dia 4:** Entender execução e gestão de risco.

---

### DIA 5: Telegram e Negócio

**Manhã (3 horas):**
- [ ] Ler [[19_Telegram_System/INDEX]] — Sistema Telegram
- [ ] Ler [[02_Business_Model/MODELO_TIPSTER.md]] — Modelo tipster
- [ ] Ler [[02_Business_Model/METRICAS_NEGOCIO.md]] — Métricas de negócio
- [ ] Ler [[02_Business_Model/PLANO_FINANCEIRO_6_MESES.md]] — Plano financeiro
- [ ] Testar Telegram Bot (comando /help, /status)

**Tarde (3 horas):**
- [ ] Ler [[16_Compliance/INDEX]] — Compliance e regulamentação
- [ ] Ler [[17_Legal/INDEX]] — Documentos legais
- [ ] Ler [[35_Financial_Tracking/INDEX]] — Tracking financeiro
- [ ] Ler [[36_KPIs/INDEX]] — KPIs do sistema
- [ ] Ler [[37_CLV_Analytics/INDEX]] — Análise de CLV

**Objetivo do Dia 5:** Entender Telegram, negócio, e compliance.

---

## 4. FERRAMENTAS E ACESSOS

### 4.1 URLs de Acesso

| Ferramenta | URL | Credenciais |
|------------|-----|-------------|
| Grafana | http://localhost:3000 | admin/admin (mudar no .env) |
| Prometheus | http://localhost:9090 | Nenhuma |
| MLflow | http://localhost:5000 | Nenhuma |
| Prefect UI | http://localhost:4200 | Nenhuma |
| API (local) | http://localhost:8000 | Nenhuma (health check público) |
| API (docs) | http://localhost:8000/docs | Nenhuma |

### 4.2 Comandos Úteis

```bash
# Verificar status de todos os serviços
docker compose ps

# Ver logs de um serviço específico
docker compose logs -f api

# Reiniciar um serviço
docker compose restart api

# Aceder ao PostgreSQL
docker compose exec postgres psql -U vb_admin -d valuebetting

# Aceder ao Redis
docker compose exec redis redis-cli -a ${REDIS_PASSWORD}

# Verificar uso de recursos
docker stats
```

---

## 5. RESPONSABILIDADES DO OPERADOR

### 5.1 Diárias

- [ ] Executar SOP-001 (Abertura Diária)
- [ ] Monitorizar dashboards Grafana
- [ ] Responder a alertas (se aplicável)
- [ ] Executar SOP-002 (Fecho Diário)

### 5.2 Semanais

- [ ] Verificar performance do modelo (CLV, ROI, Sharpe)
- [ ] Verificar drift de dados
- [ ] Revisar logs de segurança
- [ ] Participar em reunião de equipa (se aplicável)

### 5.3 Mensais

- [ ] Revisar plano financeiro
- [ ] Verificar métricas de negócio (MRR, churn)
- [ ] Atualizar documentação se necessário
- [ ] Sugerir melhorias ao sistema

---

## 6. MÉTRICAS DE SUCESSO DO ONBOARDING

### 6.1 Fim da Semana 1

Um operador é considerado onboarded com sucesso se:

- ✅ Consegue executar SOP-001 e SOP-002 sem assistência
- ✅ Consegue interpretar dashboards Grafana
- ✅ Consegue responder a incidentes básicos usando runbooks
- ✅ Consegue explicar arquitetura do sistema a terceiros
- ✅ Consegue identificar quando algo está "errado"

### 6.2 Fim do Mês 1

Um operador é considerado proficiente se:

- ✅ Consegue operar o sistema de forma autónoma
- ✅ Consegue sugerir melhorias aos processos
- ✅ Consegue treinar novos operadores
- ✅ Consegue participar em decisões estratégicas
- ✅ Consegue identificar oportunidades de otimização

---

## 7. RECURSOS DE APRENDIZAGEM

### 7.1 Documentação Essencial

- [[INDEX.md]] — Comece aqui
- [[MASTER_PLAN_UNIFICADO.md]] — Plano mestre completo
- [[GETTING_STARTED.md]] — Setup técnico
- [[25_SOPs/INDEX]] — Procedimentos operacionais
- [[26_Runbooks/INDEX]] — Resposta a incidentes

### 7.2 Documentação Avançada (Fase 2)

- [[05_Machine_Learning/INDEX]] — Deep dive em ML
- [[06_Backtesting/INDEX]] — Deep dive em backtest
- [[08_Risk_Management/INDEX]] — Deep dive em risco
- [[33_Alerting/INDEX]] — Sistema de alertas
- [[34_Security/INDEX]] — Segurança do sistema

### 7.3 Recursos Externos

- **XGBoost Documentation:** https://xgboost.readthedocs.io/
- **NBA API Documentation:** https://github.com/swar/nba_api
- **Betfair API Documentation:** https://developer.betfair.com/
- **Prometheus Documentation:** https://prometheus.io/docs/
- **Grafana Documentation:** https://grafana.com/docs/

---

## 8. SUPORTE E MENTORIA

### 8.1 Mentor

Cada novo operador é atribuído a um mentor durante o primeiro mês.

**Responsabilidades do Mentor:**
- Disponibilizar 2h/semana para dúvidas
- Revisar trabalho do operador
- Dar feedback construtivo
- Ajudar a resolver blockers

### 8.2 Canais de Comunicação

- **Slack/Discord:** #vbq-operators (canal de operadores)
- **Email:** ops@valuebetting.com (para dúvidas não urgentes)
- **Telegram:** @vbq_admins (para incidentes críticos)

### 8.3 Escalation

Se tiver um problema que não consegue resolver:

1. Consultar [[26_Runbooks/INDEX]]
2. Consultar seu mentor
3. Consultar [[28_Failure_Scenarios/INDEX]]
4. Contactar operations lead

---

## 9. CHECKLIST FINAL DE ONBOARDING

### 9.1 Conhecimento

- [ ] Consegue explicar arquitetura do sistema em 5 minutos
- [ ] Consegue explicar pipeline de dados end-to-end
- [ ] Consegue explicar como modelos geram previsões
- [ ] Consegue explicar como edge é calculado
- [ ] Consegue explicar sistema de gestão de risco

### 9.2 Operacional

- [ ] Consegue executar abertura diária sem assistência
- [ ] Consegue executar fecho diário sem assistência
- [ ] Consegue interpretar dashboards Grafana
- [ ] Consegue responder a alertas críticos
- [ ] Consegue usar runbooks para incidentes comuns

### 9.3 Técnico

- [ ] Consegue acessar todas as ferramentas (Grafana, Prometheus, MLflow)
- [ ] Consegue verificar logs de serviços
- [ ] Consegue reiniciar serviços se necessário
- [ ] Consegue executar queries SQL básicas
- [ ] Consegue entender erros comuns nos logs

### 9.4 Negócio

- [ ] Consegue explicar modelo de negócio
- [ ] Consegue interpretar métricas de negócio
- [ ] Consegue explicar compliance e requisitos legais
- [ ] Consegue identificar riscos de negócio
- [ ] Consegue sugerir melhorias ao produto

---

## 10. PRÓXIMOS PASSOS APÓS ONBOARDING

### 10.1 Fase 2 (Mês 2-3)

- Aprofundar conhecimento em ML e backtest
- Participar em decisões de melhoria do sistema
- Contribuir para documentação
- Treinar novos operadores

### 10.2 Fase 3 (Mês 4-6)

- Tornar-se especialista em uma área (ex: ML, Operações, Negócio)
- Liderar projetos de melhoria
- Participar em decisões estratégicas
- Contribuir para roadmap do produto

---

## 11. FEEDBACK

O onboarding é um processo contínuo. Por favor, dê feedback sobre:

- Clareza da documentação
- Adequação do roteiro de 1 semana
- Qualidade do suporte do mentor
- Ferramentas e acessos
- Sugestões de melhoria

Feedback pode ser enviado para: ops@valuebetting.com

---

**Fim do Onboarding Guide**
**Boa sorte e bem-vindo à equipa VBQ-UNIFIED!**
