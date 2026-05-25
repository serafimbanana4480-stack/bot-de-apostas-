# TEAM_ROLES — Papéis da Equipa

**ID:** `ORG-001` | **Fase:** #phase/1 | **Owner:** Project Manager | **Status:** #status/active

---

## 1. OBJETIVO

Definir papéis, responsabilidades, competências e expectativas da equipa do projeto, garantindo clareza de funções e accountability para execução eficiente do sistema de value betting.

---

## 2. PAPEIS PRINCIPAIS

### 2.1 Principal Quant Engineer

**Responsável por:** Modelo ML, feature engineering, backtesting, pesquisa quantitativa

**Responsabilidades Diárias:**
- Monitorizar performance do modelo em produção
- Analisar métricas de drift e calibração
- Investigar anomalias em predições
- Revisar resultados de apostas do dia anterior

**Responsabilidades Semanais:**
- Executar backtests com novos dados
- Desenvolver e testar novas features
- Ajustar hiperparâmetros do modelo
- Documentar descobertas e insights

**Responsabilidades Mensais:**
- Avaliar necessidade de retraining
- Apresentar relatório de performance do modelo
- Planejar melhorias de modelo
- Revisar literatura académica relevante

**Competências Técnicas:**
- Python avançado (pandas, numpy, scikit-learn, xgboost)
- Estatística e probabilidade
- Machine learning (supervisionado, ensemble methods)
- Feature engineering temporal
- Backtesting com purged CV
- SQL para análise de dados

**Competências Soft Skills:**
- Pensamento analítico crítico
- Comunicação técnica clara
- Capacidade de explicar conceitos complexos
- Atenção aos detalhes
- Curiosidade intelectual

**KPIs:**
- ROI do modelo > 5%
- Sharpe ratio > 0.5
- CLV médio > 2%
- Zero incidentes de leakage em produção
- Tempo de resposta a anomalias < 4 horas

---

### 2.2 Risk Manager

**Responsável por:** Gestão de risco, limites de exposição, circuit breakers

**Responsabilidades Diárias:**
- Monitorizar drawdown atual
- Revisar exposição por desporto/liga
- Validar que limites de stake não foram excedidos
- Aprovar/rejeitar apostas de alto valor

**Responsabilidades Semanais:**
- Ajustar fração de Kelly baseado em performance
- Analisar padrões de risco
- Atualizar parâmetros de circuit breakers
- Revisar stop-loss triggers

**Responsabilidades Mensais:**
- Avaliar estratégia de gestão de risco
- Apresentar relatório de risco
- Simular cenários de stress
- Revisar e atualizar política de risco

**Competências Técnicas:**
- Gestão de portfólio
- Teoria de Kelly Criterion
- Análise de drawdown
- Gestão de exposição
- Probabilidade e estatística aplicada

**Competências Soft Skills:**
- Tomada de decisão sob pressão
- Prudência e conservadorismo
- Comunicação clara de riscos
- Visão sistémica
- Capacidade de dizer "não"

**KPIs:**
- Max drawdown < 20%
- Zero violações de limites críticos
- Tempo de resposta a alertas de risco < 1 hora
- Variabilidade de stake < 30% (evitar overbetting)
- Zero incidentes de ruína

---

### 2.3 Operations Engineer

**Responsável por:** Execução de apostas, infraestrutura, monitorização operacional

**Responsabilidades Diárias:**
- Monitorizar sistema de execução
- Verificar integridade de APIs (Betfair, Pinnacle)
- Reconciliar apostas com bookmakers
- Responder a alertas operacionais

**Responsabilidades Semanais:**
- Revisar logs de erros
- Otimizar performance de execução
- Atualizar configurações de APIs
- Testar contingências

**Responsabilidades Mensais:**
- Revisar SLA de APIs
- Planear upgrades de infraestrutura
- Documentar procedimentos operacionais
- Treinar em novas funcionalidades

