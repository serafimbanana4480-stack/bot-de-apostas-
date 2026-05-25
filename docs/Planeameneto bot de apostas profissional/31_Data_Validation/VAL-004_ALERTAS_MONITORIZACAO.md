# VAL-004 — Alertas e Monitorização de Qualidade de Dados

**ID:** `VAL-004` | **Fase:** #phase/10 | **Owner:** Data Engineer | **Status:** #status/in_progress

---

## 1. OBJETIVO

Definir estratégias e procedimentos para monitorizar a qualidade dos dados em tempo real e gerar alertas automáticos quando forem detetados problemas. A monitorização proativa permite identificar e corrigir problemas antes que causem perdas financeiras ou decisões incorretas de betting.

---

## 2. CONTEXTO

A qualidade dos dados degrada-se naturalmente ao longo do tempo devido a:
- Mudanças nas APIs externas (NBA, Betfair)
- Erros temporários de ingestão
- Drift de distribuição dos dados
- Mudanças no formato dos dados
- Problemas de infraestrutura

Sem monitorização adequada, problemas podem passar despercebidos por dias ou semanas, causando perdas significativas.

---

## 3. ESCOPO

Este documento abrange:
- **Monitorização em tempo real**: Alertas imediatos para problemas críticos
- **Monitorização de tendências**: Detecção de degradação gradual
- **Monitorização de batch**: Validação de batches completos de dados
- **Alertas multi-canal**: Notificações via Telegram, Slack, email
- **Dashboarding**: Visualização de métricas de qualidade

---

## 4. HIERARQUIA DE ALERTAS

### 4.1. Níveis de Severidade

**CRITICAL (P0):**
- Impacto imediato no sistema de betting
- Requer ação imediata (dentro de 5 minutos)
- Ex: Pipeline parado, dados completamente corruptos
- Notificação: Todos os canais (Telegram + Slack + Email + SMS)

**HIGH (P1):**
- Impacto significativo mas não imediato
- Requer ação urgente (dentro de 30 minutos)
- Ex: Taxa de erro > 10%, drift significativo
- Notificação: Telegram + Slack + Email

**MEDIUM (P2):**
- Impacto moderado
- Requer ação dentro de 2 horas
- Ex: Taxa de erro > 5%, drift leve
- Notificação: Telegram + Slack

**LOW (P3):**
- Impacto menor
- Pode ser investigado no próximo dia útil
- Ex: Taxa de erro > 2%, warnings
- Notificação: Slack apenas

**INFO (P4):**
- Informacional
- Não requer ação imediata
- Ex: Relatórios diários, métricas normais
- Notificação: Dashboard apenas

### 4.2. Critérios de Escalonamento

**Escalonamento automático:**
- Se alerta P1 não resolvido em 30 minutos → escalar para P0
- Se alerta P2 não resolvido em 2 horas → escalar para P1
- Se alerto recorrente 3 vezes em 1 hora → escalar para nível superior

**Escalonamento manual:**
- On-call engineer pode escalar se necessário
- Documentar razão do escalonamento
- Notificar próximo nível na hierarquia

---

## 5. ALERTAS PARA DADOS BRUTOS

### 5.1. Alertas de Ingestão

**Falha de ingestão (P0):**
- Gatilho: API retorna erro ou timeout
- Condição: 3 tentativas consecutivas falharam
- Ação: Parar pipeline, notificar on-call

**Latência excessiva (P1):**
- Gatilho: Tempo entre disponibilidade na API e ingestão > 15 minutos
- Condição: Média dos últimos 10 batches > 15 min
- Ação: Investigar bottleneck, considerar retry

**Volume anormal (P2):**
- Gatilho: Volume de dados < 50% ou > 200% da média
- Condição: Comparado com média dos últimos 7 dias
- Ação: Investigar mudança na API ou erro de parsing

**Taxa de erro de API (P1):**
- Gatilho: Taxa de erro HTTP > 10%
- Condição: Última hora
- Ação: Verificar rate limits, status da API

### 5.2. Alertas de Qualidade NBA API

**Missing rate crítico (P0):**
- Gatilho: Missing rate > 10% em campos obrigatórios
- Exemplo: game_id null em > 10% dos registros
- Ação: Rejeitar batch, investigar mudança de schema

**Score impossível (P0):**
- Gatilho: Score > 200 ou < 0
- Condição: Qualquer registro
- Ação: Rejeitar registro, investigar erro de parsing

