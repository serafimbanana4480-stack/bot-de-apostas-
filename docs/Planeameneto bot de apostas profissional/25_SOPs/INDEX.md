# 25_SOPs — INDEX

**ID:** `SEC-25` | **Fase:** Todas | **Owner:** Operations Lead | **Status:** #status/active

---

## 1. OBJETIVO

Documentar Standard Operating Procedures (SOPs) para todas as operações críticas do sistema. SOPs garantem consistência, reduzem erros humanos, e permitem que qualquer operador qualificado execute tarefas críticas.

---

## 2. NOTAS FUNDAMENTAIS

- [[SOP-001_ABERTURA_DIARIA]] — Procedimento de abertura do sistema no início do dia
- [[SOP-002_FECHO_DIARIO]] — Procedimento de fecho do sistema no fim do dia
- [[SOP-003_VERIFICACAO_DADOS]] — Verificação de qualidade de dados antes de operação
- [[SOP-004_MONITORAMENTO_SINAIS]] — Monitorização de sinais gerados durante o dia
- [[SOP-005_RECONCILIACAO_APOSTAS]] — Reconciliação de apostas executadas vs sinais
- [[SOP-006_RESPONDER_ALERTA]] — Procedimento padrão para responder a alertas
- [[SOP-007_CIRCUIT_BREAKER]] — Procedimento quando circuit breaker é ativado
- [[SOP-008_BACKUP_MANUAL]] — Backup manual antes de alterações críticas
- [[SOP-009_DEPLOYMENT]] — Procedimento de deployment de nova versão
- [[SOP-010_ROLLBACK]] — Procedimento de rollback se deployment falhar

---

## 3. PRINCÍPIOS DE SOPs

1. **Checklist-based:** Cada SOP é um checklist passo-a-passo
2. **Verifiable:** Cada passo tem critério de verificação claro
3. **Time-bound:** Cada SOP tem tempo estimado de execução
4. **Owner-defined:** Cada SOP tem um owner responsável
5. **Versioned:** Alterações a SOPs são versionadas

---

## 4. SOPS CRÍTICOS (PRIORIDADE ALTA)

### SOP-001: Abertura Diária do Sistema
**Frequência:** Diária (antes do primeiro jogo)
**Tempo estimado:** 10 minutos
**Owner:** Operations Lead

**Checklist:**
- [ ] Verificar health check de todos os serviços (API, PostgreSQL, Redis, Prefect)
- [ ] Verificar que dados de NBA foram atualizados nas últimas 24h
- [ ] Verificar que odds estão atualizadas (última atualização < 30min)
- [ ] Verificar que Telegram Bot está online
- [ ] Verificar que não há circuit breakers ativos
- [ ] Enviar mensagem de "sistema pronto" para canal de operações
- [ ] Documentar status no log diário

**Critério de sucesso:** Todos os serviços healthy, dados atualizados, bot online.

---

### SOP-002: Fecho Diário do Sistema
**Frequência:** Diária (após último jogo)
**Tempo estimado:** 15 minutos
**Owner:** Operations Lead

**Checklist:**
- [ ] Verificar que todos os jogos do dia foram processados
- [ ] Executar reconciliação de apostas (sinais vs executadas)
- [ ] Gerar relatório diário (PnL, CLV, número de apostas)
- [ ] Verificar que backups automáticos foram executados
- [ ] Verificar que não há erros nos logs
- [ ] Enviar relatório diário para canal de operações
- [ ] Documentar status no log diário
- [ ] Se houver incidentes, criar postmortem draft

**Critério de sucesso:** Todos os jogos processados, reconciliação completa, backup OK.

---

### SOP-003: Verificação de Dados
**Frequência:** Antes de cada batch de modelação (2h)
**Tempo estimado:** 5 minutos
**Owner:** Data Engineer

**Checklist:**
- [ ] Verificar contagem de jogos hoje vs esperado (ex: 10 jogos NBA)
- [ ] Verificar % de valores null em features críticas (< 5%)
- [ ] Verificar que não há duplicados (game_id único)
- [ ] Verificar que timestamps são consistentes (nenhum futuro)
- [ ] Verificar que odds são razoáveis (não 0, não > 1000)
- [ ] Se houver anomalias, registrar alerta e pausar modelação

