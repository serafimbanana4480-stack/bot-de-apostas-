# SOP_ROTINA_FECHO — Procedimento Operacional Padrão

**ID:** `SOP-002` | **Fase:** #phase/4 | **Owner:** Operations Lead | **Status:** #status/active
**Última Revisão:** 2024-05-13 | **Próxima Revisão:** 2024-08-13

---

## 1. OBJETIVO

Estabelecer um procedimento padronizado para o fecho do dia operacional do sistema de value betting NBA, garantindo que todas as apostas são reconciliadas, as métricas são atualizadas, os alertas são verificados, e o sistema fica preparado para o dia seguinte. Este SOP assegura a integridade dos dados financeiros, a deteção atempada de anomalias, e a continuidade das operações.

---

## 2. APLICAÇÃO

**Quando executar:**
- Diariamente, após o último jogo NBA do dia (tipicamente entre 18:00 e 19:00 UTC)
- Em todos os dias em que houve execução do motor de decisão
- Independente de ter havido ou não apostas executadas

**Responsável:**
- Operador do turno do dia
- Se houver múltiplos operadores: o operador responsável pelo período 16:00-19:00 UTC

**Duração estimada:**
- 45-60 minutos em condições normais
- 90-120 minutos se houver anomalias ou discrepâncias

---

## 3. PRÉ-REQUISITOS

### 3.1. Acesso e Ferramentas
- [ ] Acesso ao dashboard Grafana
- [ ] Acesso à base de dados PostgreSQL
- [ ] Acesso à conta Betfair Exchange
- [ ] Acesso ao canal Telegram ops_handoff
- [ ] Acesso ao sistema de documentação (Obsidian)
- [ ] Template de daily note (99_Templates/TEMPLATE_DAILY)

### 3.2. Conhecimentos Necessários
- Compreensão básica de SQL para queries de reconciliação
- Familiaridade com a interface da Betfair Exchange
- Conhecimento dos circuit breakers e seus thresholds
- Capacidade de interpretar métricas de performance (ROI, CLV, drawdown)

### 3.3. Estado do Sistema
- [ ] Motor de decisão completou todas as execuções do dia (10:00, 12:00, 14:00, 16:00)
- [ ] Todos os jogos do dia terminaram ou estão em fase final
- [ ] Pipeline de dados não está a executar jobs críticos durante o fecho

---

## 4. PROCEDIMENTO DETALHADO

### 4.1. Fase 1: Preparação (18:00 - 18:05 UTC)

**Objetivo:** Preparar o ambiente e garantir que não há interrupções durante o fecho.

**Passos:**

1. **Verificar horário:**
   - Confirmar que é apropriado iniciar o fecho (último jogo terminou ou em fase final)
   - Se há jogos em curso, decidir se adiar fecho ou executar fecho parcial

2. **Notificar equipa:**
   - Enviar mensagem no canal ops_geral: "Iniciando fecho do dia às [hora]"
   - Se houver turnover, notificar operador do turno seguinte

3. **Preparar ambiente:**
   - Abrir todas as ferramentas necessárias (Grafana, PostgreSQL client, Betfair, Telegram)
   - Abrir template de daily note
   - Preparar folha de cálculo para reconciliação (se aplicável)

4. **Verificar estado do sistema:**
   - Confirmar que não há jobs críticos a correr
   - Verificar que não há alertas P1 em estado TRIGGERED
   - Se houver alerta P1: priorizar resolução antes do fecho

### 4.2. Fase 2: Reconciliação de Apostas (18:05 - 18:30 UTC)

**Objetivo:** Garantir que todas as apostas executadas estão reconciliadas com os sinais gerados.

#### 4.2.1. Exportar Dados

**Passos:**

1. **Exportar sinais do dia:**
   ```sql
   SELECT 
       signal_id,
       game_id,
       market,
       selection,
       predicted_odds,
       min_odds,
       edge,
       clv,
       timestamp_utc,
       status
   FROM signals
   WHERE DATE(timestamp_utc) = CURRENT_DATE
   ORDER BY timestamp_utc;
   ```
   - Guardar resultado em ficheiro CSV ou exportar para folha de cálculo

2. **Exportar apostas do dia:**
   ```sql
   SELECT 
       bet_id,
       signal_id,
       market,
       selection,
       stake,
       odds_obtained,
       timestamp_utc,
       status,
       result,
       pnl
   FROM bets
   WHERE DATE(timestamp_utc) = CURRENT_DATE
   ORDER BY timestamp_utc;
   ```
   - Guardar resultado em ficheiro CSV ou exportar para folha de cálculo

