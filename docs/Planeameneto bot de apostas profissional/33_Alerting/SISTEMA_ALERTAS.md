# Sistema de Alertas — Arquitetura e Design

**ID:** `ALT-100` | **Fase:** #phase/2 | **Owner:** Operations Lead | **Status:** #status/draft

---

## 1. VISÃO GERAL

O sistema de alertas é o mecanismo que notifica a equipa quando métricas excedem thresholds definidos, indicando que algo requer atenção. Um bom sistema de alertas equilibra **sensibilidade** (detetar problemas reais) com **especificidade** (evitar falsos positivos). Alertas demasiado frequentes causam "alert fatigue" e são ignorados; alertas insuficientes deixam problemas passarem despercebidos até se tornarem críticos.

### Princípios de Design

1. **Acionável**: Cada alerta deve ter uma ação clara e documentada. Se não há ação possível, não é um alerta, é uma métrica para monitorização.
2. **Específico**: O alerta deve indicar claramente o problema e o contexto (quando, onde, quão grave).
3. **Oportuno**: O alerta deve chegar no momento certo — nem demasiado cedo (falso positivo), nem demasiado tarde (dano já causado).
4. **Hierárquico**: Nem todos os alertas têm a mesma urgência. Severidade deve escalar com o risco.
5. **Resiliente**: O sistema de alertas não deve depender dos componentes que monitoriza (evitar single point of failure).

---

## 2. ARQUITETURA DO SISTEMA DE ALERTAS

### 2.1 Pipeline de Alertas

```
┌─────────────┐     Threshold Check    ┌─────────────┐
|  Métricas   │ ───────────────────>  |  Regras de   |
|  Prometheus │  (evaluation interval)  |   Alerta    |
└─────────────┘                        └──────┬──────┘
                                              │
                                         Triggered
                                              ↓
┌─────────────┐     Routing            ┌─────────────┐
|Alertmanager │ ───────────────────>  |   Canais de  |
|  (Grafana)  │  (por severidade)      |  Notificação │
└─────────────┘                        └──────┬──────┘
                                              │
                                              ↓
                                      ┌──────────────┐
                                      │   Telegram   │
                                      │     Email    │
                                      │     SMS      │
                                      └──────────────┘
                                              │
                                              ↓
                                      ┌──────────────┐
                                      │   Ack/Resolve│
                                      │   Escalation │
                                      └──────────────┘
```

### 2.2 Componentes

**Prometheus (Evaluation Engine)**
- Avalia regras de alerta a cada `evaluation_interval` (padrão: 15s)
- Compara métricas com thresholds
- Gera alertas quando condições são satisfeitas
- Armazena estado de alertas (firing, resolved)

**Alertmanager (Routing & Deduplication)**
- Recebe alertas do Prometheus
- Agrupa alertas correlacionados (grouping)
- Remove duplicatas (deduplication)
- Roteia para canais baseado em severidade e labels
- Gerencia silêncio e inibição

**Canais de Notificação**
- **Telegram**: Canal primário para CRITICAL/HIGH (instantâneo, mobile)
- **Email**: Canal para MEDIUM/LOW e resumos diários
- **SMS** (opcional): Canal de emergência para CRITICAL em horas fora do expediente

**Gestão de Alertas**
- **Acknowledge**: Operador confirma que está a trabalhar no alerta
- **Resolve**: Alerta é fechado quando problema é resolvido
- **Escalation**: Se não resolvido em X tempo, escalar para próxima pessoa
- **Silence**: Silenciar alerta temporariamente (ex: durante manutenção)

---

## 3. NÍVEIS DE SEVERIDADE

### 3.1 Definição de Severidade

| Severidade | Cor | Tempo Resposta | Impacto | Exemplo |
|------------|-----|----------------|---------|---------|
| **CRITICAL** | Vermelho 🔴 | < 5 min (24/7) | Perda financeira imediata ou sistema down | Circuit breaker ativado, drawdown > 15% |
| **HIGH** | Laranja 🟠 | < 1 hora | Degradação significativa de performance | CLV 3d < 0%, feed offline > 5 min |
| **MEDIUM** | Amarelo 🟡 | < 4 horas | Problema que requer atenção mas não urgente | CPU > 80%, ECE > 0.10 |
| **LOW** | Azul 🔵 | < 24 horas | Informacional, baixo risco | Disco > 80%, resumo diário PnL |
| **INFO** | Cinza ⚪ | N/A | Apenas informativo, sem ação necessária | Deploy completado, backup iniciado |

