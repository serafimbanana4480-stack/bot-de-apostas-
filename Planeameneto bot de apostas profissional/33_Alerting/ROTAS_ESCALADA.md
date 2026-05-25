# ROTAS_ESCALADA — Rotas de Escalação por Severidade

**ID:** `AL-002` | **Fase:** Todas | **Owner:** DevOps Engineer | **Status:** #status/active

---

## 1. OBJETIVO

Definir as rotas de escalação de alertas por severidade e tipo de incidente.

---

## 2. NÍVEIS DE SEVERIDADE

### P1 - Critical
- **Definição:** Sistema indisponível ou perda de dados iminente
- **Tempo de Resposta:** < 15 minutos
- **Escalão:** On-call imediato

### P2 - High
- **Definição:** Funcionalidade crítica degradada
- **Tempo de Resposta:** < 1 hora
- **Escalão:** On-call + Team Lead

### P3 - Medium
- **Definição:** Funcionalidade não-crítica afetada
- **Tempo de Resposta:** < 4 horas
- **Escalão:** Daytime team

### P4 - Low
- **Definição:** Questão informativa ou melhoria
- **Tempo de Resposta:** < 24 horas
- **Escalão:** Normal backlog

---

## 3. ROTAS DE ESCALAÇÃO

### 3.1 Sistema Indisponível (P1)

```
1. Alerta disparado → Telegram (on-call)
2. On-call acknowledged (5 min)
3. Se não acknowledged → SMS (10 min)
4. Se não resolvido (15 min) → Escalar para Team Lead
5. Se não resolvido (30 min) → Escalar para CTO
```

### 3.2 CLV Negativo Crítico (P2)

```
1. Alerta disparado → Telegram (Operations Lead)
2. Operations Lead acknowledged (30 min)
3. Se não resolvido (1 hora) → Escalar para Quant Engineer
4. Se não resolvido (2 horas) → Escalar para Product Manager
```

### 3.3 Drawdown Acelerado (P2)

```
1. Alerta disparado → Telegram (Risk Manager)
2. Circuit breaker ativado automaticamente
3. Risk Manager acknowledged (15 min)
4. Se não resolvido (1 hora) → Escalar para Operations Lead
```

### 3.4 API Latency Alta (P3)

```
1. Alerta disparado → Telegram (DevOps Engineer)
2. DevOps Engineer acknowledged (1 hora)
3. Investigar durante horário comercial
4. Se persistir → Escalar para Team Lead
```

---

## 4. CANAIS DE NOTIFICAÇÃO

### Telegram
- **Uso:** Alertas primários
- **Grupos:**
  - `#alerts-critical` - P1 alerts
  - `#alerts-high` - P2 alerts
  - `#alerts-medium` - P3 alerts
  - `#alerts-low` - P4 alerts

### SMS
- **Uso:** Escalamento P1 não acknowledged
- **Provedor:** Twilio
- **Custo:** ~0.05€/SMS

### Email
- **Uso:** Relatórios diários e resumos
- **Frequência:** Diário para P3+, Semanal para P4

### Slack
- **Uso:** Coordenação de equipe
- **Canais:** `#incidents`, `#operations`

---

## 5. ON-CALL ROTA

### Semana
- **Segunda-Quinta:** DevOps Engineer
- **Quinta-Domingo:** Operations Lead

### Fim de Semana
- **Sábado-Domingo:** Operations Lead (backup: DevOps Engineer)

### Feriados
- **On-call:** Team Lead

---

## 6. PROCEDIMENTO DE ESCALAÇÃO

### Passo 1: Acknowledgement
- Responder ao alerta com "ACK"
- Estimar tempo de resolução

### Passo 2: Investigação
- Seguir runbook apropriado
- Documentar descobertas

### Passo 3: Resolução
- Implementar fix
- Verificar resolução

### Passo 4: Comunicação
- Atualizar status no canal
- Notificar stakeholders se necessário

### Passo 5: Post-Incidente
- Criar postmortem
- Atualizar runbooks
- Implementar melhorias

---

## 7. BACKLOG

- [ ] Implementar sistema de on-call automático
- [ ] Adicionar integração com PagerDuty
- [ ] Criar dashboard de tempo de resposta

---

## 8. LINKS CRUZADOS

- [[33_Alerting/INDEX]] ← Secção mãe
- [[33_Alerting/THRESHOLDS_ALERTAS]] → Thresholds
- [[33_Alerting/PLAYBOOK_RESPOSTA]] → Playbooks
