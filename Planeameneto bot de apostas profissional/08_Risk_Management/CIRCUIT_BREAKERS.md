# CIRCUIT-BREAKERS — Paragem Automática

**ID:** `RM-003` | **Fase:** #phase/2-6 | **Owner:** Risk Manager + Ops | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar um sistema de paragem automática (circuit breakers) que protege a banca de perdas catastróficas. Circuit breakers são mecanismos de defesa que interrompem automaticamente as operações quando condições específicas indicam risco elevado, impedindo que emoções humanas ou erros de sistema causem danos irreparáveis. O princípio fundamental é que a proteção deve ser automática, rápida e incondicional — nenhum operador humano pode sobrepor um circuit breaker ativado sem deixar um registo auditável claro e justificado.

---

## 2. PRINCÍPIOS FUNDAMENTAIS

### 2.1 Automaticidade

Circuit breakers devem ser completamente automáticos. Uma vez que uma condição de trigger é atingida, a ação correspondente deve ser executada imediatamente sem necessidade de intervenção humana. Isto elimina a possibilidade de hesitação, negação ou julgamento emocional em momentos de stress.

### 2.2 Incondicionalidade

As regras de circuit breakers são absolutas. Se a condição de trigger é satisfeita, a ação deve ser executada, independentemente de quão "seguro" o operador se sinta ou de quão "boa" pareça a oportunidade. Não há exceções, não há "só desta vez", não há "confio no meu feeling".

### 2.3 Auditabilidade

Toda ativação, reset e tentativa de sobreposição de circuit breaker deve ser registada em audit log com timestamp completo, valores das métricas que causaram o trigger, ação tomada, responsável pela ação (se manual), e justificação. Este registo é essencial para análise post-mortem, melhoria contínua e accountability.

### 2.4 Reversibilidade

Circuit breakers devem ser desenhados para serem reversíveis. Uma vez que a condição que causou o trigger seja resolvida, o sistema deve permitir reset automático ou manual do circuit breaker. No entanto, o reset manual requer justificação explícita e aprovação de nível apropriado.

---

## 3. TABELA DE TRIGGERS

| ID | Nome | Condicao | Acao Imediata | Notificacao | Severidade | Reset Automatico |
|----|------|----------|---------------|-------------|------------|-------------------|
| CB-001 | Drawdown Crítico | DD > 15% desde pico | Stakes *= 0.5 | Telegram CRITICAL | CRITICAL | Sim, após DD < 10% por 48h |
| CB-002 | Sequência Perdas | 5 perdas seguidas | Pausa 1h | Telegram HIGH | HIGH | Sim, após 1h timeout |
| CB-003 | Edge Zero | CLV 3d < 0% | Sem novas apostas | Telegram HIGH | HIGH | Sim, após CLV 3d > 1% por 24h |
| CB-004 | Feed Offline | Sem odds > 5 min | Sem novas apostas | Telegram CRITICAL | CRITICAL | Sim, após feed OK por 10 min |
| CB-005 | Erros Execução | > 3 erros/dia | Paragem total | Telegram CRITICAL + Email | CRITICAL | Não, requer revisão manual |
| CB-006 | Exposição Máxima | > 12% diário | Rejeitar sinais | Telegram MEDIUM | MEDIUM | Sim, nova sessão (dia seguinte) |
| CB-007 | Modelo Stale | Sem update > 7 dias | Sem novas apostas | Telegram HIGH | HIGH | Não, requer retraining manual |
| CB-008 | Drift Severo | PSI > 0.30 | Pausa + análise | Telegram CRITICAL | CRITICAL | Não, requer investigação manual |

---

## 4. DETALHAMENTO DE CIRCUIT BREAKERS

### 4.1 CB-001: Drawdown Crítico

**Objetivo:** Proteger contra perdas acumuladas que ameaçam a sobrevivência da banca. Um drawdown de 15% é um sinal de que algo está fundamentalmente errado — seja o modelo, o mercado, ou a execução — e exige redução imediata de exposição.

**Lógica:** Quando o drawdown atual (diferença entre o pico histórico e a banca atual, expresso como percentagem do pico) excede 15%, todos os stakes são reduzidos para metade imediatamente. Isto não é uma punição, mas uma medida de proteção que permite ao sistema "respirar" e recuperar com menor exposição.

