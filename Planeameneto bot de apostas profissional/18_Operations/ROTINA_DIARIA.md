# ROTINA_DIARIA — Checklist Operacional Detalhado

**ID:** `OPS-001` | **Fase:** #phase/4 | **Owner:** Operations Lead | **Status:** #status/active

---

## 1. OBJETIVO

Estabelecer uma rotina operacional diária estruturada que garanta a execução consistente do sistema de value betting NBA, desde a ingestão de dados até à execução de apostas, passando pelo monitoramento de circuit breakers e métricas de performance. Esta rotina assegura que o sistema opera dentro dos parâmetros definidos: batch síncrono com latência de 2-5 segundos, horários fixos de execução (08:00 ingestão, 10:00/12:00/14:00/16:00 motor de decisão), e respeitando os limites de risco (drawdown > 15%, 7 perdas consecutivas, feed offline > 5 minutos).

---

## 2. ESTRUTURA DO DIA OPERACIONAL

O dia operacional está dividido em 4 fases principais, alinhadas com a arquitetura batch síncrona do sistema:

| Fase | Horário (UTC) | Atividade Principal | Responsável |
|------|---------------|---------------------|-------------|
| Ingestão | 08:00 | Coleta e processamento de dados históricos e odds | Pipeline Automático |
| Decisão 1 | 10:00 | Motor de decisão - primeiro batch de sinais | Motor de Decisão |
| Decisão 2 | 12:00 | Motor de decisão - segundo batch de sinais | Motor de Decisão |
| Decisão 3 | 14:00 | Motor de decisão - terceiro batch de sinais | Motor de Decisão |
| Decisão 4 | 16:00 | Motor de decisão - quarto batch de sinais | Motor de Decisão |
| Execução | Conforme sinais | Execução manual de apostas via Telegram | Operador |
| Reconciliação | Após jogos | Verificação de resultados e atualização de PnL | Operador |

---

## 3. ROTINA DE ABERTURA (07:45 - 08:15 UTC)

### 3.1. Verificação de Infraestrutura (07:45 - 07:55)

**Objetivo:** Garantir que todos os componentes do sistema estão operacionais antes do início da ingestão.

**Checklist:**
- [ ] Aceder ao dashboard Grafana (URL: `https://grafana.seusistema.com`)
- [ ] Verificar status do VPS: CPU < 70%, RAM < 80%, Disco < 85%
- [ ] Confirmar que PostgreSQL está online: `systemctl status postgresql`
- [ ] Confirmar que Redis está online: `systemctl status redis`
- [ ] Verificar que containers Docker estão a correr: `docker ps`
- [ ] Confirmar que não há alertas críticos (P1) pendentes no sistema de alertas

**Em caso de problema:**
- Se VPS offline: Contactar fornecedor de VPS imediatamente
- Se PostgreSQL down: Executar `sudo systemctl restart postgresql` e verificar logs
- Se Redis down: Executar `sudo systemctl restart redis` e verificar logs
- Se containers down: Executar `docker-compose up -d` no diretório do projeto

### 3.2. Verificação de Circuit Breakers (07:55 - 08:00)

**Objetivo:** Confirmar que nenhum circuit breaker está ativado antes de iniciar operações.

**Circuit Breakers do Sistema:**
1. **Alpha (Drawdown):** Ativado quando drawdown > 15%
2. **Beta (Perdas Consecutivas):** Ativado quando 7 perdas consecutivas
3. **Gamma (Feed Offline):** Ativado quando feed offline > 5 minutos
4. **Delta (Performance):** Ativado quando ROI < -5% nos últimos 30 dias

**Checklist:**
- [ ] Consultar tabela `circuit_breakers` no PostgreSQL
- [ ] Verificar coluna `status` de cada circuit breaker (deve ser "INACTIVE")
- [ ] Se algum circuit breaker estiver "ACTIVE":
  - [ ] Identificar causa raiz consultando coluna `trigger_reason`
  - [ ] Verificar se condição de trigger ainda persiste
  - [ ] Se condição resolvida, executar procedimento de reset (ver SOP-004)
  - [ ] Se condição persiste, NÃO prosseguir com operações e notificar gestor de risco