3. **Exportar resultados dos jogos:**
   ```sql
   SELECT 
       game_id,
       home_team,
       away_team,
       final_score,
       game_date,
       status
   FROM games
   WHERE game_date = CURRENT_DATE
   ORDER BY game_date;
   ```

#### 4.2.2. Comparar Sinais vs Apostas

**Passos:**

1. **Criar tabela de comparação:**
   - Colunas: signal_id, tem_aposta (SIM/NÃO), bet_id, status_sinal, status_aposta

2. **Identificar sinais sem aposta:**
   - Para cada sinal, verificar se existe aposta correspondente (pelo signal_id)
   - Se não existe aposta:
     - [ ] Verificar se sinal foi enviado para Telegram
     - [ ] Verificar se operador recebeu notificação
     - [ ] Verificar se operador respondeu com /skip ou /confirm
     - [ ] Investigar motivo: odd moveu? erro Betfair? operador falhou?
     - [ ] Documentar motivo na tabela de comparação

3. **Identificar apostas sem sinal:**
   - Para cada aposta, verificar se existe sinal correspondente
   - Se não existe sinal:
     - [ ] Verificar se é aposta manual autorizada
     - [ ] Verificar se é erro de sistema (aposta duplicada, etc.)
     - [ ] Documentar motivo na tabela de comparação

4. **Identificar discrepâncias de odd:**
   - Para cada aposta, comparar odds_obtained com min_odds do sinal
   - Se odds_obtained < min_odds:
     - [ ] Verificar se operador documentou razão
     - [ ] Calcular slippage (min_odds - odds_obtained)
     - [ ] Se slippage > 3%: marcar para investigação
   - Se odds_obtained > min_odds:
     - [ ] Documentar como slippage positivo (raro mas possível)

#### 4.2.3. Atualizar Resultados

**Passos:**

1. **Atualizar status das apostas:**
   - Para cada aposta com status PENDING:
     - [ ] Verificar resultado do jogo na NBA API
     - [ ] Atualizar status para WON, LOST, ou PUSH
     - [ ] Calcular PnL:
       - WON: PnL = stake * (odds_obtained - 1) - comissão
       - LOST: PnL = -stake
       - PUSH: PnL = 0

2. **Atualizar status dos sinais:**
   - Para cada sinal:
     - [ ] Se tem aposta associada: status = EXECUTED
     - [ ] Se não tem aposta e foi skip: status = SKIPPED
     - [ ] Se não tem aposta e não foi skip: status = MISSED

3. **Verificar integridade:**
   - [ ] Contar total de sinais do dia
   - [ ] Contar total de apostas do dia
   - [ ] Contar sinais EXECUTED, SKIPPED, MISSED
   - [ ] Verificar que EXECUTED + SKIPPED + MISSED = total de sinais

#### 4.2.4. Documentar Anomalias

**Passos:**

1. **Lista de anomalias:**
   - Sinais sem aposta não justificados
   - Apostas sem sinal não autorizadas
   - Discrepâncias de odd > 3%
   - Apostas com status incorreto
   - Resultados de jogos inconsistentes

2. **Para cada anomalia:**
   - [ ] Descrever anomalia em detalhe
   - [ ] Identificar causa raiz (se possível)
   - [ ] Determinar impacto financeiro (se aplicável)
   - [ ] Propor ação corretiva
   - [ ] Atribuir responsável para ação corretiva
   - [ ] Definir deadline para ação corretiva

3. **Documentar em daily note:**
   - Criar secção "Anomalias do Dia"
   - Listar todas as anomalias identificadas
   - Incluir referências para ações corretivas

### 4.3. Fase 3: Atualização de Métricas (18:30 - 18:45 UTC)

**Objetivo:** Calcular e atualizar todas as métricas de performance e risco.

#### 4.3.1. Métricas Financeiras do Dia

**Passos:**

1. **Calcular PnL do dia:**
   ```sql
   SELECT 
       SUM(CASE WHEN result = 'WON' THEN pnl ELSE 0 END) as total_won,
       SUM(CASE WHEN result = 'LOST' THEN pnl ELSE 0 END) as total_lost,
       SUM(CASE WHEN result = 'PUSH' THEN pnl ELSE 0 END) as total_push,
       SUM(pnl) as total_pnl
   FROM bets
   WHERE DATE(timestamp_utc) = CURRENT_DATE;
   ```

2. **Calcular ROI do dia:**
   - ROI = (Total PnL / Total Stake) * 100
   - Total Stake = soma de todas as stakes do dia

3. **Calcular taxa de acerto do dia:**
   - Taxa de acerto = (Número de apostas WON / Total de apostas) * 100