### 3.2 Critérios de Classificação

**CRITICAL se**:
- Sistema está completamente down (nenhum sinal gerado)
- Risco de perda financeira > €5.000/hora
- Circuit breaker ativado (sinais pausados)
- Feed de dados offline > 10 minutos
- Banco de dados inacessível
- Segurança comprometida

**HIGH se**:
- Métrica de negócio degradada (CLV negativo, drawdown > 10%)
- Feed de dados degradado (latência alta, erros intermitentes)
- API errors > 5%
- Modelo drift significativo (> 3 features)
- Latência de execução > 2 minutos

**MEDIUM se**:
- Recursos de infraestrutura sob pressão (CPU > 80%, RAM > 85%)
- Métricas de modelo ligeiramente degradadas (ECE > 0.10)
- Qualidade de dados reduzida (nulls > 5%)
- Filas de processamento a crescer

**LOW se**:
- Recursos de infraestrutura próximos de limite (disco > 80%)
- Resumos diários/semanais de performance
- Eventos informativos (deploy, backup)

### 3.3 Exemplos de Alertas por Severidade

**CRITICAL**
```
🚨 [CRITICAL] Circuit Breaker Ativado
Trigger: Drawdown diário > 15%
Valor atual: 17.3%
Ação: Pausar novas apostas, investigar causa
Timestamp: 2024-01-15 14:32:00 UTC
```

**HIGH**
```
⚠️ [HIGH] CLV 3d Negativo
Trigger: CLV médio últimas 50 apostas < 0%
Valor atual: -0.8%
Ação: Monitorizar, considerar retreino de modelo
Timestamp: 2024-01-15 12:00:00 UTC
```

**MEDIUM**
```
⚡ [MEDIUM] CPU Usage Elevado
Trigger: CPU > 80% por 5 minutos
Valor atual: 82%
Ação: Investigar processo consumidor
Timestamp: 2024-01-15 10:15:00 UTC
```

**LOW**
```
ℹ️ [LOW] Disco Próximo do Limite
Trigger: Disk usage > 80%
Valor atual: 81%
Ação: Planear limpeza ou upgrade de disco
Timestamp: 2024-01-15 08:00:00 UTC
```

---

## 4. CANAIS DE NOTIFICAÇÃO

### 4.1 Telegram (Canal Primário)

**Uso**: CRITICAL e HIGH

**Vantagens**:
- Notificações push instantâneas em mobile
- Suporte para formatação rica (Markdown)
- Interação com bot (comandos de acknowledge/resolve)
- Grupos para notificação múltipla
- Zero custo

**Configuração**:
- **Grupo P1 (CRITICAL)**: Todos os on-call + gestor de operações
- **Grupo P2 (HIGH)**: Operations lead + DevOps on-call
- **Grupo P3 (MEDIUM)**: Operations lead (resumo diário às 9h)

**Formato de Mensagem**:
```markdown
🚨 [CRITICAL] Circuit Breaker Ativado

📊 Métrica: Drawdown Diário
📈 Valor: 17.3% (limite: 15%)
🕐 Timestamp: 2024-01-15 14:32:00 UTC
🔗 Dashboard: https://grafana.example.com/d/risk-overview

📋 Ação Recomendada:
1. Verificar dashboard de risco
2. Identificar causa de drawdown
3. Ativar playbook: [[26_Runbooks/CIRCUIT_BREAKER]]

/bot acknowledge - Confirmar recebimento
/bot resolve - Marcar como resolvido
/bot escalate - Escalar para gestor
```

**Interação com Bot**:
- `/acknowledge`: Operador confirma que está a trabalhar no alerta
- `/resolve`: Alerta é fechado
- `/comment`: Adicionar comentário ao alerta
- `/snooze 30m`: Silenciar por 30 minutos
- `/escalate`: Escalar para próximo na rota

### 4.2 Email (Canal Secundário)

**Uso**: MEDIUM, LOW, e cópia de CRITICAL/HIGH

**Vantagens**:
- Audit trail permanente
- Suporte para anexos (logs, screenshots)
- Integrado com ferramentas de ticket (Jira, Zendesk)
- Acessível sem mobile

**Configuração**:
- **alerts-critical@domain.com**: CRITICAL (todos os stakeholders)
- **alerts-high@domain.com**: HIGH (operations + devops)
- **alerts-medium@domain.com**: MEDIUM (operations)
- **alerts-digest@domain.com**: LOW (digest diário às 18h)