**Competências Técnicas:**
- Python (API integration, async programming)
- REST APIs e webhooks
- Docker e containerization
- Linux administration
- Monitoring (Prometheus, Grafana)
- SQL para operações

**Competências Soft Skills:**
- Resolução de problemas sob pressão
- Atenção aos detalhes
- Comunicação clara de status
- Capacidade de trabalhar em turnos
- Resiliência

**KPIs:**
- Uptime do sistema > 99.5%
- Taxa de sucesso de execução > 95%
- Taxa de reconciliação > 98%
- Tempo médio de execução < 500ms
- Tempo de resposta a incidentes < 30 minutos

---

### 2.4 MLOps Engineer

**Responsável por:** MLOps, deployment, retraining automático, CI/CD

**Responsabilidades Diárias:**
- Monitorizar pipelines de ML
- Verificar saúde de modelos em produção
- Revisar logs de retraining
- Gerir versionamento de modelos

**Responsabilidades Semanais:**
- Executar retraining agendado
- Validar novos modelos antes de deployment
- Revisar métricas de drift
- Atualizar pipelines de CI/CD

**Responsabilidades Mensais:**
- Planejar arquitetura de MLOps
- Otimizar pipelines de treinamento
- Implementar novas features de MLOps
- Revisar custos de infraestrutura ML

**Competências Técnicas:**
- MLflow para experiment tracking
- Kubernetes (produção)
- CI/CD (GitHub Actions, GitLab CI)
- Docker e container orchestration
- Airflow/Prefect para workflows
- ML deployment strategies (canary, blue-green)

**Competências Soft Skills:**
- Visão de longo prazo
- Capacidade de automatizar
- Documentação técnica
- Colaboração cross-functional
- Melhoria contínua

**KPIs:**
- Tempo de deployment < 30 minutos
- Zero rollback em produção
- Taxa de sucesso de retraining > 95%
- Tempo de treinamento < 2 horas
- Zero incidentes de deployment

---

### 2.5 Data Engineer

**Responsável por:** Pipelines de dados, qualidade de dados, base de dados

**Responsabilidades Diárias:**
- Monitorizar pipelines de ETL
- Verificar qualidade de dados (Great Expectations)
- Revisar alertas de data quality
- Otimizar queries de BD

**Responsabilidades Semanais:**
- Adicionar novas fontes de dados
- Atualizar schemas de BD
- Revisar performance de queries
- Documentar lineage de dados

**Responsabilidades Mensais:**
- Planejar arquitetura de dados
- Otimizar storage e cost
- Implementar novas features de data quality
- Revisar backup e recovery

**Competências Técnicas:**
- PostgreSQL avançado (indexing, partitioning)
- ETL/ELT (Airflow, dbt, Prefect)
- Great Expectations ou similar
- Data modeling
- SQL otimizado
- Python para data processing

**Competências Soft Skills:**
- Rigor e precisão
- Capacidade de troubleshooting complexo
- Documentação clara
- Comunicação de trade-offs
- Foco em qualidade

**KPIs:**
- Data freshness < 15 minutos
- Data quality score > 99%
- Zero data loss em pipelines
- Query latency < 100ms (P95)
- Zero incidentes de BD

---

### 2.6 Project Manager (Opcional)

**Responsável por:** Coordenação de projeto, roadmap, stakeholder management

**Responsabilidades:**
- Gerir roadmap e backlog
- Coordenar entre equipas
- Reportar progresso
- Gerir riscos de projeto
- Facilitar comunicação

**Competências:**
- Agile/Scrum
- Gestão de projetos
- Comunicação
- Priorização
- Resolução de conflitos

---

## 3. MATRIZ DE RESPONSABILIDADES (RACI)

