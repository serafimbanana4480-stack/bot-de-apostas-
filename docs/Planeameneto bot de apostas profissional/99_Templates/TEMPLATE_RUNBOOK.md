# TPL-006 — Runbook de Resposta a Incidentes

**ID:** `RB-XXX`  
**Nome:** *Nome descritivo do incidente*  
**Severidade:** *[Critical/High/Medium/Low]*  
**Status:** #status/active  
**Owner:** *Nome do responsável técnico*  
**Última Atualização:** *YYYY-MM-DD*

---

## 1. RESUMO EXECUTIVO

| Campo | Descrição |
|-------|-----------|
| **O que é?** | *Breve descrição do incidente* |
| **Impacto** | *Quem/que sistemas afeta* |
| **RTO** | *Tempo máximo de recuperação esperado* |
| **Risco se não resolvido** | *Consequências de não atuar* |

---

## 2. SINTOMAS E DETEÇÃO

### 2.1 Como Identificar

| Indicador | Threshold | Fonte |
|-----------|-----------|-------|
| *Ex: API response time* | *> 5 segundos* | *Prometheus* |
| *Ex: Error rate* | *> 1%* | *Grafana* |
| *Ex: Database connections* | *> 80* | *PostgreSQL metrics* |

### 2.2 Alertas Automáticos
- **PagerDuty/Opsgenie:** *[Se aplicável]*
- **Telegram:** *@channel*
- **Email:** *on-call@vbq.pt*

### 2.3 Sinais Visuais
- *Dashboard Grafana mostra cor vermelha em...*
- *Logs mostram padrão...*

---

## 3. DIAGNÓSTICO (Triage)

### 3.1 Passos de Diagnóstico (em ordem)

#### Passo 1: Verificar Status dos Serviços
```bash
# Comandos para verificar status
docker compose ps
docker compose logs --tail=100 [serviço]
systemctl status [serviço]
```

#### Passo 2: Verificar Métricas
- Aceder a: `http://grafana.vbq.local`
- Dashboard: `System Health`
- Verificar: CPU, memória, disco, network

#### Passo 3: Verificar Logs
```bash
# Logs recentes
docker compose logs --since=10m [serviço]

# Logs com erro
docker compose logs | grep ERROR
```

### 3.2 Checklist de Diagnóstico

- [ ] Serviço está running?
- [ ] Portas estão abertas?
- [ ] Database responde?
- [ ] Dependências (Redis, API externa) funcionam?
- [ ] Último deploy correlaciona com início do incidente?
- [ ] Recursos (CPU/memória/disco) estão OK?

### 3.3 Ferramentas de Diagnóstico

| Ferramenta | Uso | Comando/Link |
|--------------|-----|--------------|
| **Grafana** | Dashboards de métricas | `http://grafana:3000` |
| **Prometheus** | Métricas e alertas | `http://prometheus:9090` |
| **Docker** | Status de containers | `docker compose ps` |
| **PostgreSQL** | Queries de diagnóstico | `psql -U vb_admin` |
| **Logs** | Análise de erros | `docker compose logs` |

---

## 4. RESOLUÇÃO (Playbook)

### 4.1 Solução 1: *[Título da Solução Principal]*

**Quando usar:** *Descrição da condição*

**Passos:**
1. *Passo detalhado 1*
   ```bash
   # Comando exemplo
   docker compose restart [serviço]
   ```

2. *Passo detalhado 2*
   ```sql
   -- Query exemplo
   SELECT COUNT(*) FROM table WHERE condition;
   ```

3. *Passo detalhado 3*

**Verificação pós-resolução:**
- [ ] Métrica X voltou ao normal (< threshold)
- [ ] Teste funcional passa: `curl http://api/health`
- [ ] Logs não mostram mais erros

**Tempo estimado:** *X minutos*

### 4.2 Solução 2: *[Título da Solução Alternativa]*