**Formato de Email**:
```
Subject: [CRITICAL] Circuit Breaker Ativado - 2024-01-15 14:32

Alert Details:
- Severity: CRITICAL
- Metric: Drawdown Diário
- Value: 17.3% (threshold: 15%)
- Duration: 2 minutes
- Dashboard: https://grafana.example.com/d/risk-overview

Recommended Action:
1. Verificar dashboard de risco
2. Identificar causa de drawdown
3. Ativar playbook: Circuit Breaker

Runbook: https://docs.example.com/runbooks/circuit-breaker
View in Grafana: https://grafana.example.com/alerting

---
This is an automated alert from the NBA Value Betting System.
```

### 4.3 SMS (Canal de Emergência)

**Uso**: CRITICAL em horas fora do expediente (22h-8h)

**Vantagens**:
- Garante notificação mesmo sem internet/Telegram
- Alta taxa de leitura
- Curto, direto

**Configuração**:
- Apenas para CRITICAL
- Apenas para on-call principal
- Limite: 1 SMS por 30 minutos (evitar spam)

**Formato de SMS**:
```
[CRITICAL] Circuit Breaker Ativado. Drawdown: 17.3%. Ação: Verificar dashboard. Link: https://grafana.example.com/d/risk
```

### 4.4 Digests (Resumos)

**Diário (LOW)**
- Enviado às 18h
- Contém todos os alertas LOW do dia
- Inclui resumo de métricas chave (PnL, CLV, Uptime)

**Semanal (MEDIUM)**
- Enviado segunda-feira às 9h
- Resumo de alertas MEDIUM da semana
- Tendências de infraestrutura
- Recomendações de manutenção

**Mensal (Executivo)**
- Enviado dia 1 do mês
- Resumo executivo de todos os alertas
- MTTR (Mean Time To Resolve) por severidade
- Análise de falsos positivos

---

## 5. ROTEAMENTO E ESCALAÇÃO

### 5.1 Matriz de Roteamento

| Severidade | Canal Primário | Canal Secundário | Escalação |
|------------|----------------|------------------|-----------|
| CRITICAL | Telegram (Grupo P1) | Email (all) | 5 min → SMS (on-call) → 15 min → Gestor |
| HIGH | Telegram (Grupo P2) | Email (ops+devops) | 1h → Gestor |
| MEDIUM | Email (ops) | Telegram (resumo 9h) | 4h → DevOps |
| LOW | Email (digest 18h) | - | 24h → Ops (se não resolvido) |

### 5.2 Lógica de Escalação

**Nível 1: On-call Principal**
- Tempo de resposta esperado: 5 min (CRITICAL), 1h (HIGH)
- Ação: Acknowledge + investigar

**Nível 2: On-call Secundário**
- Trigger: Nível 1 não responde em X minutos
- Ação: Notificar backup + escalar

**Nível 3: Gestor de Operações**
- Trigger: Nível 2 não resolve ou problema persiste
- Ação: Decisão de escalamento externo (ex: contactar provider)

### 5.3 Exemplo de Fluxo de Escalação

```
Alerta CRITICAL: Feed Offline
  ↓
T+0 min: Telegram para Grupo P1 (Ops Lead + DevOps On-call)
  ↓
T+5 min: Se não acknowledge → SMS para On-call
  ↓
T+15 min: Se não resolvido → Telegram para Gestor
  ↓
T+30 min: Se não resolvido → Escalar para Direção Técnica
```

### 5.4 Regras de Silêncio e Inibição

**Silêncio Temporário**
- Usar durante manutenção planeada
- Configurar duração (ex: 2 horas)
- Auto-expiração

**Inibição**
- Se alerta A é inibido por alerta B, quando B dispara, A não notifica
- Exemplo: "Database down" inibe "Slow queries" (se DB está down, slow queries são esperados)

**Janelas de Manutenção**
- Configurar janelas de silêncio recorrentes (ex: domingo 2-4am para backups)
- Documentar no calendário da equipa

---

## 6. PREVENÇÃO DE ALERT FATIGUE

### 6.1 Dampening

**Definição**: Aguardar X tempo antes de notificar, para evitar alertas por picos transitórios.

**Exemplo**:
- CPU > 95% por 10 segundos → Não alertar (pico normal)
- CPU > 95% por 5 minutos → Alertar (problema real)

