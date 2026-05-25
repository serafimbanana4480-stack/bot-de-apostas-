# ALERTAS_DRIFT — Sistema de Notificação Automática

**ID:** `DRIFT-005` | **Fase:** #phase/6 | **Owner:** Data Engineer | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar sistema de alertas automáticos para notificar a equipa quando drift é detetado, garantindo resposta rápida para mitigar impactos no sistema de value betting.

---

## 2. CONTEXTO

Drift detection sem alertas eficazes é inútil. Quando drift é detetado, a equipa precisa de ser notificada rapidamente para:
- Avaliar a severidade do problema
- Decidir sobre ações corretivas
- Minimizar perdas financeiras
- Manter a confiança no sistema

**Requisitos:**
- Alertas em tempo real para drift crítico
- Alertas oportunos para drift moderado
- Agregação de alertas para evitar spam
- Hierarquia de severidade clara
- Canais de notificação múltiplos

---

## 3. NÍVEIS DE ALERTA

### 3.1 Hierarquia de Severidade

| Nível | Cor | Threshold Típico | Tempo de Resposta | Ação |
|-------|-----|------------------|-------------------|------|
| **INFO** | Cinza | PSI < 0.10 | 24h | Logging apenas |
| **WARNING** | Amarelo | PSI 0.10 - 0.20 | 4h | Monitorizar de perto |
| **HIGH** | Laranja | PSI 0.20 - 0.30 | 1h | Preparar retraining |
| **CRITICAL** | Vermelho | PSI > 0.30 | 15min | Ação imediata |

### 3.2 Critérios por Tipo de Drift

**Feature Drift:**
- INFO: PSI < 0.10
- WARNING: PSI 0.10 - 0.20
- HIGH: PSI 0.20 - 0.30
- CRITICAL: PSI > 0.30

**Prediction Drift:**
- INFO: PSI probs < 0.05
- WARNING: PSI probs 0.05 - 0.15
- HIGH: PSI probs 0.15 - 0.25
- CRITICAL: PSI probs > 0.25

**Target Drift:**
- INFO: Δ proporção < 1%
- WARNING: Δ proporção 1 - 2%
- HIGH: Δ proporção 2 - 5%
- CRITICAL: Δ proporção > 5%

**Concept Drift:**
- INFO: Δ accuracy < 2%
- WARNING: Δ accuracy 2 - 5%
- HIGH: Δ accuracy 5 - 10%
- CRITICAL: Δ accuracy > 10%

---

## 4. CANAIS DE NOTIFICAÇÃO

### 4.1 Telegram (Primário)

**Uso:** Alertas de todos os níveis

**Vantagens:**
- Notificações push em tempo real
- Suporte para mensagens formatadas
- Integração fácil com bots
- Acesso móvel

**Configuração:**
- Canal principal para alertas operacionais
- Canais separados por severidade (opcional)
- Bot para comandos (acknowledge, snooze, etc.)

### 4.2 Email (Secundário)

**Uso:** Alertas HIGH e CRITICAL + resumos diários/semanais

**Vantagens:**
- Registro permanente
- Fácil forwarding
- Suporte para anexos
- Integração com sistemas de ticket

**Configuração:**
- Alertas HIGH: email imediato
- Alertas CRITICAL: email imediato + SMS
- Resumo diário: email às 09:00
- Resumo semanal: email segunda-feira às 09:00

### 4.3 Slack (Opcional)

**Uso:** Alertas INFO e WARNING + discussão de equipe

**Vantagens:**
- Integração com outras ferramentas
- Threads para discussão
- Webhooks fáceis
- Histórico pesquisável

**Configuração:**
- Canal #drift-alerts para alertas
- Canal #drift-discussion para análise
- Integração com PagerDuty (se usado)

### 4.4 SMS (Emergência)

**Uso:** Apenas alertas CRITICAL fora do horário comercial