4. **Documentar em daily note:**
   - PnL do dia
   - ROI do dia
   - Taxa de acerto do dia
   - Número de apostas
   - Stake total

#### 4.3.2. Métricas de Qualidade do Dia

**Passos:**

1. **Calcular CLV médio do dia:**
   ```sql
   SELECT AVG(clv) as avg_clv
   FROM signals
   WHERE DATE(timestamp_utc) = CURRENT_DATE
   AND status = 'EXECUTED';
   ```

2. **Calcular edge médio do dia:**
   ```sql
   SELECT AVG(edge) as avg_edge
   FROM signals
   WHERE DATE(timestamp_utc) = CURRENT_DATE
   AND status = 'EXECUTED';
   ```

3. **Calcular slippage médio do dia:**
   - Para cada aposta: slippage = (min_odds - odds_obtained) / min_odds
   - Slippage médio = média de todos os slippages

4. **Calcular taxa de execução:**
   - Taxa de execução = (Número de apostas / Número de sinais) * 100

5. **Documentar em daily note:**
   - CLV médio do dia
   - Edge médio do dia
   - Slippage médio do dia
   - Taxa de execução

#### 4.3.3. Métricas Acumuladas (30 dias)

**Passos:**

1. **Calcular drawdown atual:**
   - Identificar high watermark máximo nos últimos 30 dias
   - Calcular drawdown = (High Watermark - Banca Atual) / High Watermark
   - Documentar drawdown atual e drawdown máximo dos últimos 30 dias

2. **Calcular sequência de perdas:**
   - Contar perdas consecutivas nos últimos 30 dias
   - Documentar sequência atual e sequência máxima

3. **Calcular ROI dos últimos 30 dias:**
   ```sql
   SELECT 
       SUM(pnl) as total_pnl_30d,
       SUM(stake) as total_stake_30d
   FROM bets
   WHERE timestamp_utc >= CURRENT_DATE - INTERVAL '30 days';
   ```
   - ROI_30d = (Total PnL / Total Stake) * 100

4. **Calcular Sharpe ratio dos últimos 30 dias:**
   - Calcular retorno diário médio
   - Calcular desvio padrão dos retornos diários
   - Sharpe = (Retorno Médio - Taxa Livre de Risco) / Desvio Padrão
   - Taxa livre de risco: assumir 2% anual (~0.0055% diário)

5. **Documentar em daily note:**
   - Drawdown atual
   - Drawdown máximo 30 dias
   - Sequência de perdas atual
   - Sequência de perdas máxima
   - ROI 30 dias
   - Sharpe ratio 30 dias

#### 4.3.4. Verificar Thresholds de Alerta

**Passos:**

1. **Verificar drawdown:**
   - [ ] Se drawdown > 10%: Alerta P3 (já deve ter disparado)
   - [ ] Se drawdown > 15%: Alerta P1 (circuit breaker Alpha)
   - [ ] Se drawdown > 20%: Crítico - requer ação imediata

2. **Verificar sequência de perdas:**
   - [ ] Se 5 perdas consecutivas: Alerta P3
   - [ ] Se 7 perdas consecutivas: Alerta P1 (circuit breaker Beta)

3. **Verificar CLV:**
   - [ ] Se CLV negativo por 2 dias: Alerta P3
   - [ ] Se CLV negativo por 3 dias: Alerta P2 (circuit breaker Gamma)

4. **Verificar ROI 30 dias:**
   - [ ] Se ROI < -5%: Alerta P2 (circuit breaker Delta)

5. **Documentar alertas ativos:**
   - Listar todos os alertas que estão atualmente ativos
   - Indicar severidade de cada alerta
   - Indicar ação tomada ou planeada

### 4.4. Fase 4: Verificação de Alertas (18:45 - 18:55 UTC)

**Objetivo:** Garantir que não há alertas não resolvidos antes do fim do dia.

**Passos:**

1. **Consultar sistema de alertas:**
   - Aceder ao dashboard de alertas
   - Filtrar por data = hoje
   - Ordenar por severidade (P1 primeiro)

2. **Verificar cada alerta:**
   Para cada alerta em estado TRIGGERED ou INVESTIGATING:
   - [ ] Confirmar que tem owner atribuído
   - [ ] Verificar timestamp de criação
   - [ ] Verificar se tempo de resposta está dentro do SLA
   - [ ] Verificar se ação corretiva está em progresso
   - [ ] Se alerta P1 ou P2 sem ação: notificar gestor imediatamente