### 3.3. Verificação de Pipeline de Dados (08:00 - 08:05)

**Objetivo:** Confirmar que o pipeline de ingestão de dados iniciou corretamente às 08:00.

**Checklist:**
- [ ] Verificar logs do pipeline: `docker logs data_pipeline --tail 50`
- [ ] Confirmar que job de ingestão iniciou às 08:00 UTC
- [ ] Verificar que dados de odds estão a ser recebidos (Betfair API)
- [ ] Confirmar que dados históricos estão a ser atualizados (NBA API)
- [ ] Verificar que não há erros de validação nos logs

**Métricas a verificar:**
- Taxa de sucesso de ingestão > 99%
- Latência de ingestão < 30 segundos
- Número de registos inseridos > 0

**Em caso de erro:**
- Se Betfair API falhar: Verificar token de sessão, verificar rate limits
- Se NBA API falhar: Verificar quota de API, verificar status do serviço
- Se erro de validação: Consultar logs específicos, verificar schema de dados

### 3.4. Verificação de Modelo (08:05 - 08:10)

**Objetivo:** Confirmar que o modelo de ML está carregado e pronto para inferência.

**Checklist:**
- [ ] Verificar logs do serviço de predição: `docker logs prediction_service --tail 30`
- [ ] Confirmar que modelo carregou com sucesso (mensagem "Model loaded successfully")
- [ ] Verificar versão do modelo carregado (deve corresponder à versão em produção)
- [ ] Executar health check do endpoint de predição: `curl -X POST http://localhost:8000/health`
- [ ] Verificar que latência de predição está dentro do esperado (< 200ms)

**Em caso de problema:**
- Se modelo não carregou: Verificar ficheiro do modelo, verificar memória disponível
- Se health check falhar: Reiniciar serviço de predição
- Se latência alta: Verificar carga do sistema, considerar escalonamento

### 3.5. Verificação de Banca e Liquidez (08:10 - 08:15)

**Objetivo:** Confirmar que há banca disponível na Betfair para executar apostas do dia.

**Checklist:**
- [ ] Aceder à conta Betfair (Exchange)
- [ ] Verificar saldo disponível (deve ser > stake diário previsto * 2)
- [ ] Confirmar que não há restrições na conta
- [ ] Verificar liquidez dos mercados principais (NBA)
- [ ] Confirmar que API da Betfair está acessível

**Thresholds:**
- Saldo mínimo: 500 EUR (ajustar conforme stake)
- Liquidez mínima por mercado: 10.000 EUR
- Taxa de comissão atual: verificar se houve alterações

---

## 4. ROTINA DURANTE EXECUÇÃO (10:00 - 18:00 UTC)

### 4.1. Monitoramento do Motor de Decisão (10:00, 12:00, 14:00, 16:00)

**Objetivo:** Garantir que o motor de decisão executa corretamente nos horários programados.

**Procedimento para cada execução (5 minutos antes):**
- [ ] Verificar que sistema está online
- [ ] Confirmar que não há circuit breakers ativos
- [ ] Verificar que dados de odds estão atualizados (última atualização < 10 minutos)

**Durante execução:**
- [ ] Monitorizar logs do motor de decisão: `docker logs decision_engine --follow`
- [ ] Verificar número de sinais gerados (esperado: 5-20 sinais por execução)
- [ ] Confirmar que sinais são enviados para Telegram
- [ ] Verificar latência de geração (esperado: 2-5 segundos por batch)

**Após execução:**
- [ ] Verificar que não houve erros nos logs
- [ ] Confirmar que sinais foram persistidos na base de dados
- [ ] Verificar métricas de qualidade dos sinais (CLV médio, edge médio)

### 4.2. Execução Manual de Apostas (Conforme sinais)

**Objetivo:** Executar apostas manualmente na Betfair com base nos sinais recebidos via Telegram.

**Procedimento detalhado (ver também SOP-001):**

1. **Receber notificação Telegram:**
   - [ ] Manter aplicação Telegram aberta e com som ativado
   - [ ] Configurar notificações prioritárias para o canal de sinais