**Vantagens:**
- Alta probabilidade de ser visto
- Independente de internet
- Urgência clara

**Configuração:**
- Apenas para CRITICAL
- Apenas fora do horário comercial (18:00-09:00)
- Limite de 1 SMS por hora para evitar spam

---

## 5. CONTEÚDO DO ALERTA

### 5.1 Estrutura da Mensagem

```
🚨 [CRITICAL] DRIFT DETECTADO

Tipo: Feature Drift
Feature: odds_home
PSI: 0.35 (threshold: 0.30)
Timestamp: 2024-01-15 14:32:00
Impacto: Apostas podem ter EV incorreto

Ação Recomendada: Pausar apostas; investigar causa

Detalhes:
- Referência: média=2.10, std=0.45
- Atual: média=2.45, std=0.62
- KS test p-value: 0.001

[ACK] | [SNOOZE 1h] | [VIEW DASHBOARD]
```

### 5.2 Campos Obrigatórios

- **Severidade:** INFO/WARNING/HIGH/CRITICAL
- **Tipo de drift:** Feature/Prediction/Target/Concept
- **Métrica principal:** PSI, accuracy, etc.
- **Valor atual vs threshold:** 0.35 (threshold: 0.30)
- **Timestamp:** Quando drift foi detetado
- **Impacto potencial:** O que pode acontecer
- **Ação recomendada:** O que fazer

### 5.3 Campos Opcionais

- **Contexto adicional:** Informação sobre causa possível
- **Link para dashboard:** URL para visualização
- **Histórico:** Tendência dos últimos dias
- **Segmentos afetados:** Quais ligas/desportos

---

## 6. AGREGAÇÃO E DEDUPLICAÇÃO

### 6.1 Agregação Temporal

Evitar spam agregando alertas próximos no tempo.

**Regras:**
- Mesma feature + mesmo tipo + mesma severidade dentro de 1h → 1 alerta
- Alertas INFO: agregar em resumos diários
- Alertas WARNING: máximo 1 por hora por feature
- Alertas HIGH: máximo 1 por 15min por feature
- Alertas CRITICAL: imediato (sem agregação)

### 6.2 Agregação Espacial

Agrupar alertas relacionados por segmento.

**Regras:**
- Múltiplas features da mesma liga → 1 alerta agregado
- Drift em múltiplos tipos (feature + prediction) → 1 alerta combinado
- Alertas por liga: se > 3 ligas com drift → 1 alerta geral

### 6.3 Deduplicação

Evitar alertas duplicados do mesmo evento.

**Regras:**
- Mesmo hash do alerta dentro de 5min → ignorar
- Alerta já acknowledged → não reenviar
- Alerta snoozed → não reenviar até expirar snooze

---

## 7. WORKFLOW DE RESPOSTA

### 7.1 Ações Disponíveis

**ACK (Acknowledge):**
- Confirmar que alerta foi visto
- Parar reenvios do mesmo alerta
- Obrigatório para alertas HIGH e CRITICAL

**SNOOZE:**
- Adiar alerta por período definido
- Opções: 15min, 1h, 4h, 24h
- Útil para investigação em andamento

**ESCALATE:**
- Elevar severidade do alerta
- Notificar próxima pessoa na cadeia
- Usar se não houver resposta em tempo definido

**RESOLVE:**
- Marcar alerta como resolvido
- Adicionar notas sobre resolução
- Obrigatório antes de fechar alerta

### 7.2 Tempos de Resposta Esperados

| Severidade | Tempo de ACK | Tempo de Resolução | Escalação |
|-----------|--------------|--------------------|-----------|
| INFO | 24h | 72h | Não escala |
| WARNING | 4h | 24h | Escala após 8h |
| HIGH | 1h | 8h | Escala após 2h |
| CRITICAL | 15min | 1h | Escala após 30min |

### 7.3 Cadeia de Escalação