**Exemplo Prático:** Banca pico = €10,000, Banca atual = €8,200. Drawdown = (10,000 - 8,200) / 10,000 = 18%. Como 18% > 15%, CB-001 ativa. Stake que seria €100 torna-se €50. Isto reduz a velocidade de perdas e dá tempo para investigar a causa do drawdown.

**Reset Automático:** O circuit breaker reseta automaticamente quando o drawdown cai abaixo de 10% e permanece abaixo por 48 horas consecutivas. Isto garante que a recuperação é sustentável, não apenas um blip temporário.

---

### 4.2 CB-002: Sequência Perdas

**Objetivo:** Proteger contra "tilt" emocional e possíveis falhas sistêmicas que causam perdas consecutivas. Cinco perdas seguidas são estatisticamente improváveis mesmo para um modelo com edge moderado, e podem indicar problema técnico ou mudança de regime de mercado.

**Lógica:** Quando cinco apostas consecutivas resultam em perda, o sistema pausa todas as novas apostas por uma hora. Esta pausa forçada permite investigação: o modelo está a falhar sistematicamente? Há problema com dados de entrada? O mercado mudou de forma que o modelo não captura?

**Exemplo Prático:** Apostas 13:00 = loss, 14:30 = loss, 16:00 = loss, 18:30 = loss, 20:00 = loss. CB-002 ativa. Sistema pausa até 21:00. Durante esta hora, operador investiga: verificar logs de erro, verificar feeds de dados, verificar se há notícias de lesões que o modelo não capturou.

**Reset Automático:** Após uma hora de pausa, o sistema retoma automaticamente. Se a perda continuar, o circuit breaker ativa novamente, criando um ciclo de pausas que força investigação mais profunda.

---

### 4.3 CB-003: Edge Zero

**Objetivo:** Proteger contra a perda de vantagem matemática. O CLV (Closed Line Value) é a métrica suprema de edge — se o CLV médio dos últimos 3 dias é negativo, o sistema não tem vantagem matemática e apostar seria equivalente a jogar contra a casa num casino.

**Lógica:** Quando o CLV médio rolling de 3 dias cai abaixo de 0%, o sistema para de gerar novas apostas. Isto é diferente de um drawdown — o sistema pode estar a ganhar dinheiro por sorte (variação positiva) mas se o CLV é negativo, a longo prazo perderá. Parar é a única decisão racional.

**Exemplo Prático:** Últimos 50 apostas têm CLV médio de -0.5%. Isto significa que, em média, estamos a apostar a odds piores que as odds de fecho do mercado. O mercado está mais informado ou mais eficiente que nós. CB-003 ativa. Sistema para até que CLV recupere para positivo.

**Reset Automático:** Quando o CLV médio de 3 dias excede 1% (margem de segurança) por 24 horas consecutivas, o sistema retoma. A margem de 1% evita ativações/desativações oscilantes em torno de zero.

---

### 4.4 CB-004: Feed Offline

**Objetivo:** Proteger contra apostas baseadas em dados incompletos ou desatualizados. Se o feed de odds (Betfair, Pinnacle, etc.) está offline por mais de 5 minutos, não podemos garantir que as odds que estamos a ver são atualizadas e confiáveis.

**Lógica:** Quando o sistema deteta que não há atualização de odds por mais de 5 minutos, todas as novas apostas são bloqueadas. Isto evita apostar a odds "stale" que podem ter mudado significativamente, resultando em edge negativo ou execução a preços muito piores que o esperado.

**Exemplo Prático:** Última atualização de odds Betfair foi às 14:30. São 14:37 (7 minutos sem atualização). CB-004 ativa. Sistema bloqueia novas apostas. Operador investiga: problema de internet? API Betfair down? Manutenção programada?

**Reset Automático:** Quando o feed volta a atualizar normalmente por 10 minutos consecutivos, o sistema retoma. Isto garante que o feed está estável antes de confiar nele novamente.

---

### 4.5 CB-005: Erros Execução

**Objetivo:** Proteger contra falhas sistêmicas na execução de apostas. Mais de 3 erros de execução num dia indica problema técnico sério — API instável, credenciais expiradas, problema de conta, ou bug de software — que pode causar perdas se não for corrigido imediatamente.

**Lógica:** Quando o contador de erros de execução excede 3 num período de 24 horas, o sistema para completamente. Não é apenas pausa, é paragem total. Erros de execução podem incluir: falha ao colocar aposta, timeout de API, erro de autenticação, saldo insuficiente, ou odds mudadas entre sinal e execução.