2. **Validar sinal (tempo alvo: < 30 segundos):**
   - [ ] Ler odd mínima aceitável
   - [ ] Verificar timestamp do sinal (não aceitar sinais com > 2 minutos)
   - [ ] Identificar mercado e seleção

3. **Executar aposta na Betfair:**
   - [ ] Abrir Betfair Exchange
   - [ ] Procurar mercado indicado
   - [ ] Verificar odd atual >= odd mínima
   - [ ] Verificar liquidez suficiente (volume > stake * 1.5)
   - [ ] Inserir stake exata (não arredondar!)
   - [ ] Confirmar aposta

4. **Confirmar no Telegram:**
   - [ ] Enviar `/confirm <signal_id>` no Telegram
   - [ ] Registar odd obtida se diferente da sinalizada
   - [ ] Tirar screenshot (opcional mas recomendado)

5. **Documentar exceções:**
   - [ ] Se odd < mínima: Enviar `/skip <id> reason:odd_moved`
   - [ ] Se erro na Betfair: Tentar novamente em 30s, notificar se persistir
   - [ ] Se sinal expirou: NÃO apostar, sinal inválido

### 4.3. Monitoramento Contínuo de Circuit Breakers

**Objetivo:** Detectar ativação de circuit breakers em tempo real e tomar ação apropriada.

**Checklist (verificar a cada 30 minutos):**
- [ ] Consultar dashboard de circuit breakers
- [ ] Verificar drawdown atual (não deve exceder 15%)
- [ ] Verificar sequência de perdas (não deve exceder 7)
- [ ] Verificar status do feed (não deve estar offline > 5 minutos)
- [ ] Verificar ROI dos últimos 30 dias (não deve ser < -5%)

**Se circuit breaker ativado:**
- [ ] Identificar qual circuit breaker disparou
- [ ] Parar imediatamente execução de novas apostas
- [ ] Executar SOP-004 (Resposta a Circuit Breaker)
- [ ] Notificar gestor de risco se severidade P1 ou P2

---

## 5. ROTINA DE FECHO (18:00 - 19:00 UTC)

### 5.1. Reconciliação de Apostas (18:00 - 18:30)

**Objetivo:** Garantir que todas as apostas executadas estão reconciliadas com os sinais gerados.

**Checklist:**
- [ ] Exportar lista de sinais gerados do dia (tabela `signals`)
- [ ] Exportar lista de apostas executadas (tabela `bets`)
- [ ] Comparar as duas listas:
  - [ ] Sinais sem aposta correspondente: investigar motivo
  - [ ] Apostas sem sinal correspondente: verificar se é aposta manual autorizada
  - [ ] Discrepâncias de odd: documentar slippage
- [ ] Verificar resultados dos jogos do dia (NBA API)
- [ ] Atualizar status das apostas (PENDING → WON/LOST/PUSH)
- [ ] Calcular PnL do dia

**Métricas a calcular:**
- Número de apostas executadas
- Taxa de execução (apostas / sinais)
- PnL do dia
- ROI do dia
- Slippage médio
- CLV médio

### 5.2. Atualização de Métricas (18:30 - 18:45)

**Objetivo:** Atualizar todas as métricas de performance e risco.

**Checklist:**
- [ ] Atualizar dashboard de negócio (ROI, CLV, drawdown)
- [ ] Verificar drawdown atual (calcular desde o último high watermark)
- [ ] Verificar sequência de perdas (contar perdas consecutivas)
- [ ] Calcular Sharpe ratio dos últimos 30 dias
- [ ] Verificar taxa de acerto dos últimos 30 dias
- [ ] Atualizar gráficos de performance

**Thresholds de alerta:**
- Drawdown > 10%: Alerta P3
- Drawdown > 15%: Alerta P1 (circuit breaker Alpha)
- 5 perdas consecutivas: Alerta P3
- 7 perdas consecutivas: Alerta P1 (circuit breaker Beta)
- CLV negativo por 2 dias: Alerta P3
- CLV negativo por 3 dias: Alerta P2 (circuit breaker Gamma)

### 5.3. Verificação de Alertas Pendentes (18:45 - 18:55)