3. **Verificar alertas falsos positivos:**
   - Para cada alerta marcado como FALSE_POSITIVE:
   - [ ] Verificar se justificação está documentada
   - [ ] Verificar se é necessário ajustar thresholds

4. **Documentar em daily note:**
   - Número de alertas do dia
   - Número de alertas resolvidos
   - Número de alertas pendentes
   - Alertas críticos (P1/P2) pendentes

### 4.5. Fase 5: Preparação do Relatório Diário (18:55 - 19:00 UTC)

**Objetivo:** Criar resumo do dia para arquivo e possível partilha.

**Passos:**

1. **Preencher template de daily note:**
   - Secção "Resumo Executivo":
     - Número de sinais gerados
     - Número de apostas executadas
     - PnL do dia
     - ROI do dia
     - Status geral (BOM/ACEITÁVEL/CRÍTICO)

   - Secção "Métricas Detalhadas":
     - Métricas financeiras (PnL, ROI, stake, taxa de acerto)
     - Métricas de qualidade (CLV, edge, slippage, taxa de execução)
     - Métricas de risco (drawdown, sequência de perdas)

   - Secção "Anomalias":
     - Lista de anomalias identificadas
     - Causa raiz de cada anomalia
     - Ação corretiva planeada

   - Secção "Alertas":
     - Alertas disparados durante o dia
     - Status de cada alerta
     - Ações tomadas

   - Secção "Circuit Breakers":
     - Status de cada circuit breaker
     - Circuit breakers disparados (se houver)

   - Secção "Tarefas Pendentes":
     - Tarefas não concluídas durante o dia
     - Prioridade de cada tarefa
     - Deadline para conclusão

   - Secção "Observações":
     - Quaisquer observações relevantes
     - Ideias para melhoria
     - Lições aprendidas

2. **Arquivar relatório:**
   - Guardar daily note em diretório apropriado
   - Atualizar índice de daily notes
   - Enviar link para canal ops_handoff (se aplicável)

3. **Preparar resumo para stakeholders (se aplicável):**
   - Se houver subscritores ou stakeholders externos
   - Preparar resumo simplificado (sem detalhes técnicos)
   - Enviar via e-mail ou canal apropriado

### 4.6. Fase 6: Handoff (19:00 UTC)

**Objetivo:** Passar informação para o operador do turno seguinte ou preparar sistema para o dia seguinte.

**Passos:**

1. **Se houver turnover:**
   - [ ] Executar procedimento de handoff (ver COMUNICACAO_EQIPA)
   - [ ] Enviar handoff report para canal ops_handoff
   - [ ] Reunir brevemente com operador seguinte (10 minutos)
   - [ ] Transferir responsabilidade formalmente

2. **Se não houver turnover (fim de semana):**
   - [ ] Verificar que sistema está em estado estável
   - [ ] Confirmar que não há jobs críticos agendados para fora de horas
   - [ ] Verificar que monitorização está ativa
   - [ ] Configurar alertas para on-call (se aplicável)

3. **Finalizar:**
   - [ ] Enviar mensagem no canal ops_geral: "Fecho do dia concluído às [hora]"
   - [ ] Fechar todas as ferramentas
   - [ ] Sair do sistema (logout)

---

## 5. TABELAS DE REFERÊNCIA

### 5.1. Status de Sinais

| Status | Descrição | Ação Necessária |
|--------|-----------|-----------------|
| PENDING | Sinal gerado, aguardando execução | Nenhuma (processo normal) |
| EXECUTED | Aposta colocada com base no sinal | Nenhuma (processo normal) |
| SKIPPED | Sinal ignorado por operador | Verificar justificação |
| MISSED | Sinal não executado sem justificação | Investigar causa raiz |
| EXPIRED | Sinal expirou antes de execução | Investigar latência |

### 5.2. Status de Apostas

| Status | Descrição | Ação Necessária |
|--------|-----------|-----------------|
| PENDING | Aposta colocada, aguardando resultado | Aguardar resultado do jogo |
| WON | Aposta vencedora | Calcular PnL, atualizar métricas |
| LOST | Aposta perdedora | Calcular PnL, atualizar métricas |
| PUSH | Aposta reembolsada (empate) | Calcular PnL (0), atualizar métricas |
| VOID | Aposta anulada pela Betfair | Investigar motivo |

### 5.3. Thresholds de Alerta

| Métrica | Threshold P3 | Threshold P2 | Threshold P1 |
|---------|--------------|--------------|--------------|
| Drawdown | > 10% | > 12% | > 15% |
| Perdas consecutivas | 5 | 6 | 7 |
| CLV negativo (dias) | 2 | 3 | N/A |
| ROI 30 dias | < -3% | < -5% | N/A |
| Slippage médio | > 2% | > 3% | N/A |

