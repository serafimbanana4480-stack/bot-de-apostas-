# 18_Operations — INDEX

**ID:** `SEC-18` | **Fase:** #phase/1-15 | **Owner:** Operations Lead | **Status:** #status/active

---

## 1. OBJETIVO

Gerir o dia-a-dia do sistema: verificar sinais, executar apostas (Fase 1), monitorizar alertas, responder a incidentes, e garantir que o sistema opera conforme especificado 24/7.

---

## 2. NOTAS FUNDAMENTAIS

- [[ROTINA_DIARIA]] — Checklists de abertura e fecho de dia
- [[GESTAO_ALERTAS]] — Como responder a cada tipo de alerta
- [[COMUNICACAO_EQIPA]] — Canais, escalada, turnos
- [[DOCUMENTACAO_OPERACIONAL]] — Logs, daily notes, handovers
- [[MANUTENCAAO_PROGRAMADA]] — Janelas de manutenção, comunicação

---

## 3. ROTINA DIÁRIA (Fase 1-3: Manual)

### Abertura (1h antes do primeiro jogo)
- [ ] Verificar se o pipeline de dados correu esta manhã
- [ ] Verificar se as odds foram atualizadas nas últimas 2h
- [ ] Verificar se o modelo está ativo (health check)
- [ ] Verificar saldo da banca Betfair
- [ ] Abrir Telegram Bot e confirmar que está a enviar

### Durante os jogos
- [ ] Monitorizar Telegram para sinais
- [ ] Quando sinal chega: verificar odd, confirmar dentro de expiry
- [ ] Colocar aposta manualmente na Betfair
- [ ] Responder no Telegram com confirmação (comando /confirm)
- [ ] Registar aposta no sistema

### Fecho (após último jogo)
- [ ] Reconciliar todas as apostas do dia
- [ ] Verificar resultados e atualizar PnL
- [ ] Preencher daily note ([[99_Templates/TEMPLATE_DAILY]])
- [ ] Verificar alertas pendentes
- [ ] Preparar resumo para subscritores (se aplicável)

---

## 4. BACKLOG TÉCNICO

- [ ] Criar SOP de rotina diária (SOP-001)
- [ ] Criar runbook de resposta a alertas
- [ ] Configurar sistema de turnos (se equipa > 1)
- [ ] Implementar handover digital entre turnos

---

## 5. LINKS CRUZADOS

- [[00_Master_Index/INDEX]] ← Cérebro do sistema
- [[25_SOPs/INDEX]] → Procedimentos operacionais detalhados
- [[26_Runbooks/INDEX]] → Runbooks de incidentes
- [[19_Telegram_System/INDEX]] → Sistema de sinais e comunicação