| Tarefa | Quant | Risk | Ops | MLOps | Data | PM |
|--------|-------|------|-----|-------|------|----|
| Desenvolver modelo | R | A | C | C | C | I |
| Definir limites de risco | A | R | C | I | I | I |
| Executar apostas | I | I | R | C | I | I |
| Retraining automático | A | I | C | R | C | I |
| Pipelines de dados | A | I | I | C | R | I |
| Backtesting | R | A | I | I | C | I |
| Reconciliação | I | I | R | I | A | I |
| Monitorização | I | A | R | R | C | I |
| CI/CD | C | I | C | R | C | I |
| Data quality | A | I | I | C | R | I |
| Gestão de projeto | I | I | I | I | I | R |

**Legenda:**
- **R (Responsible):** Executa a tarefa
- **A (Accountable):** Dono da decisão/responsável final
- **C (Consulted):** Consultado antes/durante
- **I (Informed):** Informado após conclusão

---

## 4. ONBOARDING E TREINO

### 4.1 Onboarding (Primeiras 2 semanas)

**Semana 1:**
- Dia 1: Visão geral do projeto, setup de ambiente
- Dia 2: Arquitetura do sistema, documentação
- Dia 3: Ferramentas e tecnologias (Git, Docker, etc.)
- Dia 4: Processos e workflows
- Dia 5: Shadowing com membro da equipa

**Semana 2:**
- Dia 1-2: Tarefas supervisionadas simples
- Dia 3-4: Tarefas independentes supervisionadas
- Dia 5: Review e feedback

### 4.2 Treino Contínuo

- **Weekly:** 1h de team sync
- **Monthly:** 1h de deep dive técnico
- **Quarterly:** 2h de offsite/planning
- **Annually:** Review de competências e desenvolvimento

---

## 5. COMUNICAÇÃO

### 5.1 Canais

- **Slack #general:** Comunicação assíncrona
- **Slack #incidents:** Alertas e incidentes
- **Slack #random:** Social e team building
- **Weekly Sync:** Reunião semanal (1h)
- **Daily Standup:** Opcional (15 min)

### 5.2 Protocolos de Comunicação

**Incidentes Críticos:**
- Slack #incidents imediato
- Call se urgente
- Documentar em Jira

**Decisões Técnicas:**
- Proposta em documento
- Discussão em team sync
- Aprovação por responsável
- Documentar decisão

**Progresso:**
- Atualizar Jira regularmente
- Reportar blockers imediatamente
- Compartilhar learnings

---

## 6. PERFORMANCE REVIEW

### 6.1 Avaliação Trimestral

**Critérios:**
- KPIs atingidos
- Qualidade do trabalho
- Colaboração
- Comunicação
- Iniciativa

**Resultados:**
- Excede expectativas
- Atende expectativas
- Precisa de melhoria
- Insuficiente

### 6.2 Desenvolvimento Profissional

**Oportunidades:**
- Conferências (ML, Quant Finance)
- Cursos online
- Certificações
- Livros e papers
- Projetos de R&D

---

## 7. ESCALONAMENTO

### 7.1 Necessidade de Contratação

**Indicadores:**
- Backlog crescente
- KPIs em risco
- Burnout da equipa
- Expansão de funcionalidades

**Perfis Prioritários:**
1. Quant Engineer (se volume de apostas aumentar)
2. Data Engineer (se novos dados/sources)
3. Operations Engineer (se 24/7 coverage necessário)

---

## 8. CULTURA E VALORES

### 8.1 Valores

- **Rigor:** Precisão em tudo
- **Transparência:** Comunicação honesta
- **Aprendizagem:** Melhoria contínua
- **Colaboração:** Trabalho em equipa
- **Responsabilidade:** Ownership das tarefas

### 8.2 Normas

- Documentar tudo
- Testar antes de deploy
- Revisar código (peer review)
- Comunicar problemas cedo
- Aprender com erros

---

## 9. LINKS CRUZADOS

- [[01_Vision_And_Strategy/INDEX]] ← Visão geral
- [[02_Business_Model/INDEX]] → Modelo de negócio
- [[SUPPORT_LEVELS]] → Níveis de suporte
- [[25_SOPs/INDEX]] → Procedimentos operacionais