**Objetivo:** Garantir que não há alertas não resolvidos antes do fim do dia.

**Checklist:**
- [ ] Consultar sistema de alertas
- [ ] Verificar alertas em estado "TRIGGERED" ou "INVESTIGATING"
- [ ] Para cada alerta:
  - [ ] Confirmar que tem owner atribuído
  - [ ] Verificar se ação corretiva está em progresso
  - [ ] Se alerta crítico (P1/P2) sem ação: notificar gestor
- [ ] Confirmar que não há alertas falsos positivos

### 5.4. Preparação do Relatório Diário (18:55 - 19:00)

**Objetivo:** Criar resumo do dia para arquivo e possível partilha com stakeholders.

**Conteúdo do relatório:**
- [ ] Resumo de operações: número de sinais, apostas executadas
- [ ] Performance financeira: PnL, ROI
- [ ] Métricas de qualidade: CLV, slippage, taxa de acerto
- [ ] Status de circuit breakers
- [ ] Alertas e incidentes do dia
- [ ] Anomalias observadas
- [ ] Tarefas pendentes para o dia seguinte

**Checklist:**
- [ ] Preencher template de daily note (ver 99_Templates/TEMPLATE_DAILY)
- [ ] Arquivar relatório no sistema de documentação
- [ ] Enviar resumo para canal ops_handoff (se houver turnover)

---

## 6. ROTINA SEMANAL (Segunda-feira, 10:00 - 11:00 UTC)

### 6.1. Revisão de Performance Semanal

**Objetivo:** Analisar tendências de performance e identificar áreas de melhoria.

**Checklist:**
- [ ] Calcular ROI semanal
- [ ] Calcular CLV médio semanal
- [ ] Calcular Sharpe ratio semanal
- [ ] Comparar com objetivos semanais
- [ ] Identificar dias de performance pobre e investigar causas

### 6.2. Análise de Modelo

**Objetivo:** Avaliar se o modelo precisa de retreino.

**Checklist:**
- [ ] Verificar AUC do modelo nos últimos 7 dias
- [ ] Verificar drift de predições (comparar com distribuição histórica)
- [ ] Analisar calibração do modelo (reliability diagrams)
- [ ] Se AUC < 0.55 ou drift significativo: agendar retreino (ver SOP-005)

### 6.3. Análise de Slippage

**Objetivo:** Comparar slippage real com slippage esperado.

**Checklist:**
- [ ] Calcular slippage médio da semana
- [ ] Comparar com slippage esperado (definido em backtesting)
- [ ] Se slippage real > slippage esperado + 1%: investigar causas
- [ ] Possíveis causas: latência de execução, liquidez insuficiente, mercado ineficiente

### 6.4. Revisão de Circuit Breakers

**Objetivo:** Analisar circuit breakers disparados e melhorar thresholds.

**Checklist:**
- [ ] Listar todos os circuit breakers disparados na semana
- [ ] Analisar causas raiz de cada disparo
- [ ] Avaliar se thresholds são apropriados
- [ ] Se muitos falsos positivos: considerar ajuste de thresholds
- [ ] Se nenhum disparo em longo período: considerar se thresholds são demasiado permissivos

### 6.5. Atualização de Backlog

**Objetivo:** Manter backlog de melhorias atualizado.

**Checklist:**
- [ ] Adicionar melhorias identificadas durante a semana
- [ ] Priorizar itens do backlog
- [ ] Atribuir owners e deadlines
- [ ] Comunicar backlog à equipa

---

## 7. ROTINA MENSAL (Última sexta do mês, 14:00 - 16:00 UTC)

### 7.1. Revisão de Performance Mensal

**Objetivo:** Avaliar performance global e alinhar com objetivos de negócio.

**Checklist:**
- [ ] Calcular ROI mensal
- [ ] Calcular drawdown máximo mensal
- [ ] Calcular Sharpe ratio mensal
- [ ] Comparar com objetivos mensais
- [ ] Preparar relatório executivo para stakeholders

### 7.2. Auditoria de Sistema

**Objetivo:** Garantir que todos os componentes do sistema estão a funcionar corretamente.