### 5.4. Tempos Estimados por Fase

| Fase | Duração Normal | Duração com Anomalias |
|------|----------------|----------------------|
| Preparação | 5 minutos | 10 minutos |
| Reconciliação | 25 minutos | 60 minutos |
| Atualização de métricas | 15 minutos | 20 minutos |
| Verificação de alertas | 10 minutos | 20 minutos |
| Preparação do relatório | 5 minutos | 10 minutos |
| Handoff | 5 minutos | 10 minutos |
| **TOTAL** | **65 minutos** | **130 minutos** |

---

## 6. TROUBLESHOOTING

### 6.1. Problema: Reconciliação não fecha (número de sinais ≠ número de apostas + skips)

**Causas possíveis:**
- Sinais não enviados para Telegram
- Apostas não registadas na base de dados
- Erro na query de extração

**Resolução:**
1. Verificar logs do Telegram bot para confirmar que sinais foram enviados
2. Verificar logs do serviço de apostas para confirmar que apostas foram registadas
3. Re-executar queries com filtros diferentes (por timestamp, por game_id)
4. Se discrepância persistir: marcar como anomalia crítica e escalar

### 6.2. Problema: Resultados de jogos inconsistentes

**Causas possíveis:**
- NBA API com dados incorretos
- Jogo adiado ou cancelado
- Erro no parsing dos resultados

**Resolução:**
1. Verificar resultado em fonte alternativa (site oficial NBA, ESPN)
2. Verificar se jogo foi adiado ou cancelado
3. Se dados incorretos na API: reportar anomalia, atualizar manualmente
4. Se jogo adiado: marcar apostas como VOID, remover do cálculo de PnL do dia

### 6.3. Problema: Drawdown calculado incorretamente

**Causas possíveis:**
- High watermark incorreto
- Banca atual não atualizada
- Erro na fórmula de cálculo

**Resolução:**
1. Verificar high watermark máximo nos últimos 30 dias
2. Verificar banca atual na Betfair
3. Recalcular drawdown manualmente
4. Se erro na fórmula: corrigir query, atualizar documentação

### 6.4. Problema: Alerta não resolvido ao fim do dia

**Causas possíveis:**
- Owner não disponível
- Problema mais complexo do que esperado
- Falha de comunicação

**Resolução:**
1. Verificar se owner está disponível
2. Se owner não disponível: reatribuir a outro operador
3. Se problema complexo: escalar para gestor
4. Documentar no daily note, garantir que ação está planeada

---

## 7. CHECKLIST FINAL

Antes de considerar o fecho concluído, verificar:

- [ ] Todas as apostas do dia estão reconciliadas
- [ ] Todos os resultados estão atualizados
- [ ] PnL do dia está calculado corretamente
- [ ] Todas as métricas estão atualizadas
- [ ] Todos os alertas têm owner ou estão resolvidos
- [ ] Anomalias estão documentadas
- [ ] Daily note está preenchido
- [ ] Handoff foi executado (se aplicável)
- [ ] Sistema está em estado estável
- [ ] Equipa foi notificada do fim do fecho

---

## 8. MÉTRICAS DE SUCESSO

| Métrica | Threshold | Ação se não cumprido |
|---------|-----------|---------------------|
| Taxa de conclusão do fecho | 100% (diário) | Investigar causa, reforçar treinamento |
| Tempo de conclusão do fecho | < 75 minutos (normal) | Otimizar processo |
| Taxa de reconciliação | 100% | Investigar discrepâncias |
| Número de anomalias críticas | 0 | Escalar imediatamente |
| Taxa de daily notes preenchidos | 100% | Automatizar reminders |

---

## 9. RISCOS E MITIGAÇÃO

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|------------|
| Erro na reconciliação | Alto (PnL incorreto) | Baixa | Double-check por segundo operador |
| Falha de sistema durante fecho | Alto (dados perdidos) | Baixa | Executar backup antes do fecho |
| Anomalia não detetada | Médio | Média | Checklist detalhado |
| Handoff falhado | Médio | Baixa | Procedimento formal de handoff |
| Daily note não preenchido | Baixo | Baixa | Template obrigatório |

---

## 10. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
- [[18_Operations/ROTINA_DIARIA]] ← Rotina diária completa
- [[18_Operations/GESTAO_ALERTAS]] → Gestão de alertas
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Circuit breakers
- [[10_Monitoring/DASHBOARD_NEGOCIO]] → Dashboard de métricas
- [[99_Templates/TEMPLATE_DAILY]] → Template de daily note