**Nível 1:** Data Engineer on-call
**Nível 2:** MLOps Lead
**Nível 3:** Tech Lead
**Nível 4:** CTO (apenas para CRITICAL fora do horário)

---

## 8. CONFIGURAÇÃO

### 8.1 Arquivo de Configuração

```yaml
alerting:
  channels:
    telegram:
      enabled: true
      bot_token: "${TELEGRAM_BOT_TOKEN}"
      chat_id: "${TELEGRAM_CHAT_ID}"
      levels: [INFO, WARNING, HIGH, CRITICAL]
    
    email:
      enabled: true
      smtp_server: "smtp.example.com"
      from: "drift-alerts@example.com"
      to: ["mlops-team@example.com"]
      levels: [HIGH, CRITICAL]
      daily_summary: true
      daily_summary_time: "09:00"
    
    slack:
      enabled: false
      webhook_url: "${SLACK_WEBHOOK_URL}"
      levels: [INFO, WARNING]
    
    sms:
      enabled: true
      provider: "twilio"
      phone_numbers: ["+351912345678"]
      levels: [CRITICAL]
      business_hours_only: true
  
  aggregation:
    time_window:
      INFO: 86400  # 24h
      WARNING: 3600  # 1h
      HIGH: 900  # 15min
      CRITICAL: 0  # imediato
    
    spatial:
      by_league: true
      by_sport: true
      max_alerts_per_batch: 5
  
  escalation:
    enabled: true
    levels:
      WARNING:
        ack_timeout: 14400  # 4h
        resolve_timeout: 86400  # 24h
        escalate_to: "mlops-lead"
      HIGH:
        ack_timeout: 3600  # 1h
        resolve_timeout: 28800  # 8h
        escalate_to: "tech-lead"
      CRITICAL:
        ack_timeout: 900  # 15min
        resolve_timeout: 3600  # 1h
        escalate_to: ["tech-lead", "cto"]
```

### 8.2 Variáveis de Ambiente

```bash
# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=-1001234567890

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=alerts@example.com
SMTP_PASSWORD=secret

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# SMS
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890
```

---

## 9. MONITORIZAÇÃO DO SISTEMA DE ALERTAS

### 9.1 Métricas do Sistema

Monitorizar a saúde do sistema de alertas:

- **Latência de envio:** Tempo entre deteção e notificação
- **Taxa de sucesso:** % de alertas entregues com sucesso
- **Taxa de falso positivo:** Alertas que não requerem ação
- **Tempo de resposta:** Tempo entre alerta e ACK
- **Tempo de resolução:** Tempo entre alerta e RESOLVE

### 9.2 Alertas do Sistema

O sistema de alertas deve ter seus próprios alertas:

- Alerta se latência > 5min
- Alerta se taxa de sucesso < 95%
- Alerta se canal de notificação está down
- Alerta se configuração é inválida

---

## 10. MELHORIAS FUTURAS

- [ ] Implementar inteligência para reduzir falsos positivos
- [ ] Adicionar machine learning para priorizar alertas
- [ ] Implementar auto-remediação para alertas simples
- [ ] Adicionar integração com sistemas de ticket (Jira, etc.)
- [ ] Implementar dashboard de alertas em tempo real
- [ ] Adicionar histórico de alertas para análise de padrões

---

## 11. LINKS CRUZADOS

- [[48_Data_Drift/INDEX]] ← Secção mãe
- [[48_Data_Drift/DETECAO_FEATURE_DRIFT]] → Detecção de feature drift
- [[48_Data_Drift/DETECAO_PREDICTION_DRIFT]] → Detecção de prediction drift
- [[48_Data_Drift/DETECAO_TARGET_DRIFT]] → Detecção de target drift
- [[48_Data_Drift/DETECAO_CONCEPT_DRIFT]] → Detecção de concept drift
- [[48_Data_Drift/MITIGACAO_DRIFT]] → Resposta a drift
- [[11_MLOps/INDEX]] → Operações de MLOps