# TEMPLATE_INCIDENTE — Registo de Incidente

**ID:** `INC-YYYY-NNN` *  
**Título:** *[Título curto descritivo]*  
**Data/Hora Deteção:** `YYYY-MM-DD HH:MM UTC` *  
**Data/Hora Resolução:** `YYYY-MM-DD HH:MM UTC` *  
**Severidade:** 🔴 Critical / 🟠 High / 🟡 Medium / 🟢 Low *  
**Tipo:** #type/incident  
**Área:** #area/data / #area/ml / #area/exec / #area/ops / #area/infra *  
**Owner:** *[Nome do responsável]*  
**Status:** #status/active / #status/resolved / #status/postmortem  

---

## 1. SUMÁRIO EXECUTIVO

*[2-3 frases: o que aconteceu, impacto, como foi resolvido]*

---

## 2. LINHA DO TEMPO

| Hora (UTC) | Evento |
|------------|--------|
| HH:MM | Incidente detetado |
| HH:MM | Equipa notificada |
| HH:MM | Diagnóstico inicial |
| HH:MM | Mitigação aplicada |
| HH:MM | Resolução confirmada |
| HH:MM | Postmortem agendado |

---

## 3. IMPACTO

### 3.1 Impacto Financeiro
- Apostas afetadas: `N`
- PnL impactado: `X€` (estimativa)
- Período de indisponibilidade: `HH:MM`

### 3.2 Impacto Operacional
- [ ] Pipeline de dados interrompido
- [ ] Sinais não gerados durante o incidente
- [ ] Apostas executadas incorretamente
- [ ] Dashboard/alertas não funcionaram
- [ ] Subscritores Telegram afetados

---

## 4. ROOT CAUSE

*[Análise técnica da causa raiz — ser específico e evitar "falha humana" como causa final]*

**Causa Imediata:** *[O que falhou diretamente]*  
**Causa Contribuinte:** *[O que tornou a falha possível]*  
**Causa Raiz:** *[Por que a causa contribuinte existia]*

---

## 5. DIAGNÓSTICO

### 5.1 Logs Relevantes
```
[YYYY-MM-DD HH:MM:SS] ERROR — [mensagem de erro]
```

### 5.2 Métricas no Momento do Incidente
| Métrica | Valor Normal | Valor Observado |
|---------|-------------|-----------------|
| | | |

### 5.3 Runbook Seguido
- [[26_Runbooks/RB-XXX_NOME_DO_RUNBOOK]]

---

## 6. MITIGAÇÃO E RESOLUÇÃO

### 6.1 Ação Imediata (contenção)
```bash
# Comandos executados para conter o incidente
```

### 6.2 Fix Definitivo
*[O que foi alterado para resolver permanentemente]*

### 6.3 Verificação
- [ ] Sistema a funcionar normalmente
- [ ] Métricas dentro dos thresholds
- [ ] Alertas desativados (incidente resolvido)
- [ ] Dados históricos reconciliados

---

## 7. LIÇÕES APRENDIDAS

| # | Lição | Ação Derivada | Owner | Prazo |
|---|-------|--------------|-------|-------|
| 1 | | | | |
| 2 | | | | |

---

## 8. MELHORIAS DE PREVENÇÃO

- [ ] *[Melhoria de monitorização]*
- [ ] *[Melhoria de runbook]*
- [ ] *[Melhoria de código/infraestrutura]*
- [ ] *[Melhoria de processo]*

---

## 9. LINKS CRUZADOS

- [[27_Postmortems/INDEX]] → Histórico de postmortems
- [[26_Runbooks/INDEX]] → Runbooks de resposta
- [[28_Failure_Scenarios/CENARIOS_FALHA]] → Cenários mapeados

---

**Este template deve ser preenchido em até 24h após a resolução do incidente.**  
**Postmortem obrigatório para incidentes de severidade Critical e High.**
