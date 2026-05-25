# SOP_CIRCUIT_BREAKER — Procedimento Operacional Padrão

**ID:** `SOP-004` | **Fase:** #phase/4 | **Owner:** Risk Manager | **Status:** #status/active
**Última Revisão:** 2024-05-13 | **Próxima Revisão:** 2024-08-13

---

## 1. OBJETIVO

Estabelecer um procedimento padronizado para resposta à ativação de circuit breakers no sistema de value betting NBA. Circuit breakers são mecanismos de proteção automática que interrompem operações quando condições de risco críticas são detetadas. Este SOP garante que a resposta seja rápida, consistente, e documentada, minimizando perdas adicionais e facilitando a análise pós-incidente.

---

## 2. APLICAÇÃO

**Quando executar:**
- Imediatamente após receber alerta de circuit breaker ativado (P1)
- Quando verificar manualmente que um circuit breaker está ativo
- Durante revisões diárias se circuit breaker foi ativado e não resolvido

**Responsável:**
- Operador on-call (primeira resposta)
- Risk Manager (análise e decisão de reset)
- Operations Lead (comunicação e coordenação)

**Duração estimada:**
- Resposta imediata: 5-10 minutos (parar operações)
- Análise e decisão: 30-60 minutos
- Reset ou ajuste: 15-30 minutos

---

## 3. CIRCUIT BREAKERS DO SISTEMA

O sistema possui 4 circuit breakers principais, cada um com um trigger específico:

| ID | Nome | Trigger | Severidade | Ação Automática |
|----|------|---------|------------|-----------------|
| Alpha | Drawdown | Drawdown > 15% | P1 | Parar motor de decisão |
| Beta | Perdas Consecutivas | 7 perdas consecutivas | P1 | Parar motor de decisão |
| Gamma | Feed Offline | Feed offline > 5 minutos | P1 | Parar motor de decisão |
| Delta | Performance | ROI < -5% nos últimos 30 dias | P2 | Alerta (não para automaticamente) |

---

## 4. PRÉ-REQUISITOS

### 4.1. Acesso e Ferramentas
- [ ] Acesso ao dashboard de circuit breakers
- [ ] Acesso à base de dados PostgreSQL
- [ ] Acesso ao sistema de alertas
- [ ] Acesso ao canal Telegram ops_alertas
- [ ] Permissões para parar/iniciar motor de decisão

### 4.2. Conhecimentos Necessários
- Compreensão dos 4 circuit breakers e seus thresholds
- Capacidade de calcular drawdown e sequência de perdas
- Familiaridade com métricas de performance (ROI, CLV)
- Autoridade para tomar decisões de risco (ou acesso a quem tem)

### 4.3. Estado do Sistema
- [ ] Motor de decisão está acessível
- [ ] Base de dados está online
- [ ] Sistema de alertas está funcional

---

## 5. PROCEDIMENTO GERAL DE RESPOSTA

Este procedimento aplica-se a todos os circuit breakers. Procedimentos específicos para cada circuit breaker estão na secção 6.

### 5.1. Fase 1: Resposta Imediata (0-5 minutos)

**Objetivo:** Parar operações e prevenir perdas adicionais.

**Passos:**

1. **Receber alerta:**
   - Alerta P1 é recebido via PagerDuty (call) + Telegram + E-mail
   - Ler mensagem do alerta para identificar qual circuit breaker disparou

2. **Confirmar ativação:**
   - Aceder ao dashboard de circuit breakers
   - Verificar status do circuit breaker (deve estar "ACTIVE")
   - Verificar timestamp de ativação
   - Verificar trigger_reason (motivo do disparo)

3. **Parar motor de decisão:**
   - Se motor ainda está a correr: parar imediatamente
   - Comando: `docker stop decision_engine`
   - Confirmar que motor parou: `docker ps` (não deve aparecer decision_engine)
   - Se motor já parou automaticamente: confirmar no dashboard

4. **Notificar equipa:**
   - Enviar mensagem urgente no canal ops_alertas:
     ```
     [URGENTE] Circuit Breaker [ID] ativado às [hora]
     Trigger: [motivo]
     Motor de decisão parado
     A investigar...
     ```
   - Se severidade P1: marcar gestor de risco na mensagem

5. **Documentar ativação:**
   - Criar registo em daily note (se dia ativo) ou em log de incidentes
   - Registar: timestamp, circuit breaker ID, trigger, ações tomadas

### 5.2. Fase 2: Investigação (5-30 minutos)

**Objetivo:** Compreender causa raiz e avaliar gravidade.

**Passos:**

