# IMPLEMENTACAO_DRIFT — Pipeline de Detecção Automática

**ID:** `DRIFT-008` | **Fase:** #phase/6 | **Owner:** Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Descrever a implementação do pipeline de deteção de drift, incluindo arquitetura, componentes, fluxo de dados e integração com o sistema de value betting.

---

## 2. ARQUITETURA DO PIPELINE

### 2.1 Visão Geral

O pipeline de deteção de drift é composto por quatro componentes principais:

1. **Data Extraction Layer:** Coleta dados de referência e atuais
2. **Drift Detection Engine:** Calcula métricas de drift
3. **Alert Engine:** Gera e envia notificações
4. **Storage Layer:** Guarda resultados históricos

### 2.2 Fluxo de Dados

```
Fontes de Dados (Bookmakers, APIs)
    ↓
Data Warehouse / Data Lake
    ↓
Data Extraction Layer (Scheduled)
    ↓
┌─────────────────────────────────────┐
│  Dados de Referência (Baseline)     │
│  - Dados de treino do modelo        │
│  - Período: últimos 3-6 meses       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Dados Atuais (Production)          │
│  - Última semana/mês                │
│  - Janela deslizante                │
└─────────────────────────────────────┘
    ↓
Drift Detection Engine
    ↓
┌─────────────────────────────────────┐
│  Cálculo de Métricas:               │
│  - PSI (Population Stability Index) │
│  - KS Test (Kolmogorov-Smirnov)    │
│  - Estatísticas descritivas         │
│  - Performance metrics              │
└─────────────────────────────────────┘
    ↓
Comparação com Thresholds
    ↓
Alert Engine
    ↓
┌─────────────────────────────────────┐
│  Canais de Notificação:             │
│  - Telegram                         │
│  - Email                            │
│  - Slack (opcional)                 │
│  - SMS (apenas CRITICAL)            │
└─────────────────────────────────────┘
    ↓
Storage Layer (Histórico)
    ↓
Dashboard / Visualização
```

---

## 3. COMPONENTES DO PIPELINE

### 3.1 Data Extraction Layer

**Responsabilidade:** Coletar dados de referência e atuais para comparação.

**Fontes de dados:**
- Data Warehouse (dados históricos)
- Data Lake (dados brutos)
- APIs de bookmakers (dados em tempo real)
- Sistema de predições (predictions em produção)

**Parâmetros de configuração:**
- Período de referência (ex: últimos 6 meses)
- Período atual (ex: última semana)
- Frequência de extração (diária, semanal)
- Features a monitorizar (top 10 por importância)

**Validações:**
- Verificar se dados de referência existem
- Verificar se dados atuais são suficientes (min 100 obs)
- Verificar qualidade dos dados (missing values, outliers)
- Verificar consistência de schema

### 3.2 Drift Detection Engine

**Responsabilidade:** Calcular métricas de drift e comparar com thresholds.

**Métricas calculadas:**

**Para Feature Drift:**
- PSI para cada feature
- KS test para cada feature contínua
- Chi-square test para features categóricas
- Estatísticas descritivas (média, mediana, std)

**Para Prediction Drift:**
- PSI das probabilidades preditas
- KS test das distribuições de probs
- Brier Score (calibração)
- Expected Calibration Error (ECE)

**Para Target Drift:**
- Proporção de classes
- Chi-square test
- Taxa de vitória média
- PSI de outcomes (se contínuos)

**Para Concept Drift:**
- Performance degradation (accuracy, AUC, EV)
- Feature importance drift
- Residual analysis
- Adversarial validation

**Thresholds configuráveis:**
- PSI thresholds por feature
- Performance thresholds
- Níveis de severidade (INFO, WARNING, HIGH, CRITICAL)

### 3.3 Alert Engine

**Responsabilidade:** Gerar e enviar notificações quando drift é detetado.

**Funcionalidades:**
- Agregação de alertas (evitar spam)
- Deduplicação de alertas
- Escalamento baseado em severidade
- Formatação de mensagens
- Integração múltipla (Telegram, Email, etc.)

**Lógica de envio:**
- Alertas INFO: logging apenas (resumos diários)
- Alertas WARNING: notificação imediata
- Alertas HIGH: notificação imediata + preparação de retraining
- Alertas CRITICAL: notificação imediata + pausa de operações

### 3.4 Storage Layer

**Responsabilidade:** Guardar resultados históricos para análise e tendências.

**Dados armazenados:**
- Métricas de drift calculadas
- Alertas enviados
- Timestamps de verificação
- Configurações usadas
- Ações tomadas

