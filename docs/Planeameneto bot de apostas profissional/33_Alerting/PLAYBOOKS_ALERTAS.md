# Playbooks de Alertas — Procedimentos de Resposta

**ID:** `ALT-101` | **Fase:** #phase/2 | **Owner:** Operations Lead | **Status:** #status/draft

---

## 1. INTRODUÇÃO

Este documento contém playbooks detalhados para cada tipo de alerta. Um playbook é um guia passo-a-passo que descreve como diagnosticar, resolver e documentar um incidente. Playbooks devem ser seguidos rigorosamente para garantir consistência na resposta a incidentes e reduzir o tempo de resolução (MTTR).

### Estrutura de um Playbook

Cada playbook contém:
- **Descrição**: O que é o alerta e por que é importante
- **Severidade**: Nível de urgência
- **Trigger**: Condição que dispara o alerta
- **Diagnóstico**: Passos para identificar a causa raiz
- **Resolução**: Ações para resolver o problema
- **Verificação**: Como confirmar que o problema está resolvido
- **Prevenção**: Ações para evitar recorrência
- **Escalation**: Quando e como escalar

---

## 2. PLAYBOOKS CRÍTICOS

### 2.1 Circuit Breaker Ativado

**Descrição**: O circuit breaker de risco foi ativado automaticamente, pausando a geração de novos sinais. Isto acontece quando drawdown ou outras métricas de risco excedem limites definidos para proteger a banca.

**Severidade**: CRITICAL 🔴

**Trigger**: Drawdown diário > 15% OU drawdown semanal > 25%

**Diagnóstico**:
1. Verificar dashboard de risco (DB-004)
2. Identificar qual circuit breaker foi ativado (drawdown diário, semanal, CLV, etc.)
3. Verificar PnL dos últimos 7 dias para identificar causa
4. Verificar se há anomalias no modelo (CLV negativo, drift)
5. Verificar se há problemas operacionais (slippage alto, fill rate baixo)

**Resolução**:
```
Se Drawdown Diário > 15%:
  1. Confirmar se drawdown é normal (variação) ou anômalo
  2. Se normal: Ajustar threshold temporariamente, monitorizar
  3. Se anômalo: Investigar causa (modelo, mercado, execução)
  4. Se causa identificada: Corrigir, retreinar modelo se necessário
  5. Se causa não identificada: Manter CB pausado, investigação profunda

Se Drawdown Semanal > 25%:
  1. Análise profunda de todas as apostas da semana
  2. Verificar se há padrão (mercado específico, bookmaker, horário)
  3. Se padrão identificado: Ajustar estratégia
  4. Se não há padrão: Pausar operações, revisão completa do modelo
  5. Considerar redução de bankroll ou pausa temporária
```

**Verificação**:
- PnL dos últimos 3 dias é positivo ou neutro
- Drawdown está abaixo de 10%
- CLV médio > 0%
- Nenhum outro circuit breaker ativado

**Prevenção**:
- Ajustar thresholds baseado em volatilidade histórica
- Implementar alertas prévios (drawdown > 10% como HIGH)
- Monitorizar tendências de degradação antes de atingir limite
- Revisar estratégia de stakes e Kelly fracionado

**Escalation**:
- Se não resolvido em 1 hora → Escalar para Quant Engineer
- Se não resolvido em 4 horas → Escalar para Gestor de Operações
- Se drawdown > 30% → Parar operações, reunião de emergência

---

### 2.2 Feed de Dados Offline

**Descrição**: Um ou mais feeds de dados críticos (NBA Stats, Odds, Injuries) estão offline ou não respondendo. Sem dados, o modelo não pode gerar sinais.

**Severidade**: CRITICAL 🔴

**Trigger**: Feed offline > 10 minutos OU taxa de erro > 10%

**Diagnóstico**:
1. Verificar qual feed está afetado (NBA Stats, Odds, Injuries)
2. Verificar status do provider (status page, Twitter)
3. Testar endpoint manualmente (curl ou Postman)
4. Verificar logs da aplicação para mensagens de erro
5. Verificar se há rate limiting ou bloqueio de IP
6. Verificar conectividade de rede (ping, traceroute)