1. **Recolher dados:**
   - Consultar métricas relevantes para o circuit breaker (ver secção 6)
   - Exportar dados para análise (últimos 30 dias, últimos 7 dias, etc.)
   - Verificar se há padrões ou tendências

2. **Analisar contexto:**
   - Verificar se há outros alertas ativos
   - Verificar se há anomalias em outros sistemas
   - Verificar se há eventos externos relevantes (ex: mudança de regulamentação)

3. **Identificar causa raiz:**
   - Usar técnica dos 5 porquês para identificar causa raiz
   - Documentar hipóteses de causa
   - Verificar dados para confirmar ou refutar hipóteses

4. **Avaliar impacto:**
   - Calcular perda financeira até ao momento
   - Avaliar impacto em subscritores (se aplicável)
   - Avaliar impacto em reputação

5. **Comunicar descobertas:**
   - Enviar atualização no canal ops_alertas:
     ```
     Atualização Circuit Breaker [ID]:
     - Investigação em curso
     - Causa provável: [descrição]
     - Impacto estimado: [descrição]
     - Próximos passos: [descrição]
     ```

### 5.3. Fase 3: Decisão e Ação (30-60 minutos)

**Objetivo:** Tomar decisão sobre reset ou ajuste e executar.

**Passos:**

1. **Consultar Risk Manager:**
   - Se operador não tem autoridade para reset: contactar Risk Manager
   - Apresentar dados recolhidos e análise
   - Recomendar ação: reset imediato, reset condicional, ou manter parado

2. **Tomar decisão:**
   - Opções de decisão:
     - **Reset imediato:** Condição resolvida, seguro retomar
     - **Reset condicional:** Retomar com ajustes (ex: reduzir stake)
     - **Manter parado:** Condição não resolvida, risco ainda elevado
     - **Ajustar threshold:** Threshold incorreto, necessário ajustar
   - Documentar decisão com justificação

3. **Executar ação:**
   - Se reset imediato ou condicional: executar procedimento de reset (ver secção 6)
   - Se ajustar threshold: executar procedimento de ajuste (ver secção 7)
   - Se manter parado: agendar revisão futura

4. **Comunicar decisão:**
   - Enviar mensagem no canal ops_alertas:
     ```
     Decisão Circuit Breaker [ID]:
     - Ação: [reset/ajuste/manter parado]
     - Justificação: [descrição]
     - Responsável: [nome]
     - Próxima revisão: [data/hora]
     ```

### 5.4. Fase 4: Monitorização Pós-Reset (60-90 minutos)

**Objetivo:** Garantir que sistema está estável após reset.

**Passos:**

1. **Reiniciar motor de decisão (se reset):**
   - Comando: `docker start decision_engine`
   - Confirmar que motor iniciou: `docker logs decision_engine --tail 20`
   - Verificar que não há erros nos logs

2. **Monitorizar execução:**
   - Observar primeira execução do motor após reset
   - Verificar número de sinais gerados
   - Verificar qualidade dos sinais (CLV, edge)
   - Verificar que não há erros

3. **Verificar métricas:**
   - Monitorizar métricas que dispararam o circuit breaker
   - Verificar que estão dentro de thresholds aceitáveis
   - Se métricas ainda fora de thresholds: considerar parar novamente

4. **Documentar resultado:**
   - Atualizar registo em daily note ou log de incidentes
   - Documentar resultado do reset
   - Se houver problemas: documentar e escalar

### 5.5. Fase 5: Análise Pós-Incidente (24-48 horas)

**Objetivo:** Aprender com incidente e melhorar sistema.

**Passos:**

1. **Preparar postmortem:**
   - Se incidente foi severo (P1): criar postmortem formal
   - Se incidente foi moderado (P2): criar análise simplificada
   - Usar template TEMPLATE_POSTMORTEM

2. **Identificar lições aprendidas:**
   - O que correu bem na resposta?
   - O que pode ser melhorado?
   - O incidente pode ser prevenido no futuro?

3. **Implementar melhorias:**
   - Atribuir ações corretivas com owners e deadlines
   - Atualizar SOPs e runbooks se necessário
   - Ajustar thresholds se apropriado

4. **Compartilhar conhecimento:**
   - Apresentar postmortem à equipa
   - Documentar lições aprendidas em base de conhecimento
   - Atualizar treinamento de operadores

---

## 6. PROCEDIMENTOS ESPECÍFICOS POR CIRCUIT BREAKER

### 6.1. Circuit Breaker Alpha: Drawdown

**Trigger:** Drawdown > 15%