**Armazenamento:**
- Base de dados relacional (PostgreSQL, MySQL)
- Time series database (InfluxDB, TimescaleDB)
- Object storage (S3) para dados brutos

**Retenção:**
- Métricas agregadas: 2 anos
- Alertas: 1 ano
- Dados brutos: 6 meses

---

## 4. AGENDAMENTO E FREQUÊNCIA

### 4.1 Frequência de Verificação

| Tipo de Verificação | Frequência | Justificação |
|---------------------|------------|--------------|
| Feature drift (odds) | Diária | Odds mudam rapidamente |
| Feature drift (estatísticas) | Semanal | Mudam mais lentamente |
| Prediction drift | Diária | Detetar mudanças rápidas |
| Target drift | Semanal | Requer outcomes |
| Concept drift | Semanal | Computationally expensive |
| Performance metrics | Diária | EV pode ser estimado |

### 4.2 Horários de Execução

**Verificações diárias:**
- Horário: 02:00 UTC (fora de pico de apostas)
- Janela de dados: últimas 24h
- Tempo de execução estimado: 5-15min

**Verificações semanais:**
- Horário: Domingo 02:00 UTC
- Janela de dados: última semana
- Tempo de execução estimado: 15-30min

**Verificações mensais:**
- Horário: 1º do mês 03:00 UTC
- Janela de dados: último mês
- Tempo de execução estimado: 30-60min

### 4.3 Configuração de Scheduler

Usar sistema de agendamento robusto:
- **Airflow:** Para pipelines complexos com dependências
- **Cron:** Para tarefas simples e independentes
- **Kubernetes CronJobs:** Para ambientes containerizados
- **AWS EventBridge / CloudWatch:** Para ambientes AWS

**Configuração de exemplo (Cron):**
```
# Verificação diária de feature drift
0 2 * * * /opt/vb/scripts/check_feature_drift.sh >> /var/log/drift/daily.log 2>&1

# Verificação diária de prediction drift
0 2 * * * /opt/vb/scripts/check_prediction_drift.sh >> /var/log/drift/daily.log 2>&1

# Verificação semanal de target drift
0 2 * * 0 /opt/vb/scripts/check_target_drift.sh >> /var/log/drift/weekly.log 2>&1

# Verificação semanal de concept drift
0 3 * * 0 /opt/vb/scripts/check_concept_drift.sh >> /var/log/drift/weekly.log 2>&1
```

---

## 5. INTEGRAÇÃO COM SISTEMA EXISTENTE

### 5.1 Integração com Data Warehouse

**Conexão:**
- Usar connection pool para eficiência
- Queries otimizadas com índices
- Cache de resultados frequentes

**Queries de exemplo:**
```sql
-- Dados de referência (últimos 6 meses)
SELECT * FROM betting_features
WHERE game_date >= CURRENT_DATE - INTERVAL '6 months'
AND model_version = 'latest';

-- Dados atuais (última semana)
SELECT * FROM betting_features
WHERE game_date >= CURRENT_DATE - INTERVAL '7 days';
```

### 5.2 Integração com Sistema de Predições

**Coleta de predições:**
- API endpoint para obter predições recentes
- Logging de todas as predições em produção
- Armazenamento de predições com timestamps

**Coleta de outcomes:**
- Sistema de scraping de resultados
- Validação de outcomes (regras de aposta)
- Matching de predições com outcomes

### 5.3 Integração com Sistema de Apostas

**Pausa automática:**
- Quando drift CRITICAL detetado
- API call para pausar sistema
- Notificação aos stakeholders

**Retoma automática:**
- Após correção validada
- Aprovação manual obrigatória
- Monitorização intensiva por 48h

---

## 6. MONITORIZAÇÃO DO PIPELINE

### 6.1 Métricas de Saúde do Pipeline

Monitorizar a saúde do próprio pipeline de drift:

- **Latência:** Tempo entre agendamento e conclusão
- **Sucesso rate:** % de execuções bem-sucedidas
- **Data freshness:** Idade dos dados usados
- **Alert delivery rate:** % de alertas entregues

### 6.2 Alertas do Pipeline

O pipeline deve ter seus próprios alertas:

- Execução falha por 3 dias consecutivos
- Latência > 30min
- Dados de referência não disponíveis
- Taxa de sucesso < 95%
- Alert delivery rate < 90%

### 6.3 Logs e Debugging