**Resolução**:
```
Se Provider Down:
  1. Verificar status page do provider
  2. Se outage conhecido: Aguardar resolução, estimar tempo
  3. Se outage desconhecido: Contactar suporte do provider
  4. Ativar cache de dados se disponível (dados de backup)

Se Rate Limiting:
  1. Verificar limite de requests do plano
  2. Reduzir frequência de scrape se necessário
  3. Implementar backoff exponencial
  4. Considerar upgrade de plano do provider

Se Erro de Autenticação:
  1. Verificar se API key expirou
  2. Renovar API key se necessário
  3. Verificar se há mudança na API do provider

Se Problema de Rede:
  1. Verificar firewall do VPS
  2. Verificar DNS resolution
  3. Testar conectividade com outros endpoints
  4. Considerar mudança de IP se bloqueado
```

**Verificação**:
- Feed responde a requests com sucesso
- Latência < threshold definido
- Taxa de erro < 1%
- Dados são atualizados (freshness < 5 min)

**Prevenção**:
- Implementar múltiplos providers para feeds críticos (redundância)
- Configurar cache local com dados de backup (24h)
- Implementar health checks ativos (ping a cada 30s)
- Monitorizar rate limits e quotas
- Ter contato direto com suporte do provider

**Escalation**:
- Se não resolvido em 15 min → Escalar para DevOps
- Se não resolvido em 1 hora → Escalar para Gestor de Operações
- Se sem dados por > 4 horas → Considerar pausa de operações

---

### 2.3 Banco de Dados Inacessível

**Descrição**: PostgreSQL não está acessível ou está a responder com timeouts. Sem banco de dados, nenhuma operação é possível (sinais, apostas, dashboards).

**Severidade**: CRITICAL 🔴

**Trigger**: PostgreSQL connection errors > 10% OU timeout > 5s

**Diagnóstico**:
1. Verificar se processo PostgreSQL está running
2. Verificar logs de PostgreSQL (/var/log/postgresql/)
3. Verificar conexões ativas (pg_stat_activity)
4. Verificar uso de recursos (CPU, RAM, disk)
5. Verificar se há locks ou deadlocks
6. Verificar espaço em disco (pg_database_size)

**Resolução**:
```
Se PostgreSQL Down:
  1. Tentar reiniciar serviço: systemctl restart postgresql
  2. Se não iniciar: Verificar logs para erro
  3. Se disco cheio: Liberar espaço (limpar logs, arquivos temporários)
  4. Se corrupção: Restaurar do backup mais recente

Se Muitas Conexões:
  1. Verificar max_connections no postgresql.conf
  2. Identificar queries long-running (pg_stat_activity)
  3. Matar queries problematicas se necessário
  4. Aumentar max_connections ou implementar connection pool

Se Locks/Deadlocks:
  1. Identificar locks (pg_locks)
  2. Matar transações bloqueadas
  3. Otimizar queries para reduzir tempo de lock
  4. Implementar timeout de transações

Se Performance Lenta:
  1. Identificar slow queries (pg_stat_statements)
  2. EXPLAIN ANALYZE das queries lentas
  3. Adicionar índices se necessário
  4. Otimizar queries ou arquitetura
```

**Verificação**:
- PostgreSQL aceita conexões
- Queries respondem em < 100ms (P95)
- Nenhum lock ou deadlock
- Replication lag < 1s (se replicação ativa)

**Prevenção**:
- Configurar monitorização proativa de conexões e performance
- Implementar connection pool (PgBouncer)
- Configurar backups automáticos diários
- Implementar replicação (hot standby)
- Revisar e otimizar queries regularmente

**Escalation**:
- Se não resolvido em 10 min → Escalar para DBA/DevOps
- Se não resolvido em 30 min → Escalar para Gestor de Operações
- Se downtime > 1 hora → Ativar plano de disaster recovery

---

## 3. PLAYBOOKS HIGH

### 3.1 CLV 3d Negativo

**Descrição**: CLV (Closing Line Value) médio das últimas 50-100 apostas é negativo, indicando que o modelo está a perder para o mercado (sem edge).

**Severidade**: HIGH 🟠

**Trigger**: CLV médio 3 dias < 0%