**Métricas a analisar:**
- Drawdown atual (%)
- Drawdown máximo nos últimos 30 dias
- High watermark
- Banca atual
- Sequência de perdas atual
- ROI dos últimos 7, 14, 30 dias

**Investigação detalhada:**

1. **Verificar drawdown:**
   - Calcular drawdown: (High Watermark - Banca Atual) / High Watermark
   - Confirmar que drawdown > 15%
   - Verificar quando drawdown começou a aumentar

2. **Analisar causas possíveis:**
   - Sequência de perdas longa?
   - Perdas grandes individuais?
   - Aumento de stake sem aumento de edge?
   - Degradação de performance do modelo?

3. **Verificar contexto:**
   - Há mudanças no mercado (ex: offseason, mudança de regras)?
   - Há mudanças no modelo (ex: retreino recente)?
   - Há anomalias nos dados?

**Critérios de reset:**

| Condição | Ação |
|----------|------|
| Drawdown < 12% e tendência estável | Reset imediato |
| Drawdown 12-15% e tendência descendente | Reset condicional (reduzir stake 50%) |
| Drawdown > 15% e tendência descendente | Manter parado, investigar |
| Drawdown causado por evento externo único | Reset imediato se evento resolvido |

**Procedimento de reset:**
1. Confirmar que drawdown está abaixo de threshold ou tendência é estável
2. Se reset condicional: ajustar parâmetro de stake na base de dados
3. Executar reset: `UPDATE circuit_breakers SET status='INACTIVE', trigger_reason=NULL WHERE id='ALPHA'`
4. Reiniciar motor de decisão
5. Monitorizar drawdown durante 24 horas

---

### 6.2. Circuit Breaker Beta: Perdas Consecutivas

**Trigger:** 7 perdas consecutivas

**Métricas a analisar:**
- Sequência de perdas atual
- Sequência de perdas máxima histórica
- Taxa de acerto dos últimos 7, 14, 30 dias
- CLV médio das últimas 7 apostas
- Edge médio das últimas 7 apostas
- Slippage médio das últimas 7 apostas

**Investigação detalhada:**

1. **Verificar sequência:**
   - Contar perdas consecutivas
   - Confirmar que são 7 ou mais
   - Verificar data da primeira perda da sequência

2. **Analisar causas possíveis:**
   - Modelo degradado (CLV negativo)?
   - Slippage excessivo?
   - Odds movendo rapidamente (latência alta)?
   - Stake demasiado alto?
   - Má execução manual?

3. **Verificar qualidade dos sinais:**
   - CLV médio está positivo?
   - Edge médio está dentro do esperado?
   - Sinais estão a ser executados dentro do expiry?

**Critérios de reset:**

| Condição | Ação |
|----------|------|
| CLV médio > 2% e edge normal | Reset imediato |
| CLV médio 0-2% ou slippage alto | Reset condicional (reduzir stake 50%) |
| CLV médio < 0% | Manter parado, investigar modelo |
| Sequência causada por execução manual falhada | Reset imediato, treinar operador |

**Procedimento de reset:**
1. Confirmar que causa raiz foi identificada e resolvida
2. Se reset condicional: ajustar parâmetro de stake
3. Executar reset: `UPDATE circuit_breakers SET status='INACTIVE', trigger_reason=NULL WHERE id='BETA'`
4. Reiniciar motor de decisão
5. Monitorizar sequência durante 24 horas

---

### 6.3. Circuit Breaker Gamma: Feed Offline

**Trigger:** Feed offline > 5 minutos

**Métricas a analisar:**
- Status do feed Betfair API
- Última atualização de odds
- Taxa de sucesso de chamadas API
- Latência de chamadas API
- Rate limits atuais
- Status do token de sessão

**Investigação detalhada:**

1. **Verificar status do feed:**
   - Testar conexão: `curl -I https://api.betfair.com`
   - Verificar logs do serviço de feed
   - Verificar se há erros de autenticação

2. **Analisar causas possíveis:**
   - Token de sessão expirado?
   - Rate limits excedidos?
   - Betfair API down?
   - Problema de rede?
   - Problema no código de integração?

3. **Verificar impacto:**
   - Quantos jogos foram afetados?
   - Quantos sinais foram perdidos?
   - Há apostas pendentes com odds desatualizadas?

**Critérios de reset:**

| Condição | Ação |
|----------|------|
| Token expirado | Renovar token, reset imediato |
| Rate limits | Aguardar janela de reset, reset imediato |
| Betfair API down | Aguardar resolução, monitorizar |
| Problema de rede | Resolver rede, reset imediato |
| Problema no código | Corrigir código, testar, reset |