**Níveis de log:**
- INFO: Execução normal, métricas calculadas
- WARNING: Drift detetado, thresholds excedidos
- ERROR: Falha na execução
- DEBUG: Informação detalhada para troubleshooting

**Armazenamento de logs:**
- Centralizado (ELK Stack, CloudWatch)
- Retenção: 30 dias
- Indexação por timestamp e severidade

---

## 7. DEPLOYMENT E CI/CD

### 7.1 Versionamento

- Todo o código versionado em Git
- Tags para releases
- Branch strategy: main (produção), develop (dev), feature/*

### 7.2 CI/CD Pipeline

**Estágios:**
1. **Lint:** Verificar qualidade de código
2. **Testes unitários:** Validar funções individuais
3. **Testes de integração:** Validar pipeline completo
4. **Build:** Criar Docker image
5. **Deploy to staging:** Deploy em ambiente de staging
6. **E2E tests:** Testes end-to-end em staging
7. **Deploy to production:** Deploy em produção (canary)

### 7.3 Rollback

Procedimento de rollback:
- Manter últimas 3 versões em produção
- Rollback automático se alertas CRITICAL em 1h
- Rollback manual via CI/CD pipeline
- Notificação da equipa após rollback

---

## 8. SEGURANÇA

### 8.1 Controlo de Acesso

- Autenticação obrigatória para acessar configurações
- Role-based access control (RBAC)
- Audit logging de todas as mudanças
- Segregação de ambientes (dev, staging, prod)

### 8.2 Segurança de Dados

- Dados sensíveis encriptados em repouso
- Conexões encriptadas (TLS)
- Secrets geridos por secret manager (Vault, AWS Secrets Manager)
- Anonymização de dados pessoais (GDPR)

### 8.3 Segurança de Alertas

- Rate limiting para evitar spam
- Validação de recipients
- Autenticação de webhooks
- Verificação de integridade de mensagens

---

## 9. PERFORMANCE E OTIMIZAÇÃO

### 9.1 Otimizações

**Caching:**
- Cache de dados de referência (atualizar semanalmente)
- Cache de resultados de cálculos frequentes
- Cache de configurações

**Paralelização:**
- Cálculo de PSI em paralelo para múltiplas features
- Paralelização de queries de banco de dados
- Distribuição de carga em múltiplos workers

**Batching:**
- Processamento em batch para grandes volumes
- Chunking de dados para evitar memory issues
- Streaming para datasets muito grandes

### 9.2 Escalabilidade

**Horizontal scaling:**
- Deploy em Kubernetes para auto-scaling
- Fila de tarefas para distribuição de carga
- Load balancing para múltiplas instâncias

**Vertical scaling:**
- Aumentar recursos de CPU/RAM conforme necessário
- Otimizar queries de banco de dados
- Usar índices apropriados

---

## 10. PLANO DE IMPLEMENTAÇÃO

### 10.1 Fase 1: MVP (4 semanas)

- [ ] Implementar deteção de feature drift (PSI)
- [ ] Implementar alertas via Telegram
- [ ] Configurar scheduler diário
- [ ] Criar dashboard básico
- [ ] Documentar processo

### 10.2 Fase 2: Expansão (6 semanas)

- [ ] Adicionar deteção de prediction drift
- [ ] Adicionar deteção de target drift
- [ ] Implementar alertas via Email
- [ ] Adicionar histórico de métricas
- [ ] Criar playbooks de resposta

### 10.3 Fase 3: Maturidade (8 semanas)

- [ ] Adicionar deteção de concept drift
- [ ] Implementar auto-retraining
- [ ] Adicionar shadow mode
- [ ] Implementar canary deployment
- [ ] Criar sistema de análise de causas

---

## 11. LINKS CRUZADOS

- [[48_Data_Drift/INDEX]] ← Secção mãe
- [[48_Data_Drift/DETECAO_FEATURE_DRIFT]] → Detecção de feature drift
- [[48_Data_Drift/DETECAO_PREDICTION_DRIFT]] → Detecção de prediction drift
- [[48_Data_Drift/DETECAO_TARGET_DRIFT]] → Detecção de target drift
- [[48_Data_Drift/DETECAO_CONCEPT_DRIFT]] → Detecção de concept drift
- [[48_Data_Drift/ALERTAS_DRIFT]] → Sistema de alertas
- [[48_Data_Drift/ANALISE_CAUSAS_DRIFT]] → Análise de causas
- [[48_Data_Drift/MITIGACAO_DRIFT]] → Mitigação de drift
- [[11_MLOps/INDEX]] → Operações de MLOps