**Checklist:**
- [ ] Verificar integridade da base de dados
- [ ] Verificar backups automáticos estão a funcionar
- [ ] Verificar que todos os alertas estão configurados corretamente
- [ ] Verificar que documentação está atualizada
- [ ] Verificar que secrets estão atualizados (ver SOP-010)

### 7.3. Retrospectiva Operacional

**Objetivo:** Identificar lições aprendidas e oportunidades de melhoria.

**Checklist:**
- [ ] Revisar incidentes do mês
- [ ] Revisar postmortems criados
- [ ] Identificar padrões de problemas
- [ ] Propor melhorias de processo
- [ ] Atualizar SOPs e runbooks conforme necessário

---

## 8. PROCEDIMENTOS DE EMERGÊNCIA

### 8.1. Se Sistema Offline Durante Horário de Operação

**Passos imediatos (1-2 minutos):**
1. Verificar status do VPS: `ping <ip>`
2. Se VPS offline: Contactar fornecedor imediatamente
3. Se VPS online mas serviços down: Reiniciar serviços críticos
4. Notificar equipa via Telegram canal ops_alertas
5. Executar runbook RB-001 (Downtime)

### 8.2. Se Feed de Odds Offline

**Passos imediatos (1-2 minutos):**
1. Verificar conexão Betfair API: `curl -I https://api.betfair.com`
2. Verificar token de sessão: renovar se expirado
3. Verificar rate limits: esperar se necessário
4. Circuit breaker Delta ativado automaticamente
5. Notificar: "Feed offline, apostas pausadas"
6. Executar runbook RB-001 (Feed Offline)

### 8.3. Se Modelo Produz Predições Estranhas

**Passos imediatos (1-2 minutos):**
1. Verificar logs do serviço de predição
2. Verificar se modelo carregou corretamente
3. Analisar predições: verificar se estão fora de [0.05, 0.95]
4. Fallback: usar modelo anterior (registry)
5. Se falha persistir: shadow mode até resolução
6. Executar runbook RB-002 (Modelo Valores Estranhos)

### 8.4. Se Drawdown Acelera (> 10% em 48h)

**Passos imediatos (1-2 minutos):**
1. Verificar drawdown atual
2. Verificar sequência de perdas
3. Se drawdown > 15%: circuit breaker Alpha ativado automaticamente
4. Parar imediatamente execução de novas apostas
5. Notificar gestor de risco
6. Executar runbook RB-008 (Drawdown Acelerado)
7. Preparar postmortem se drawdown > 20%

---

## 9. MÉTRICAS DE SUCESSO DA ROTINA

| Métrica | Threshold | Ação se não cumprido |
|---------|-----------|---------------------|
| Taxa de execução de checklist diário | 100% | Investigar causa, reforçar treinamento |
| Tempo de resposta a sinais | < 2 minutos | Investigar latência, otimizar processo |
| Taxa de reconciliação de apostas | 100% | Investigar discrepâncias |
| Número de alertas não resolvidos ao fim do dia | 0 | Escalar para gestor |
| Tempo de preparação do relatório diário | < 15 minutos | Otimizar template |
| Frequência de revisão semanal | 100% | Agendar reminder automático |

---

## 10. BACKLOG

- [ ] Criar versão impressa do checklist para operações offline
- [ ] Automatizar checks que forem possíveis (health checks automáticos)
- [ ] Documentar processo de handoff entre operadores (já em COMUNICACAO_EQIPA)
- [ ] Criar dashboard específico para rotina diária (status de cada checkpoint)
- [ ] Implementar reminders automáticos para checkpoints críticos
- [ ] Criar versão mobile-friendly do checklist

---

## 11. LINKS CRUZADOS

- [[18_Operations/INDEX]] ← Secção mãe
- [[25_SOPs/INDEX]] → Procedimentos detalhados
- [[26_Runbooks/INDEX]] → Runbooks de incidentes
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Detalhes dos circuit breakers
- [[10_Monitoring/DASHBOARD_NEGOCIO]] → Dashboard de métricas
- [[19_Telegram_System/INDEX]] → Sistema de sinais
