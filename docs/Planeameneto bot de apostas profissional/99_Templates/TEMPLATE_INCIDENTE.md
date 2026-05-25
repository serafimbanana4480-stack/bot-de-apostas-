# TEMPLATE_INCIDENTE — Report de Incidente

**ID:** TPL-012 | **Versão:** v1.0 | **Data:** YYYY-MM-DD  
**Tags:** #type/incident #status/[active|mitigated|resolved|postmortem] #priority/[critical|high|medium|low]

---

## 1. INFORMAÇÕES DO INCIDENTE

| Campo | Valor |
|-------|-------|
| **ID** | *INC-XXXX-YYYYMMDD-NNN* |
| **Título** | *Resumo breve* |
| **Severidade** | *[SEV-1|SEV-2|SEV-3|SEV-4|SEV-5]* |
| **Data/Hora de Início** | *YYYY-MM-DD HH:MM UTC* |
| **Data/Hora de Deteção** | *YYYY-MM-DD HH:MM UTC* |
| **Data/Hora de Resolução** | *YYYY-MM-DD HH:MM UTC* |
| **Duração** | *HH:MM* |
| **Componente Afetado** | *[API|Database|Modelo|Telegram|Infra]* |
| **Owner do Incidente** | *Nome (on-call)* |

---

## 2. RESUMO EXECUTIVO

### 2.1 O que aconteceu?
*Descrição breve (2-3 frases) do incidente, impacto e resolução.*

### 2.2 Impacto

| Métrica | Valor |
|---------|-------|
| **Utilizadores Afetados** | *Número ou %* |
| **Apostas Perdidas** | *Número* |
| **Dinheiro Perdido** | *€* |
| **Dados Perdidos** | *[Sim|Não]* |

### 2.3 Timeline Resumida

```
HH:MM - Incidente começou
HH:MM - Detetado por [quem]
HH:MM - Resposta iniciada
HH:MM - Mitigado/Resolvido
```

---

## 3. TIMELINE DETALHADA

| Hora (UTC) | Evento | Quem |
|------------|--------|------|
| *14:00* | *Primeiro sinal de problema* | *Sistema* |
| *14:05* | *Alerta disparado* | *Prometheus* |
| *14:10* | *Engenheiro entrou* | *João Silva* |
| *14:20* | *Mitigação aplicada* | *João Silva* |

---

## 4. AÇÕES DE RESPOSTA

### 4.1 Imediatas (Mitigação)

| # | Ação | Quem | Quando | Resultado |
|---|------|------|--------|-----------|
| 1 | *Restart do serviço* | *João* | *14:20* | *✅ Recuperado* |

### 4.2 Comunicação

| Stakeholder | Meio | Mensagem | Quando |
|-------------|------|----------|--------|
| *Equipa Técnica* | *Slack* | *INC-001 aberto* | *14:06* |
| *Subscritores* | *Telegram* | *Breve interrupção* | *14:30* |

---

## 5. DIAGNÓSTICO (ROOT CAUSE)

### 5.1 Cadeia de Eventos

```
Deploy v1.2.3 ──▶ Memory leak ──▶ OOM ──▶ API restart
```

### 5.2 Fator Contribuinte

- [ ] *Fator 1: Falta de testes de carga*
- [ ] *Fator 2: Monitorização insuficiente*

---

## 6. LIÇÕES APRENDIDAS

### 6.1 O que funcionou bem?

1. *Deteção rápida por Prometheus*
2. *On-call respondeu em 4 minutos*

### 6.2 O que não funcionou?

1. *Rollback demorou 2 min*
2. *Comunicação aos subscritores atrasou*

---

## 7. AÇÕES PÓS-INCIDENTE

| # | Ação | Owner | Deadline | Status |
|---|------|-------|----------|--------|
| 1 | *Implementar health check* | *DevOps* | *2024-01-22* | *[open|in_progress|done]* |

---

## 8. CHECKLIST DE FECHO

- [ ] Root cause identificado
- [ ] Ações pós-incidente criadas
- [ ] Stakeholders comunicados
- [ ] Incidente marcado como "resolved"
- [ ] Postmortem criado (se SEV-1/2)

---

## 9. LINKS CRUZADOS

- [[27_Postmortems/INDEX]] ← Postmortems
- [[26_Runbooks/INDEX]] → Runbooks
- [[28_Failure_Scenarios/INDEX]] → Cenários de falha

---

**Status:** *[Active|Mitigated|Resolved]*

---

**Fim do Template de Incidente**