**Procedimento de reset:**
1. Resolver causa raiz do problema
2. Verificar que feed está a funcionar (testar chamadas API)
3. Confirmar que dados estão a ser atualizados
4. Executar reset: `UPDATE circuit_breakers SET status='INACTIVE', trigger_reason=NULL WHERE id='GAMMA'`
5. Reiniciar motor de decisão
6. Verificar que pipeline de dados está a processar

---

### 6.4. Circuit Breaker Delta: Performance

**Trigger:** ROI < -5% nos últimos 30 dias

**Métricas a analisar:**
- ROI dos últimos 30 dias
- ROI dos últimos 7, 14 dias
- Drawdown dos últimos 30 dias
- Taxa de acerto dos últimos 30 dias
- CLV médio dos últimos 30 dias
- AUC do modelo nos últimos 30 dias
- Sharpe ratio dos últimos 30 dias

**Investigação detalhada:**

1. **Verificar performance:**
   - Calcular ROI 30 dias
   - Confirmar que ROI < -5%
   - Comparar com ROI 7 e 14 dias (tendência)

2. **Analisar causas possíveis:**
   - Modelo degradado (drift)?
   - Mudança no mercado (regime change)?
   - Slippage aumentou?
   - Thresholds de edge mudaram?
   - Overfitting do modelo?

3. **Verificar qualidade do modelo:**
   - AUC atual vs AUC histórico
   - Calibração do modelo
   - Distribuição de predições vs histórico
   - Feature drift

**Critérios de reset:**

| Condição | Ação |
|----------|------|
| ROI -5% a -3% e tendência ascendente | Reset imediato |
| ROI -5% a -3% e tendência descendente | Reset condicional (reduzir stake 30%) |
| ROI < -5% e tendência descendente | Manter parado, retreinar modelo |
| ROI < -5% mas CLV positivo | Manter parado, investigar execução |

**Procedimento de reset:**
1. Identificar causa raiz (degradação de modelo ou problema de execução)
2. Se degradação de modelo: agendar retreino (ver SOP-005)
3. Se problema de execução: corrigir problema
4. Executar reset: `UPDATE circuit_breakers SET status='INACTIVE', trigger_reason=NULL WHERE id='DELTA'`
5. Reiniciar motor de decisão
6. Monitorizar performance durante 7 dias

---

## 7. PROCEDIMENTO DE AJUSTE DE THRESHOLDS

Se a análise revelar que um threshold está incorreto (muito sensível ou muito permissivo), proceder ao ajuste:

**Passos:**

1. **Justificar ajuste:**
   - Apresentar dados que suportam a necessidade de ajuste
   - Calcular novo threshold proposto
   - Avaliar impacto do novo threshold

2. **Obter aprovação:**
   - Se ajuste de threshold P1 ou P2: requer aprovação do Risk Manager
   - Se ajuste de threshold P3 ou P4: pode ser aprovado por Operations Lead
   - Documentar aprovação com justificação

3. **Executar ajuste:**
   - Atualizar threshold na base de dados:
     ```sql
     UPDATE circuit_breakers
     SET threshold_value = [novo valor],
         last_modified = NOW(),
         modified_by = '[operador]',
         modification_reason = '[justificação]'
     WHERE id = '[ID]';
     ```

4. **Testar novo threshold:**
   - Verificar que circuit breaker não dispara falsamente
   - Monitorizar durante período de teste (7 dias)
   - Se necessário, ajustar novamente

5. **Documentar:**
   - Atualizar documentação do circuit breaker
   - Atualizar SOP-004
   - Comunicar mudança à equipa

---

## 8. TABELAS DE REFERÊNCIA

### 8.1. Estados de Circuit Breaker

| Estado | Descrição | Ação Permitida |
|--------|-----------|----------------|
| INACTIVE | Circuit breaker não disparado | Operações normais |
| ACTIVE | Circuit breaker disparou | Operações paradas |
| INVESTIGATING | Em investigação | Operações paradas |
| RESET_PENDING | Reset autorizado, aguardando execução | Operações paradas |
| MAINTENANCE | Em manutenção (threshold ajuste) | Operações paradas |

### 8.2. Tempos de Resposta Alvo

| Atividade | Tempo Alvo | Tempo Máximo |
|-----------|------------|--------------|
| Parar motor de decisão | 2 minutos | 5 minutos |
| Iniciar investigação | 5 minutos | 10 minutos |
| Completar investigação | 30 minutos | 60 minutos |
| Tomar decisão | 60 minutos | 120 minutos |
| Executar reset | 15 minutos | 30 minutos |
| Completar postmortem | 24 horas | 48 horas |