**Jogo contra si mesmo (P0):**
- Gatilho: home_team_id = away_team_id
- Condição: Qualquer registro
- Ação: Rejeitar registro, investigar erro de dados

**Data futura (P1):**
- Gatilho: game_date no futuro para jogos passados
- Condição: Qualquer registro marcado como "finished"
- Ação: Rejeitar registro, investigar timestamp

### 5.3. Alertas de Qualidade Betfair API

**Odd inválida (P0):**
- Gatilho: odd ≤ 1.0 ou odd > 1000.0
- Condição: Qualquer registro
- Ação: Rejeitar registro, investigar erro de parsing

**Volume anormal (P2):**
- Gatilho: total_matched > 3 desvios padrão da média
- Condição: Mercado específico
- Ação: Flag para revisão, investigar se é evento especial

**Timestamp futuro (P0):**
- Gatilho: timestamp > now
- Condição: Qualquer registro
- Ação: Rejeitar registro, investigar clock do sistema

**Margem de mercado extrema (P1):**
- Gatilho: odds home + odds away > 2.5 ou < 1.8
- Condição: Mercado de moneyline
- Ação: Investigar erro de odds, mercado ilíquido

---

## 6. ALERTAS PARA FEATURES

### 6.1. Alertas de Missing Values

**Missing rate crítico (P0):**
- Gatilho: Missing rate > 5% em features críticas
- Exemplo: team_rolling_avg_pts_last_5 com > 5% missing
- Ação: Parar pipeline, investigar feature engineering

**Missing rate elevado (P1):**
- Gatilho: Missing rate > 10% em features importantes
- Exemplo: player_rest_days com > 10% missing
- Ação: Investigar causa, considerar imputação

**Missing rate crescente (P2):**
- Gatilho: Missing rate aumentou > 50% vs semana anterior
- Condição: Qualquer feature
- Ação: Investigar tendência, prever esgotamento de dados

### 6.2. Alertas de Outliers

**Taxa de outliers extrema (P1):**
- Gatilho: Outlier rate > 15% em qualquer feature
- Condição: Comparado com baseline histórico
- Ação: Investigar mudança de distribuição, erro de computação

**Outlier extremo (P2):**
- Gatilho: Valor > 5 desvios padrão da média
- Condição: Feature crítica
- Ação: Flag para revisão manual, verificar se é erro

**Outlier pattern (P2):**
- Gatilho: Mesmo outlier em múltiplos registros consecutivos
- Condição: Padrão detetado
- Ação: Investigar erro sistemático

### 6.3. Alertas de Drift

**PSI alto (P1):**
- Gatilho: PSI > 0.25 em feature crítica
- Condição: Comparado com distribuição base
- Ação: Alertar para re-treino de modelo, investigar mudança de domínio

**PSI moderado (P2):**
- Gatilho: PSI > 0.1 em feature importante
- Condição: Comparado com distribuição base
- Ação: Monitorizar, planejar re-treino se persistir

**KS test significativo (P2):**
- Gatilho: p-value < 0.01 em feature crítica
- Condição: Comparado com distribuição histórica
- Ação: Investigar mudança de distribuição

### 6.4. Alertas de Data Leakage

**Computed_at futuro (P0):**
- Gatilho: computed_at ≥ game_date
- Condição: Qualquer registro
- Ação: Rejeitar batch, investigar pipeline temporal

**Feature usa dados futuros (P0):**
- Gatilho: Feature depende de resultado de jogo futuro
- Condição: Detetado em validação de lógica
- Ação: Rejeitar feature, corrigir código de feature engineering

---

## 7. ALERTAS PARA PREDICTIONS

### 7.1. Alertas de Bounds

**Probabilidade fora de bounds (P0):**
- Gatilho: Probabilidade < 0.0 ou > 1.0
- Condição: Qualquer prediction
- Ação: Rejeitar prediction, investigar modelo

**Probabilidade extrema (P1):**
- Gatilho: Probabilidade < 0.01 ou > 0.99
- Condição: Qualquer prediction
- Ação: Flag para revisão, verificar overfitting

**Spread fora de bounds (P0):**
- Gatilho: |spread| > 30
- Condição: Qualquer prediction
- Ação: Rejeitar prediction, investigar modelo

**EV fora de bounds (P0):**
- Gatilho: EV < -20% ou EV > +30%
- Condição: Qualquer prediction
- Ação: Rejeitar prediction, investigar cálculo

### 7.2. Alertas de Calibração