**Diagnóstico**:
1. Verificar dashboard de performance quant (DB-002)
2. Analisar CLV por regime (casa/fora, favorito/underdog)
3. Verificar se há mudança de mercado (nova temporada, regras)
4. Verificar drift de features (PSI, KS test)
5. Verificar se há problema com odds de fechamento (fonte incorreta)

**Resolução**:
```
Se CLV Negativo Isolado:
  1. Verificar se é variação normal (ruído estatístico)
  2. Monitorizar próximos 50 apostas
  3. Se continuar negativo: Investigar mais a fundo

Se CLV Negativo por Regime:
  1. Identificar regime com problema (ex: jogos fora de casa)
  2. Ajustar modelo para esse regime ou pausar sinais nele
  3. Retreinar modelo com foco no regime problemático

Se Feature Drift:
  1. Identificar features com drift significativo
  2. Coletar novos dados para refletir novo regime
  3. Retreinar modelo com dados recentes
  4. Validar em backtest antes de deploy

Se Mudança de Mercado:
  1. Investigar o que mudou (regras, formato, etc.)
  2. Adaptar features ao novo regime
  3. Retreinar modelo com dados pós-mudança
```

**Verificação**:
- CLV médio 50 apostas > 0%
- CLV por regime > 0% (ou pelo menos neutro)
- Feature drift < threshold
- Modelo validado em backtest recente

**Prevenção**:
- Monitorizar CLV rolling continuamente
- Implementar alertas prévios (CLV < 1% como MEDIUM)
- Retreinar modelo regularmente (mensal ou trimestral)
- Manter dataset de treino atualizado
- Implementar A/B testing para novas versões do modelo

**Escalation**:
- Se não resolvido em 24h → Escalar para Quant Engineer
- Se não resolvido em 72h → Escalar para Gestor de Operações
- Se CLV < -2% por 7 dias → Considerar pausa de operações

---

### 3.2 Drawdown > 10%

**Descrição**: Drawdown atual excedeu 10%, indicando perda significativa. Ainda não é crítico mas requer atenção.

**Severidade**: HIGH 🟠

**Trigger**: Drawdown atual > 10%

**Diagnóstico**:
1. Verificar dashboard de risco (DB-004)
2. Analisar curva de drawdown (tendência ou pico isolado)
3. Verificar PnL dos últimos 7 dias
4. Verificar se há apostas de stake alto contribuindo
5. Verificar CLV e performance do modelo

**Resolução**:
```
Se Drawdown por Pico Isolado:
  1. Verificar se foi aposta de stake alto ou outlier
  2. Se stake alto: Revisar estratégia de stakes (Kelly)
  3. Monitorizar recuperação nos próximos dias
  4. Se não recuperar: Investigar mais

Se Drawdown por Tendência:
  1. Identificar causa (modelo degradado, mercado mudou)
  2. Se modelo: Retreinar ou ajustar
  3. Se mercado: Ajustar estratégia ou pausar mercado
  4. Reduzir stakes temporariamente (50%)
```

**Verificação**:
- Drawdown < 10%
- PnL dos últimos 3 dias positivo ou neutro
- CLV médio > 0%

**Prevenção**:
- Implementar gestão de stakes conservadora (Kelly fracionado)
- Monitorizar drawdown em tempo real
- Ajustar stakes dinamicamente baseado em risco
- Diversificar por mercado e bookmaker

**Escalation**:
- Se drawdown > 15% → Escala para CRITICAL (ver playbook CB)
- Se não resolvido em 48h → Escalar para Risk Manager

---

### 3.3 Modelo Drift Detectado

**Descrição**: Drift significativo detetado em múltiplas features, indicando que a distribuição de dados mudou e o modelo pode estar descalibrado.

**Severidade**: HIGH 🟠

**Trigger**: > 3 features com PSI > 0.2 ou KS > 0.1

**Diagnóstico**:
1. Verificar dashboard de performance quant (DB-002)
2. Identificar features com drift
3. Analisar distribuição das features afetadas
4. Investigar causa (nova temporada, mudança de regras, outlier)
5. Verificar impacto em performance (AUC, Brier, CLV)