### 8.3. Níveis de Escalada

| Severidade | Primeira Resposta | Escalada se não resolvido em | Escalada Final |
|------------|-------------------|------------------------------|----------------|
| P1 | Operador on-call | 15 minutos → Risk Manager | 30 minutos → CEO |
| P2 | Operador on-call | 1 hora → Risk Manager | 4 horas → Operations Lead |
| P3 | Operador do dia | 4 horas → Risk Manager | 24 horas → Operations Lead |
| P4 | Operador do dia | 24 horas → Risk Manager | 7 dias → Operations Lead |

---

## 9. TROUBLESHOOTING

### 9.1. Problema: Circuit breaker dispara falsamente

**Causas possíveis:**
- Threshold demasiado sensível
- Erro no cálculo da métrica
- Dados incorretos na base de dados

**Resolução:**
1. Verificar cálculo da métrica manualmente
2. Verificar dados na base de dados
3. Se threshold incorreto: executar procedimento de ajuste (secção 7)
4. Se erro no cálculo: corrigir código, testar, reset

### 9.2. Problema: Motor de decisão não para quando circuit breaker ativa

**Causas possíveis:**
- Erro no mecanismo de parada automática
- Motor não está a verificar status do circuit breaker
- Problema de comunicação entre serviços

**Resolução:**
1. Parar motor manualmente: `docker stop decision_engine`
2. Verificar logs do motor para identificar problema
3. Corrigir código se necessário
4. Testar mecanismo de parada automática
5. Documentar incidente

### 9.3. Problema: Não é possível identificar causa raiz

**Causas possíveis:**
- Dados insuficientes
- Múltiplas causas possíveis
- Problema complexo

**Resolução:**
1. Recolher mais dados (expandir período de análise)
2. Consultar especialistas (ML engineer, data engineer)
3. Manter sistema parado até causa identificada
4. Se crítico: considerar reset com monitorização intensiva

### 9.4. Problema: Reset não funciona (circuit breaker reativa)

**Causas possíveis:**
- Condição de trigger ainda persiste
- Threshold ainda é excedido
- Erro no procedimento de reset

**Resolução:**
1. Verificar que condição de trigger está resolvida
2. Verificar que métricas estão dentro de thresholds
3. Se condição persiste: não fazer reset, manter parado
4. Se erro no reset: corrigir procedimento, tentar novamente

---

## 10. CHECKLIST FINAL

Antes de considerar circuit breaker resolvido, verificar:

- [ ] Causa raiz identificada
- [ ] Ação corretiva executada
- [ ] Métricas dentro de thresholds aceitáveis
- [ ] Motor de decisão reiniciado (se apropriado)
- [ ] Sistema monitorizado após reset
- [ ] Equipa notificada da resolução
- [ ] Incidente documentado
- [ ] Postmortem criado (se P1)
- [ ] Lições aprendidas documentadas
- [ ] Melhorias implementadas (se aplicável)

---

## 11. MÉTRICAS DE SUCESSO

| Métrica | Threshold | Ação se não cumprido |
|---------|-----------|---------------------|
| Tempo de parada do motor | < 5 minutos | Investigar atraso |
| Tempo de identificação de causa | < 60 minutos | Otimizar processo de investigação |
| Taxa de falsos positivos | < 10% | Ajustar thresholds |
| Tempo de reset | < 30 minutos | Simplificar procedimento |
| Taxa de reativação | < 20% (em 7 dias) | Investigar causas recorrentes |

---

## 12. RISCOS E MITIGAÇÃO

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|------------|
| Parada desnecessária (falso positivo) | Médio (perda de oportunidade) | Médio | Thresholds calibrados, análise rápida |
| Parada insuficiente (risco persiste) | Alto (perdas adicionais) | Baixa | Critérios de reset estritos |
| Reset prematuro | Alto (reativação) | Baixo | Verificação rigorosa antes de reset |
| Falha no mecanismo de parada | Crítico | Baixa | Testes regulares, parada manual disponível |
| Causa raiz não identificada | Alto | Médio | Análise profunda, especialistas disponíveis |

---

## 13. LINKS CRUZADOS

- [[25_SOPs/INDEX]] ← Secção mãe
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Detalhes técnicos dos circuit breakers
- [[08_Risk_Management/DRAWDOWN_CONTROL]] → Controle de drawdown
- [[18_Operations/GESTAO_ALERTAS]] → Gestão de alertas
- [[26_Runbooks/RB-008_Drawdown_Acelerado]] → Runbook específico
- [[27_Postmortems/INDEX]] → Postmortems