**Exemplo Prático:** 09:00 = erro timeout API, 12:00 = erro odds changed, 15:00 = erro authentication failed. CB-005 ativa. Sistema para completamente. Operador deve investigar e corrigir o problema raiz antes de retomar.

**Reset Automático:** Não há reset automático. Requer revisão manual e correção do problema. Após correção, operador deve documentar a causa e a solução em audit log antes de reset manual aprovado por Risk Manager.

---

### 4.6 CB-006: Exposição Máxima

**Objetivo:** Proteger contra concentração excessiva de risco em curto período. Apostar mais de 12% da banca num dia é agressivo mesmo para um sistema com edge comprovado, e aumenta significativamente a probabilidade de drawdown severo se todos os sinais do dia falharem.

**Lógica:** Quando a exposição total diária (soma de todos os stakes do dia) excede 12% da banca atual, novos sinais são rejeitados automaticamente. Isto não afeta apostas já colocadas, apenas impede novas apostas até o dia seguinte.

**Exemplo Prático:** Banca = €5,000. Apostas do dia: €300 + €250 + €200 = €750 (15% da banca). CB-006 ativa. Novo sinal de €150 é rejeitado. Sistema avisa: "Exposição diária atingida. Novas apostas retomam amanhã."

**Reset Automático:** Reset automático no início de cada nova sessão (dia seguinte). Isto é uma "reset diária" natural que permite recomeçar com exposição limpa.

---

### 4.7 CB-007: Modelo Stale

**Objetivo:** Proteger contra o uso de um modelo desatualizado que pode ter sofrido drift não detetado. Modelos de machine learning degradam ao longo do tempo à medida que o mercado muda, lesões ocorrem, estratégias de times evoluem, etc. Um modelo não atualizado por 7+ dias é potencialmente obsoleto.

**Lógica:** Quando o modelo em produção não foi atualizado (retrained) por mais de 7 dias, o sistema para de gerar novas apostas. Isto força retraining regular e garante que o modelo reflete padrões recentes de mercado.

**Exemplo Prático:** Último retraining foi há 10 dias. CB-007 ativa. Sistema para. Operador deve executar pipeline de retraining com dados recentes antes de retomar.

**Reset Automático:** Não há reset automático. Requer retraining manual do modelo com dados atualizados. Após retraining bem-sucedido e validação, operador pode reset manual.

---

### 4.8 CB-008: Drift Severo

**Objetivo:** Proteger contra mudanças drásticas na distribuição de features que indicam que o modelo treinado em dados históricos não é mais aplicável ao ambiente atual. PSI (Population Stability Index) > 0.30 indica mudança severa na distribuição de uma ou mais features.

**Lógica:** Quando o PSI agregado de features principais excede 0.30, o sistema pausa e inicia análise automática de drift. Isto pode indicar mudança de regime de mercado, nova regra de NBA, mudança em como as casas de apostas precificam, ou outro evento estrutural.

**Exemplo Prático:** Feature "pontos médios últimos 5 jogos" tem PSI de 0.45 (mudança severa). CB-008 ativa. Sistema pausa. Investigação revela que a NBA mudou regras de ofensa ou há nova tendência estratégica na liga que o modelo não captura.

**Reset Automático:** Não há reset automático. Requer investigação manual da causa do drift, possível reengenharia de features, retraining do modelo, e validação antes de reset manual aprovado por Quant Lead.

---

## 5. HIERARQUIA DE SEVERIDADE

### 5.1 CRITICAL

Circuit breakers CRITICAL devem resultar em paragem imediata e notificação via múltiplos canais (Telegram + Email). Representam ameaças diretas à sobrevivência da banca ou integridade do sistema.

- CB-001: Drawdown Crítico
- CB-004: Feed Offline
- CB-005: Erros Execução
- CB-008: Drift Severo

**Protocolo:**
1. Paragem imediata de operações
2. Notificação Telegram CRITICAL
3. Notificação Email para todos os stakeholders
4. Requer intervenção humana obrigatória
5. Reset manual apenas após investigação e aprovação

---

### 5.2 HIGH

Circuit breakers HIGH resultam em pausa ou restrição significativa, mas não necessariamente paragem total. Representam problemas sérios que requerem atenção urgente.