**Critério de sucesso:** Dados passam todas as validações, modelação pode prosseguir.

---

### SOP-004: Monitorização de Sinais
**Frequência:** Contínua durante dias de jogo
**Tempo estimado:** Ad-hoc (verificar a cada 30min)
**Owner:** Operations Lead

**Checklist:**
- [ ] Verificar que sinais estão sendo gerados (último sinal < 2h)
- [ ] Verificar edge médio dos sinais (deve ser > 2%)
- [ ] Verificar que Telegram Bot está enviando sinais
- [ ] Verificar que não há erros de execução
- [ ] Se houver pausa > 1h sem sinais, investigar

**Critério de sucesso:** Sinais sendo gerados e enviados consistentemente.

---

### SOP-005: Reconciliação de Apostas
**Frequência:** Diária (fecho)
**Tempo estimado:** 10 minutos
**Owner:** Risk Manager

**Checklist:**
- [ ] Contar sinais gerados no dia
- [ ] Contar apostas executadas no dia
- [ ] Calcular fill rate (deve ser > 80%)
- [ ] Calcular slippage médio (deve ser < 2%)
- [ ] Verificar stakes executadas vs stakes recomendados
- [ ] Se fill rate < 80%, investigar razões
- [ ] Se slippage > 2%, investigar execution

**Critério de sucesso:** Fill rate > 80%, slippage < 2%, reconciliação completa.

---

### SOP-006: Responder a Alerta
**Frequência:** Quando alerta é recebido
**Tempo estimado:** Variável (5-30min)
**Owner:** On-call Engineer

**Checklist:**
- [ ] Receber alerta (Telegram + email)
- [ ] Verificar severidade (CRITICAL, HIGH, MEDIUM)
- [ ] Se CRITICAL: responder em < 5 min
- [ ] Se HIGH: responder em < 30 min
- [ ] Se MEDIUM: responder em < 4h
- [ ] Investigar causa raiz usando logs/métricas
- [ ] Executar mitigação apropriada
- [ ] Documentar incidente em log
- [ ] Se necessário, escalar para on-call senior

**Critério de sucesso:** Alerta respondido dentro de SLA, mitigação executada.

---

### SOP-007: Circuit Breaker Ativado
**Frequência:** Quando circuit breaker é ativado
**Tempo estimado:** 15-30 minutos
**Owner:** Risk Manager + Operations Lead

**Checklist:**
- [ ] Receber notificação de circuit breaker (qual trigger)
- [ ] Identificar trigger (Alpha, Beta, Gamma, Delta, Epsilon, Zeta)
- [ ] Verificar estado do sistema (drawdown, perdas consecutivas, etc.)
- [ ] Executar ação de recovery específica do trigger
- [ ] Se trigger Alpha (drawdown > 15%): reduzir stakes 50%
- [ ] Se trigger Beta (5 perdas consecutivas): pausa 1h + revisão manual
- [ ] Se trigger Gamma (CLV 3d < 0%): pausa novas apostas
- [ ] Se trigger Delta (feed falha): sem apostas até feed OK
- [ ] Se trigger Epsilon (erro execução > 3x): paragem total
- [ ] Se trigger Zeta (exposição > 12%): rejeitar novos sinais
- [ ] Documentar incidente
- [ ] Notificar stakeholders

**Critério de sucesso:** Circuit breaker recuperado, sistema estável, incidente documentado.

---

## 5. BACKLOG DE SOPs

- [ ] SOP-008: Backup Manual (antes de alterações críticas)
- [ ] SOP-009: Deployment (nova versão)
- [ ] SOP-010: Rollback (se deployment falhar)
- [ ] SOP-011: Onboarding de Novo Operador
- [ ] SOP-012: Manutenção Semanal (limpeza de logs, etc.)
- [ ] SOP-013: Atualização de Modelos (retraining)
- [ ] SOP-014: Expansão para Novo Mercado
- [ ] SOP-015: Compliance Check (mensal)

---

## 6. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[26_Runbooks/INDEX]] → Runbooks para incidentes específicos
- [[18_Operations/INDEX]] → Operações diárias
- [[27_Postmortems/INDEX]] → Análise pós-incidente