**Calibração degradada (P1):**
- Gatilho: Brier Score aumentou > 20% vs baseline
- Condição: Últimos 50 predictions
- Ação: Alertar para recalibração ou re-treino

**Overconfidence sistemática (P1):**
- Gatilho: Win rate < P - 10% em bin de alta probabilidade
- Condição: Bin P > 0.7
- Ação: Recalibrar probabilidades, reduzir confiança

**Subconfidence sistemática (P2):**
- Gatilho: Win rate > P + 10% em bin de baixa probabilidade
- Condição: Bin P < 0.3
- Ação: Recalibrar probabilidades, aumentar confiança

### 7.3. Alertas de Performance

**Accuracy em queda (P1):**
- Gatilho: Accuracy caiu > 10% vs baseline
- Condição: Últimos 50 predictions
- Ação: Investigar degradação, considerar re-treino

**MAE em aumento (P1):**
- Gatilho: MAE aumentou > 20% vs baseline
- Condição: Últimos 50 predictions
- Ação: Investigar degradação, considerar re-treino

**Realized EV < Predicted EV (P1):**
- Gatilho: Realized EV < Predicted EV - 10%
- Condição: Últimas 50 apostas
- Ação: Recalibrar modelo, investigar overfitting

### 7.4. Alertas de Consistência

**Inconsistência home-away (P0):**
- Gatilho: P(home) + P(away) ≠ 1.0 ± 0.01
- Condição: Qualquer prediction
- Ação: Rejeitar prediction, corrigir código

**Inconsistência spread-moneyline (P2):**
- Gatilho: Spread não corresponde a P(vitória)
- Condição: Discrepância > 10%
- Ação: Investigar modelo, verificar conversão

**Variação extrema dia-a-dia (P2):**
- Gatilho: Prediction varia > 30% para mesmo matchup
- Condição: Dias consecutivos
- Ação: Investigar instabilidade do modelo

---

## 8. CANAIS DE NOTIFICAÇÃO

### 8.1. Telegram

**Uso:**
- Alertas P0, P1, P2
- Notificações urgentes
- Comandos manuais de monitorização

**Configuração:**
- Bot dedicado para alertas
- Grupo principal: on-call engineers
- Mensagens formatadas com Markdown
- Botões para ação rápida (acknowledge, escalate)

**Formato de mensagem:**
```
🚨 [P0] CRITICAL: Falha de ingestão NBA API

📊 Detalhes:
- API: NBA API
- Erro: Connection timeout
- Timestamp: 2024-XX-XX 14:30:00 UTC
- Tentativas: 3/3

🔧 Ação requerida:
- Verificar status da API
- Reiniciar pipeline manualmente se necessário

[👋 Acknowledge] [📈 Escalar]
```

### 8.2. Slack

**Uso:**
- Alertas P1, P2, P3, P4
- Discussão de problemas
- Integração com outras ferramentas (PagerDuty, Jira)

**Configuração:**
- Channel: #data-quality-alerts
- Integração com webhook
- Threads para discussão
- Integração com Jira para ticket automático

**Formato de mensagem:**
```
⚠️ [P1] HIGH: Missing rate elevado em team_rolling_avg_pts_last_5

Details:
- Feature: team_rolling_avg_pts_last_5
- Missing rate: 12.5%
- Threshold: 5%
- Timestamp: 2024-XX-XX 14:30:00 UTC

Action: Investigar feature engineering
Thread: https://slack.com/archives/...
```

### 8.3. Email

**Uso:**
- Alertas P0, P1
- Relatórios diários/semanais
- Notificações para stakeholders não técnicos

**Configuração:**
- Lista de distribuição: data-team@company.com
- Template HTML para melhor legibilidade
- Anexos com relatórios detalhados
- Integração com sistema de tickets

**Formato de email:**
```
Subject: [P0] CRITICAL: Falha de ingestão NBA API

Dear Data Team,

A critical data quality issue has been detected:

Issue: NBA API ingestion failure
Severity: P0 (Immediate action required)
Timestamp: 2024-XX-XX 14:30:00 UTC

Details:
- Error: Connection timeout after 3 attempts
- Impact: Pipeline stopped, no new data being ingested
- Affected systems: Feature engineering, predictions

Required Action:
1. Check NBA API status
2. Restart pipeline if API is operational
3. Investigate root cause

Dashboard: https://dashboard.company.com/data-quality
Runbook: https://docs.company.com/runbooks/ingestion-failure

Best regards,
Data Quality Monitoring System
```

### 8.4. SMS (Opcional)