**Resolução**:
```
Se Drift por Nova Temporada:
  1. Coletar dados da nova temporada
  2. Retreinar modelo com dados recentes
  3. Validar em backtest
  4. Deploy gradual (canary)

Se Drift por Mudança de Regras:
  1. Adaptar features às novas regras
  2. Remover features obsoletas
  3. Adicionar features para capturar novo regime
  4. Retreinar e validar

Se Drift por Outlier:
  1. Identificar e remover outlier do treino
  2. Se outlier é realidade nova: Adaptar modelo
  3. Se outlier é erro: Corrigir dados
```

**Verificação**:
- PSI/KS das features < threshold
- Performance do modelo estável (AUC, Brier)
- CLV médio > 0%

**Prevenção**:
- Monitorizar drift continuamente
- Retreinar modelo regularmente
- Manter pipeline de dados atualizado
- Implementar validação de dados antes de inferência

**Escalation**:
- Se não resolvido em 48h → Escalar para Quant Engineer
- Se performance degradada significativamente → Considerar pausa

---

## 4. PLAYBOOKS MEDIUM

### 4.1 CPU Usage Elevado

**Descrição**: CPU do VPS está acima de 80% por período prolongado, indicando possível bottleneck ou processo mal-comportado.

**Severidade**: MEDIUM 🟡

**Trigger**: CPU > 80% por 5 minutos

**Diagnóstico**:
1. Verificar dashboard de infraestrutura (DB-006)
2. Identificar processo consumidor (top, htop)
3. Verificar se há loops infinitos ou memory leaks
4. Verificar se há aumento de carga (mais sinais, mais subscritores)

**Resolução**:
```
Se Processo Específico:
  1. Identificar processo (ex: Python worker)
  2. Verificar logs do processo para erros
  3. Se loop: Reiniciar processo
  4. Se leak: Corrigir código ou reiniciar periodicamente

Se Aumento de Carga:
  1. Verificar se aumento é esperado (sazonalidade)
  2. Se esperado: Escalar VPS (mais CPU)
  3. Se inesperado: Investigar causa (bug, DDoS)
```

**Verificação**:
- CPU < 70%
- Nenhum processo consumidor anômalo
- Performance da aplicação normal

**Prevenção**:
- Implementar auto-scaling se em cloud
- Otimizar código e queries
- Implementar rate limiting
- Monitorizar tendências de CPU

**Escalation**:
- Se CPU > 95% → Escala para HIGH
- Se não resolvido em 4h → Escalar para DevOps

---

### 4.2 Disk Usage Elevado

**Descrição**: Disco está acima de 80% de capacidade, arriscando falta de espaço para logs, banco de dados e arquivos do sistema.

**Severidade**: MEDIUM 🟡

**Trigger**: Disk usage > 80%

**Diagnóstico**:
1. Verificar dashboard de infraestrutura (DB-006)
2. Identificar o que está ocupando espaço (du -sh)
3. Verificar crescimento de logs
4. Verificar tamanho do banco de dados

**Resolução**:
```
Se Logs Grandes:
  1. Limpar logs antigos (logrotate)
  2. Comprimir logs se necessário
  3. Ajustar retenção de logs

Se Banco de Dados Grande:
  1. Arquivar dados históricos
  2. Implementar particionamento
  3. Limpar tabelas temporárias

Se Arquivos Temporários:
  1. Limpar /tmp
  2. Limpar cache de aplicações
```

**Verificação**:
- Disk usage < 70%
- Projeção de crescimento < 90% em 30 dias

**Prevenção**:
- Configurar logrotate automático
- Implementar arquivamento de dados
- Monitorizar tendências de crescimento
- Configurar alertas prévios (disk > 70% como LOW)

**Escalation**:
- Se disk > 90% → Escala para HIGH
- Se não resolvido em 24h → Escalar para DevOps

---

### 4.3 ECE (Calibration Error) Alto

**Descrição**: Expected Calibration Error está acima de 0.10, indicando que as probabilidades do modelo não estão calibradas (sobre-confiantes ou sub-confiantes).

**Severidade**: MEDIUM 🟡

**Trigger**: ECE > 0.10

**Diagnóstico**:
1. Verificar reliability diagram no dashboard quant (DB-002)
2. Verificar se modelo é sobre-confiante (prob > real)
3. Verificar se modelo é sub-confiante (prob < real)
4. Analisar por regime de probabilidade (bins)