**Quando usar:** *Se Solução 1 falhar ou não for aplicável*

**Passos:**
1. 
2. 
3. 

---

## 5. ESCALAÇÃO

### 5.1 Quando Escalar

| Situação | Escalar Para | Tempo Máximo |
|----------|--------------|--------------|
| Não consegue diagnosticar em 15 min | Senior Engineer | 15 min |
| Solução 1 e 2 falharam | On-call Lead | 30 min |
| Impacto em clientes > 50% | Incident Commander | Imediato |
| Data loss suspeito | CTO + DBA | Imediato |

### 5.2 Contactos de Escalada

| Nível | Nome | Contacto | Disponibilidade |
|-------|------|----------|-----------------|
| **L1** | *On-call Engineer* | *Telegram: @vbq-oncall* | *24/7* |
| **L2** | *Senior Engineer* | *Telegram: @vbq-senior* | *24/7* |
| **L3** | *Tech Lead* | *Telegram: @vbq-lead* | *8h-22h* |
| **L4** | *CTO* | *Telegram: @vbq-cto* | *Emergências* |

### 5.3 Informação Necessária para Escalar

Ao escalar, fornecer:
1. **ID do Runbook:** RB-XXX
2. **Tempo desde início:** *X minutos*
3. **Impacto:** *Quem afeta*
4. **Diagnóstico atual:** *O que já foi verificado*
5. **Tentativas de resolução:** *O que já foi tentado*

---

## 6. COMUNICAÇÃO

### 6.1 Durante o Incidente

| Stakeholder | Meio | Frequência | Mensagem |
|-------------|------|------------|----------|
| **Equipa Técnica** | #incidentes Slack | A cada 15 min | Status atual |
| **Stakeholders** | #updates Slack | A cada 30 min | Impacto e ETA |
| **Clientes** | Status page | Quando afetado | Transparência |

### 6.2 Templates de Comunicação

**Início do Incidente:**
```
🔴 INCIDENTE ABERTO - RB-XXX
Impacto: [Descrição]
Início: [Hora]
Ação: Investigação em curso
ETA: 15 min para update
```

**Update:**
```
🟡 UPDATE - RB-XXX
Status: [Diagnóstico atual]
Ação: [O que está a ser feito]
ETA: [Previsão de resolução]
```

**Resolução:**
```
🟢 RESOLVIDO - RB-XXX
Duração: [X minutos]
Causa: [Breve descrição]
Próximos passos: [Postmortem se necessário]
```

---

## 7. PREVENÇÃO E MELHORIAS

### 7.1 Ações Preventivas

- [ ] *Monitorização adicional para detetar mais cedo*
- [ ] *Alertas mais granulares*
- [ ] *Automação de resposta*
- [ ] *Testes de resiliência*

### 7.2 Métricas de Eficácia

| Métrica | Target | Como Medir |
|---------|--------|------------|
| MTTR (Mean Time To Recovery) | < 30 min | Tempo alerta → resolvido |
| MTTD (Mean Time To Detect) | < 5 min | Tempo incidente → alerta |
| % Resolvido sem escalada | > 80% | Runbooks bem documentados |

---

## 8. HISTÓRICO

| Data | Versão | Alteração | Autor |
|------|--------|-----------|-------|
| *YYYY-MM-DD* | *v1.0* | *Criação* | *Nome* |
| *YYYY-MM-DD* | *v1.1* | *Adicionada Solução 2* | *Nome* |

---

## 9. REFERÊNCIAS

- [[26_Runbooks/INDEX]] ← Outros runbooks
- [[27_Postmortems/INDEX]] → Postmortems relacionados
- [[TEMPLATE_INCIDENTE]] → Template para report de incidente
- [[RB-XXX_NOME_DO_RUNBOOK]] → Runbook relacionado

---

**⚠️ NOTA:** Este runbook deve ser testado trimestralmente com drill exercises.