**Uso:**
- Alertas P0 apenas
- Notificações fora do horário de trabalho
- Quando outros canais não são respondidos

**Configuração:**
- Serviço: Twilio ou similar
- Lista de números: on-call engineers
- Limitado a 5 SMS por dia para evitar spam
- Inclui link para dashboard

**Formato de SMS:**
```
[P0] CRITICAL: NBA API ingestion failure. Pipeline stopped. Check dashboard: https://dashboard.company.com/data-quality
```

---

## 9. DASHBOARD DE MONITORIZAÇÃO

### 9.1. Componentes do Dashboard

**Página Principal (Overview):**
1. Status geral do sistema (green/yellow/red)
2. Taxa de sucesso de ingestão (última hora)
3. Taxa de sucesso de validação (última hora)
4. Número de alertas ativos por severidade
5. Top 5 alertas mais recentes

**Página de Dados Brutos:**
1. Taxa de sucesso por API (NBA vs Betfair)
2. Latência de ingestão por API
3. Volume de dados por API
4. Taxa de erro por tipo de validação
5. Mapa de calor de falhas por hora

**Página de Features:**
1. Taxa de missing values por feature (heatmap)
2. Taxa de outliers por feature (bar chart)
3. PSI por feature (bar chart)
4. Distribuição de features críticas (histogramas)
5. Correlação entre features (matrix)

**Página de Predictions:**
1. Reliability diagram (calibração)
2. Accuracy rolling (line chart)
3. Realized vs Predicted EV (line chart)
4. Distribuição de predictions (histogramas)
5. Top 10 erros mais recentes

**Página de Alertas:**
1. Histórico de alertas (tabela)
2. Alertas por severidade (pie chart)
3. Alertas por tipo (bar chart)
4. Tempo de resolução (line chart)
5. Tendência de alertas (line chart)

### 9.2. Atualização do Dashboard

**Frequência de atualização:**
- Métricas em tempo real: a cada 1 minuto
- Métricas de tendência: a cada 5 minutos
- Relatórios horários: a cada hora
- Relatórios diários: às 00:00 UTC

**Cache:**
- Métricas em tempo real: sem cache
- Métricas de tendência: cache de 1 minuto
- Relatórios: cache de 5 minutos
- Histórico: cache de 1 hora

**Performance:**
- Tempo de carregamento < 3 segundos
- Queries otimizadas com índices
- Agregações pré-computadas
- Lazy loading para dados históricos

### 9.3. Acesso e Permissões

**Permissões:**
- Admin: Acesso total, pode configurar alertas
- Engineer: Acesso de leitura e acknowledge
- Stakeholder: Acesso de leitura apenas
- Público: Acesso limitado a métricas agregadas

**Autenticação:**
- SSO (Single Sign-On)
- 2FA para admin
- Audit log de acessos

---

## 10. WORKFLOW DE RESOLUÇÃO DE ALERTAS

### 10.1. Recebimento de Alerta

1. Sistema deteta condição de alerta
2. Alerta é gerado com severidade apropriada
3. Notificação enviada via canais configurados
4. Alerta registado no dashboard

### 10.2. Acknowledge

1. On-call engineer recebe alerta
2. Engineer clica em "Acknowledge" no bot/Slack
3. Alerta marcado como "acknowledged" no dashboard
4. Timer de resolução iniciado (SLA por severidade)

### 10.3. Investigação

1. Engineer acessa dashboard para detalhes
2. Consulta logs relevantes
3. Analisa métricas relacionadas
4. Identifica causa raiz

### 10.4. Resolução

1. Engineer implementa correção
2. Valida que correção resolveu problema
3. Marca alerta como "resolved"
4. Documenta resolução no ticket

### 10.5. Post-mortem (para alertas P0/P1)

1. Reunião de post-mortem em 24-48h
2. Documentação de causa raiz
3. Identificação de melhorias
4. Implementação de prevenção
5. Atualização de runbooks

---

## 11. REFERÊNCIAS CRUZADAS

- [[31_Data_Validation/INDEX]] ← Secção mãe
- [[10_Monitoring/INDEX]] → Sistema de monitorização geral
- [[33_Alerting/INDEX]] → Sistema de alertas geral
- [[26_Runbooks/INDEX]] → Procedimentos de resolução

---

## 12. HISTÓRICO DE ALTERAÇÕES

| Data | Versão | Alteração | Autor |
|------|--------|-----------|-------|
| 2024-XX-XX | 1.0 | Criação inicial do documento | Data Engineer |