- CB-002: Sequência Perdas
- CB-003: Edge Zero
- CB-007: Modelo Stale

**Protocolo:**
1. Pausa ou restrição de operações
2. Notificação Telegram HIGH
3. Investigação obrigatória
4. Reset automático possível se condição resolvida
5. Reset manual requer justificação

---

### 5.3 MEDIUM

Circuit breakers MEDIUM resultam em restrições moderadas ou warnings. Representam situações que requerem monitorização aumentada mas não necessariamente paragem.

- CB-006: Exposição Máxima

**Protocolo:**
1. Restrição seletiva (rejeitar novos sinais)
2. Notificação Telegram MEDIUM
3. Monitorização aumentada
4. Reset automático por período natural (dia seguinte)

---

## 6. IMPLEMENTAÇÃO

A implementação deve seguir esta arquitetura de classes para garantir modularidade, testabilidade e manutenibilidade:

### 6.1 Sistema Central

O sistema central coordena todos os circuit breakers, verificando cada um sequencialmente a cada intervalo definido (ex: a cada 30 segundos). Mantém estado de quais breakers estão ativos, notifica stakeholders quando necessário, e implementa lógica de reset.

### 6.2 Breakers Individuais

Cada circuit breaker é implementado como uma classe independente com métodos padronizados:
- `should_trigger(state)`: Retorna True se condição de trigger é satisfeita
- `get_action()`: Retorna a ação a ser executada
- `can_reset(state)`: Retorna True se condições de reset são satisfeitas
- `get_severity()`: Retorna severidade (CRITICAL/HIGH/MEDIUM)

### 6.3 Audit Log

Todas as ativações, resets e tentativas de sobreposição são registadas com timestamp completo, métricas que causaram o trigger, ação tomada, responsável, e justificação. Este log é imutável e armazenado em tabela dedicada do PostgreSQL.

---

## 7. AUDIT LOG

Cada evento de circuit breaker é registado com os seguintes campos:

- **timestamp:** Data e hora exata do evento
- **breaker_id:** Identificador do circuit breaker (CB-001, etc.)
- **condition_value:** Valor da métrica que causou o trigger
- **action_taken:** Ação executada pelo sistema
- **state_before:** Estado do sistema antes do trigger
- **state_after:** Estado do sistema após o trigger
- **reset_by:** Responsável pelo reset ('auto' ou 'manual:user_id')
- **justification:** Justificação para reset manual (se aplicável)

---

## 8. PROCEDIMENTOS OPERACIONAIS

### 8.1 Ativação de Circuit Breaker

Quando um circuit breaker ativa:
1. Sistema executa ação imediata automaticamente
2. Notificação enviada via canais apropriados
3. Evento registado em audit log
4. Dashboard atualizado para mostrar breaker ativo
5. Se severidade CRITICAL/HIGH, operador notificado para investigação

### 8.2 Reset Automático

Circuit breakers com reset automático verificam periodicamente (ex: a cada 5 minutos) se condições de reset são satisfeitas. Se sim, reset automaticamente e notifica stakeholders.

### 8.3 Reset Manual

Para circuit breakers sem reset automático, o processo é:
1. Operador investiga e corrige problema raiz
2. Operador documenta causa e solução
3. Operador solicita reset via dashboard
4. Risk Manager aprova ou rejeita
5. Se aprovado, reset executado e registado em audit log
6. Se rejeitado, motivo documentado e investigação continua

---

## 9. BACKLOG TÉCNICO

- [ ] Implementar todos os 8 circuit breakers com classes modulares
- [ ] Criar testes de stress para cada breaker
- [ ] Implementar dashboard em tempo real de circuit breakers
- [ ] Configurar notificações multi-canal (Telegram, Email, Slack)
- [ ] Documentar SOP detalhado de reset manual para cada breaker
- [ ] Implementar simulações de cenários de falha para treino de operadores
- [ ] Criar relatórios mensais de ativação de circuit breakers
- [ ] Implementar alertas de "near-miss" (quando condição está a 80% do trigger)

---

## 10. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]] ← Secção mãe
- [[10_Monitoring/INDEX]] → Dashboard de circuit breakers
- [[08_Risk_Management/DRAWDOWN_CONTROL]] → Detalhes sobre drawdown
- [[08_Risk_Management/BANKROLL_SURVIVAL]] → Análise de sobrevivência