**Configuração**:
```yaml
alert: HighCPUUsage
expr: cpu_usage_percent > 95
for: 5m  # Dampening: apenas alertar se > 95% por 5 minutos
labels:
  severity: HIGH
```

### 6.2 Agrupamento (Grouping)

**Definição**: Agrupar alertas correlacionados numa única notificação.

**Exemplo**:
- Em vez de 10 alertas "Database connection failed" (um por query), enviar 1 alerta "Database: 10 connection failures in 1m"

**Configuração**:
```yaml
group_by: ['alertname', 'cluster', 'service']
group_wait: 10s      # Aguardar 10s para agrupar
group_interval: 10s  # Agrupar novos alertas na janela de 10s
repeat_interval: 12h # Repetir a cada 12h se não resolvido
```

### 6.3 Limitação de Frequência

**Regra**: Mesmo alerta não pode notificar mais de X vezes em Y horas.

**Exemplo**:
- "Disk usage > 80%" pode notificar no máximo 1 vez por hora
- Evita spam se threshold é ligeiramente excedido

### 6.4 Janelas de Silêncio Automáticas

**Detectar Falsos Positivos Recorrentes**:
- Se alerta X é resolvido sem ação em < 5 minutos, 5 vezes consecutivas
- Automaticamente aumentar dampening para 15 minutos
- Notificar equipa: "Alerta X ajustado: dampening aumentado para 15m devido a falsos positivos"

---

## 7. MÉTRICAS DO SISTEMA DE ALERTAS

### 7.1 KPIs de Alerting

**MTTR (Mean Time To Resolve)**
- Definição: Tempo médio desde alerta até resolução
- Meta por severidade: CRITICAL < 30min, HIGH < 2h, MEDIUM < 8h
- Cálculo: (Σ resolve_time - firing_time) / total_alerts

**MTTA (Mean Time To Acknowledge)**
- Definição: Tempo médio desde alerta até acknowledge
- Meta por severidade: CRITICAL < 5min, HIGH < 30min
- Cálculo: (Σ acknowledge_time - firing_time) / total_alerts

**False Positive Rate**
- Definição: Percentagem de alertas que não requerem ação
- Meta: < 10%
- Cálculo: (alertas_resolvidos_sem_ação / total_alerts) × 100

**Alert Volume**
- Definição: Número de alertas por dia/semana
- Meta: < 50 alertas/dia (todos os níveis)
- Monitorizar tendências (aumento indica problemas ou thresholds incorretos)

### 7.2 Dashboard de Alerting

**Painéis Recomendados**:
1. **Alertas por Severidade** (bar chart) - Volume por nível
2. **MTTR por Severidade** (gauge) - Tempo de resposta
3. **Top 10 Alertas Mais Frequentes** (table) - Identificar ruído
4. **Falsos Positivos por Alerta** (table) - Ajustar thresholds
5. **Alertas Não Acknowledged** (list) - Ação pendente

---

## 8. CHECKLIST DE IMPLEMENTAÇÃO

- [ ] Instalar e configurar Prometheus
- [ ] Instalar e configurar Alertmanager
- [ ] Definir regras de alerta para todas as métricas críticas
- [ ] Configurar canais de notificação (Telegram, Email)
- [ ] Implementar bot Telegram com comandos de interação
- [ ] Configurar roteamento por severidade
- [ ] Implementar lógica de escalação
- [ ] Configurar dampening para todos os alertas
- [ ] Implementar agrupamento de alertas correlacionados
- [ ] Criar playbook para cada tipo de alerta
- [ ] Testar pipeline end-to-end (simular alerta CRITICAL)
- [ ] Configurar janelas de silêncio para manutenção
- [ ] Implementar métricas de alerting (MTTR, MTTA)
- [ ] Criar dashboard de monitorização de alertas
- [ ] Documentar processo de on-call e escalada
- [ ] Treinar equipa em resposta a alertas

---

## 9. LINKS CRUZADOS

- [[33_Alerting/INDEX]] ← Seção mãe
- [[33_Alerting/ALERTAS_TELEGRAM]] → Configuração específica Telegram
- [[33_Alerting/PLAYBOOKS_ALERTAS]] → Playbooks de resposta por tipo de alerta
- [[10_Monitoring/INDEX]] → Métricas que geram alertas
- [[20_Dashboarding/DB_OPERATIONS_CENTER]] → Dashboard que mostra alertas ativos
- [[26_Runbooks/INDEX]] → Runbooks operacionais detalhados