**Resolução**:
```
Se Sobre-confiante:
  1. Aplicar calibração isotónica ou Platt scaling
  2. Retreinar com mais dados
  3. Ajustar thresholds de geração de sinais

Se Sub-confiante:
  1. Revisar features e arquitetura do modelo
  2. Aumentar capacidade do modelo (mais features, mais complexo)
  3. Verificar se há leak de informação
```

**Verificação**:
- ECE < 0.10
- Reliability diagram alinhado (45 graus)
- CLV médio estável

**Prevenção**:
- Implementar calibração regular do modelo
- Monitorizar ECE continuamente
- Retreinar modelo com dados recentes
- Validar calibração em backtest

**Escalation**:
- Se ECE > 0.15 → Escala para HIGH
- Se não resolvido em 72h → Escalar para Quant Engineer

---

## 5. PLAYBOOKS LOW

### 5.1 Disco Próximo do Limite

**Descrição**: Disk usage está entre 70-80%, indicando que espaço está a ficar escasso mas não é crítico ainda.

**Severidade**: LOW 🔵

**Trigger**: Disk usage > 70%

**Diagnóstico**:
1. Verificar taxa de crescimento (últimos 30 dias)
2. Projetar quando atingirá 90%
3. Identificar o que está crescendo mais rápido

**Resolução**:
```
Planejamento:
  1. Agendar limpeza ou arquivamento
  2. Se crescimento rápido: Considerar upgrade de disco
  3. Se crescimento lento: Monitorizar, agendar manutenção
```

**Verificação**:
- Projeção de crescimento segura (> 30 dias até 90%)

**Prevenção**:
- Monitorizar tendências de crescimento
- Implementar arquivamento automático
- Configurar alertas progressivos (70%, 80%, 90%)

**Escalation**:
- Se disk > 85% → Escala para MEDIUM
- Se não resolvido em 7 dias → Escalar para DevOps

---

### 5.2 Resumo Diário de PnL

**Descrição**: Alerta informativo com resumo diário de performance financeira (PnL, ROI, CLV, apostas).

**Severidade**: LOW 🔵

**Trigger**: Agendado diariamente às 18h

**Diagnóstico**:
N/A (informativo)

**Resolução**:
N/A (informativo)

**Verificação**:
N/A

**Prevenção**:
N/A

**Escalation**:
Se PnL diário < -€2.000 → Revisar manualmente

---

## 6. PROCESSO DE RESPOSTA A INCIDENTES

### 6.1 Fluxo Geral

```
1. RECEBER ALERTA
   ↓
2. ACKNOWLEDGE (confirmar recebimento)
   ↓
3. DIAGNÓSTICO (seguir playbook)
   ↓
4. RESOLUÇÃO (executar ações)
   ↓
5. VERIFICAÇÃO (confirmar resolução)
   ↓
6. RESOLVE ALERTA (fechar)
   ↓
7. DOCUMENTAÇÃO (post-mortem)
```

### 6.2 Template de Post-Mortem

**Incidente**: [Nome do incidente]
**Data**: [DD/MM/YYYY HH:MM]
**Severidade**: [CRITICAL/HIGH/MEDIUM/LOW]
**Duração**: [X horas Y minutos]
**Impacto**: [Descrição do impacto]

**Causa Raiz**:
- [Descrição detalhada da causa]

**Linha do Tempo**:
- [HH:MM] Alerta disparou
- [HH:MM] Acknowledge por [Nome]
- [HH:MM] Diagnóstico iniciado
- [HH:MM] Causa identificada
- [HH:MM] Resolução iniciada
- [HH:MM] Incidente resolvido

**Ações Tomadas**:
- [Lista de ações]

**Lições Aprendidas**:
- [O que funcionou bem]
- [O que poderia ser melhorado]

**Ações de Prevenção**:
- [O que fazer para evitar recorrência]

---

## 7. LINKS CRUZADOS

- [[33_Alerting/INDEX]] ← Seção mãe
- [[33_Alerting/SISTEMA_ALERTAS]] → Arquitetura do sistema de alertas
- [[33_Alerting/ALERTAS_TELEGRAM]] → Configuração Telegram
- [[26_Runbooks/INDEX]] → Runbooks operacionais gerais
- [[10_Monitoring/METRICAS_DETALHADAS]] → Definições de métricas