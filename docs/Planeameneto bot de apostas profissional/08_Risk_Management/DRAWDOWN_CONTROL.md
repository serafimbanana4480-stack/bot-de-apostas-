# DRAWDOWN_CONTROL — Gestão de Drawdown

**ID:** `RM-002` | **Fase:** #phase/2-4 | **Owner:** Risk Manager | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar um sistema sistemático de gestão de drawdown que protege a banca de perdas catastróficas através de redução dinâmica de exposição, pausas forçadas e análise contínua. Drawdown é a medida de queda acumulada desde o pico histórico da banca e é o indicador mais importante de risco de curto prazo. O objetivo não é evitar drawdowns completamente — isso é impossível em qualquer sistema com variância — mas gerenciá-los de forma que sejam temporários e não ameacem a sobrevivência da banca.

---

## 2. DEFINIÇÕES FUNDAMENTAIS

### 2.1 Drawdown Atual

O drawdown atual representa a percentagem de queda desde o pico histórico da banca até o valor atual. É calculado como:

```
Drawdown Atual = (Banca Pico - Banca Atual) / Banca Pico
```

Por exemplo, se a banca atingiu um pico de €10,000 e agora está em €8,500, o drawdown atual é (10,000 - 8,500) / 10,000 = 15%.

### 2.2 Max Drawdown

O max drawdown é o maior drawdown já experimentado historicamente. É uma medida importante da volatilidade passada e serve como referência para entender o que é "normal" para o sistema. Se o drawdown atual se aproxima do max drawdown histórico, isso indica que estamos a experimentar uma das piores sequências já vistas.

### 2.3 Recovery Time

O recovery time é o tempo necessário para a banca recuperar de um drawdown e atingir um novo pico. Recovery times longos são problemáticos porque significam que o capital está "preso" em recuperação em vez de gerar novo lucro. Recovery times muito longos podem indicar que o modelo perdeu edge ou que o regime de mercado mudou.

### 2.4 Drawdown Relativo vs Absoluto

O drawdown relativo (percentual) é mais útil que o drawdown absoluto (valor monetário) porque é independente do tamanho da banca. Um drawdown de €500 é significativo numa banca de €1,000 (50%) mas irrelevante numa banca de €100,000 (0.5%). Por esta razão, todos os circuit breakers de drawdown são baseados em percentuais, não em valores absolutos.

---

## 3. PSICOLOGIA DO DRAWDOWN

### 3.1 O Perigo do "Tilt"

Quando ocorre um drawdown significativo, especialmente rápido, os operadores humanos tendem a experimentar "tilt" emocional — uma resposta psicológica que leva a decisões irracionais. Sintomas comuns de tilt incluem:

- Aumentar stakes para "recuperar as perdas" (chasing losses)
- Ignorar sinais do sistema porque "o modelo está errado"
- Fazer apostas manuais fora do sistema para "compensar"
- Duvidar de todo o sistema baseado em resultados de curto prazo

O sistema de gestão de drawdown é desenhado especificamente para contrariar estes impulsos emocionais através de regras automáticas que não podem ser sobrepostas por decisão humana.

### 3.2 Ilusão de Controlo

Durante drawdowns, operadores frequentemente acreditam erroneamente que podem "controlar" o resultado através de intervenção manual. Esta ilusão de controlo é perigosa porque remove a disciplina sistemática que torna o sistema lucrativo a longo prazo. Os circuit breakers de drawdown reforçam que o sistema, não o operador, está no controlo.

### 3.3 Viés de Recência

O viés de recência faz com que operadores overreactem a resultados recentes, dando-lhes peso desproporcional. Três perdas consecutivas podem parecer catastróficas quando estatisticamente são normais. O sistema de gestão de drawdown usa janelas de tempo mais longas (48h, 7 dias) para evitar reações excessivas a ruído de curto prazo.

---

## 4. NÍVEIS DE DRAWDOWN E RESPOSTAS

### 4.1 Nível Verde (0-5% Drawdown)

**Condição:** Drawdown entre 0% e 5% desde o pico.

**Interpretação:** Variação normal esperada. Não há motivo para preocupação.

**Ação:** Nenhuma. Operação normal com Kelly fracionado padrão (meio Kelly).

**Monitorização:** Monitorização padrão. Nenhum alerta adicional.

---

### 4.2 Nível Amarelo (5-10% Drawdown)

**Condição:** Drawdown entre 5% e 10% desde o pico.

**Interpretação:** Variação elevada mas ainda dentro de limites aceitáveis. Pode indicar período de baixa performance ou má sorte estatística.

**Ação:** Aumentar monitorização mas manter stakes normais. Revisar métricas de CLV e drift para verificar se há problema sistêmico.

**Monitorização:** Alerta LOW no dashboard. Revisão diária de métricas.

---

### 4.3 Nível Laranja (10-15% Drawdown)

**Condição:** Drawdown entre 10% e 15% desde o pico.

**Interpretação:** Drawdown significativo que requer atenção. Pode indicar problema de modelo, mudança de regime, ou sequência estatisticamente improvável de más decisões.

**Ação:** Reduzir stakes em 25% (Kelly multiplicado por 0.75). Aumentar frequência de revisão de métricas. Considerar pausa temporária se drawdown continuar a piorar.

**Monitorização:** Alerta MEDIUM via Telegram. Revisão de métricas a cada 4 horas. Investigação de causas possíveis.

---

### 4.4 Nível Vermelho (>15% Drawdown)

**Condição:** Drawdown superior a 15% desde o pico.

**Interpretação:** Drawdown crítico que ameaça sobrevivência. Indica problema sério que requer intervenção imediata e redução drástica de exposição.

**Ação:** Reduzir stakes em 50% (Kelly multiplicado por 0.5). Pausa de novas apostas até investigação completa. Revisão obrigatória de todas as componentes do sistema (dados, modelo, execução).

**Monitorização:** Alerta CRITICAL via Telegram + Email. Revisão imediata por Risk Manager. Análise post-mortem obrigatória após recuperação.

**Reset:** Stakes só podem ser restaurados ao nível anterior após drawdown cair abaixo de 10% e permanecer abaixo por 48 horas consecutivas.

---

## 5. CIRCUIT BREAKERS DE DRAWDOWN

### 5.1 Alpha: Drawdown Crítico

| Trigger | Condição | Ação | Recovery |
|---------|----------|------|----------|
| Alpha | Drawdown > 15% desde pico | Reduzir stakes 50% | Drawdown < 10% por 48h |

**Objetivo:** Proteção imediata contra perdas catastróficas. Redução de 50% em stakes reduz a velocidade de perdas e dá tempo para investigação sem expor a banca a ruína.

**Implementação:** Quando o drawdown excede 15%, o fator de Kelly é multiplicado por 0.5 automaticamente. Se estava a usar meio Kelly (0.5), passa para quarter Kelly (0.25). Esta redução é aplicada imediatamente a todas as novas apostas.

**Exemplo:** Banca pico = €10,000, Banca atual = €8,200 (DD = 18%). Stake que seria €100 torna-se €50. Se drawdown continuar a piorar para 20%, stake reduz novamente para €25.

---

### 5.2 Beta: Sequência de Perdas

| Trigger | Condição | Ação | Recovery |
|---------|----------|------|----------|
| Beta | 5 perdas consecutivas | Pausa 1h + alerta ops | Revisão manual obrigatória |

**Objetivo:** Proteger contra tilt emocional e possíveis falhas sistêmicas. Cinco perdas consecutivas são estatisticamente improváveis (probabilidade ≈ 3% para win rate de 55%) e podem indicar problema técnico ou mudança de regime.

**Implementação:** Quando cinco apostas consecutivas resultam em perda, o sistema pausa todas as novas apostas por uma hora. Esta pausa forçada permite investigação calma: verificar logs de erro, verificar feeds de dados, verificar notícias de lesões, verificar se há problema com o modelo.

**Exemplo:** Apostas às 13:00, 14:30, 16:00, 18:30, 20:00 = todas perdas. Sistema pausa até 21:00. Operador investiga durante a hora: verifica se há problema com API, verifica se dados de odds estão corretos, verifica se há lesões de jogadores que o modelo não capturou.

---

### 5.3 Gamma: Edge Zero

| Trigger | Condição | Ação | Recovery |
|---------|----------|------|----------|
| Gamma | CLV 3d < 0% | Pausa novas apostas | CLV 3d > 1% por 24h |

**Objetivo:** Proteger contra perda de vantagem matemática. CLV negativo significa que estamos a apostar a odds piores que as odds de fecho do mercado — não temos edge matemático e a longo prazo perderemos.

**Implementação:** Quando o CLV médio dos últimos 3 dias cai abaixo de 0%, o sistema para de gerar novas apostas. Isto é diferente de um drawdown — podemos estar a ganhar dinheiro por sorte (variação positiva) mas se CLV é negativo, a longo prazo perderemos.

**Exemplo:** Últimas 50 apostas têm CLV médio de -0.5%. Isto significa que em média apostamos a odds piores que o mercado. O mercado está mais informado ou mais eficiente que nós. Sistema para até que CLV recupere para positivo.

**Reset:** Quando CLV médio de 3 dias excede 1% por 24 horas consecutivas, sistema retoma. A margem de 1% evita ativações/desativações oscilantes em torno de zero.

---

### 5.4 Delta: Feed Offline

| Trigger | Condição | Ação | Recovery |
|---------|----------|------|----------|
| Delta | Feed falha > 5 min | Sem novas apostas | Feed OK por 10 min |

**Objetivo:** Proteger contra apostas baseadas em dados desatualizados. Se o feed de odds está offline por mais de 5 minutos, não podemos garantir que as odds que vemos são atualizadas e confiáveis.

**Implementação:** Quando o sistema deteta que não há atualização de odds por mais de 5 minutos, todas as novas apostas são bloqueadas. Isto evita apostar a odds "stale" que podem ter mudado significativamente.

**Exemplo:** Última atualização de odds Betfair foi às 14:30. São 14:37 (7 minutos sem atualização). Sistema bloqueia novas apostas. Operador investiga: problema de internet? API Betfair down? Manutenção programada?

---

### 5.5 Epsilon: Erro Execução

| Trigger | Condição | Ação | Recovery |
|---------|----------|------|----------|
| Epsilon | Erro execucao > 3x/dia | Paragem total | Fix + teste shadow |

**Objetivo:** Proteger contra falhas sistêmicas na execução. Mais de 3 erros num dia indica problema técnico sério que pode causar perdas se não for corrigido.

**Implementação:** Quando o contador de erros de execução excede 3 num período de 24 horas, o sistema para completamente. Erros podem incluir: falha ao colocar aposta, timeout de API, erro de autenticação, saldo insuficiente, odds mudadas.

**Exemplo:** 09:00 = erro timeout API, 12:00 = erro odds changed, 15:00 = erro authentication failed. Sistema para completamente. Operador deve investigar e corrigir problema raiz antes de retomar.

**Recovery:** Não há reset automático. Requer revisão manual e correção do problema. Após correção, operador deve documentar causa e solução em audit log antes de reset manual aprovado por Risk Manager.

---

### 5.6 Zeta: Exposição Diária

| Trigger | Condição | Ação | Recovery |
|---------|----------|------|----------|
| Zeta | Exposicao diaria > 12% | Rejeitar novos sinais | Nova sessão (dia seguinte) |

**Objetivo:** Proteger contra concentração excessiva de risco em curto período. Apostar mais de 12% da banca num dia é agressivo e aumenta significativamente probabilidade de drawdown severo se todos os sinais falharem.

**Implementação:** Quando a exposição total diária (soma de todos os stakes do dia) excede 12% da banca atual, novos sinais são rejeitados automaticamente.

**Exemplo:** Banca = €5,000. Apostas do dia: €300 + €250 + €200 = €750 (15% da banca). Novo sinal de €150 é rejeitado. Sistema avisa: "Exposição diária atingida. Novas apostas retomam amanhã."

**Recovery:** Reset automático no início de cada nova sessão (dia seguinte). É uma "reset diária" natural que permite recomeçar com exposição limpa.

---

## 6. ANÁLISE DE DRAWDOWN

### 6.1 Causas Comuns de Drawdown

**Causa 1: Variação Estatística Normal**
- Mesmo com edge positivo, sequências de perdas são inevitáveis
- Um modelo com 55% de win rate ainda tem 45% de perdas
- Sequências de 5-10 perdas são estatisticamente esperadas ocasionalmente
- **Ação:** Manter disciplina, não alterar stakes, esperar que a variância normalize

**Causa 2: Mudança de Regime de Mercado**
- NBA muda regras (ex: nova regra de faltas)
- Estratégias de times mudam (ex: mais three-pointers)
- Casas de apostas mudam precificação
- **Ação:** Investigar mudanças, reengenhar features se necessário, retreinar modelo

**Causa 3: Drift de Modelo**
- Features degradam em relevância ao longo do tempo
- Modelo overfitted a dados históricos específicos
- PSI de features aumenta significativamente
- **Ação:** Retreinar modelo com dados recentes, remover features obsoletas, adicionar novas features

**Causa 4: Problemas de Dados**
- Feed de odds instável ou desatualizado
- Dados de estatísticas incorretos ou incompletos
- Lesões não reportadas em tempo útil
- **Ação:** Corrigir pipeline de dados, adicionar validações, implementar redundância

**Causa 5: Problemas de Execução**
- Latência excessiva entre sinal e execução
- Slippage maior que o esperado
- Fill rate baixo (sinais não executados)
- **Ação:** Otimizar pipeline de execução, mudar para APIs mais rápidas, ajustar thresholds

---

### 6.2 Diagnóstico de Drawdown

Quando ocorre um drawdown significativo, seguir este processo de diagnóstico sistemático:

**Passo 1: Verificar Métricas de Edge**
- CLV médio ainda positivo? Se sim, drawdown provavelmente é variação normal
- CLV caiu significativamente? Se sim, pode haver problema de modelo ou dados
- Win rate dentro de intervalo de confiança esperado? Se não, investigar

**Passo 2: Verificar Métricas de Drift**
- PSI de features principais está aumentando? Se sim, features podem estar obsoletas
- Alguma feature específica tem PSI muito alto? Investigar essa feature
- Distribuição de predições mudou? Se sim, calibração pode estar errada

**Passo 3: Verificar Qualidade de Dados**
- Feed de odds está atualizado? Verificar timestamps
- Estatísticas de times estão corretas? Amostragem manual
- Há missing values inesperados? Verificar logs de pipeline

**Passo 4: Verificar Execução**
- Latência média aumentou? Se sim, investigar performance de API
- Slippage médio aumentou? Se sim, pode haver problema com timing
- Fill rate caiu? Se sim, verificar se odds estão mudando rápido demais

**Passo 5: Verificar Contexto de Mercado**
- Há mudanças de regras na NBA? Verificar notícias
- Há mudanças de estratégias predominantes? Analisar tendências de liga
- Há eventos externos (lesões de estrelas, trades)? Verificar news

---

## 7. RECUPERAÇÃO DE DRAWDOWN

### 7.1 Estratégias de Recuperação

**Estratégia 1: Paciência e Disciplina**
- Manter stakes reduzidos até drawdown recuperar significativamente
- Não tentar "recuperar rápido" aumentando stakes
- Confiança no sistema a longo prazo, não em resultados de curto prazo
- Recuperação natural é preferível a recuperação forçada

**Estratégia 2: Análise e Melhoria**
- Usar drawdown como oportunidade para análise profunda
- Identificar causas raiz e implementar melhorias
- Testar melhorias em paper trading antes de produção
- Documentar learnings para evitar repetição

**Estratégia 3: Ajuste Conservador**
- Se drawdown foi causado por problema sistêmico, corrigir antes de retomar
- Considerar reduzir Kelly fracionado permanentemente se drawdowns são frequentes
- Aumentar margens de segurança (ex: aumentar threshold de CLV)
- Implementar circuit breakers adicionais se apropriado

---

### 7.2 Métricas de Recuperação

**Tempo de Recuperação**
- Medido desde o início do drawdown até o novo pico
- Target: < 30 dias para drawdowns < 15%
- Target: < 60 dias para drawdowns 15-20%
- Se tempo de recuperação excede targets, investigar se há problema estrutural

**Taxa de Recuperação**
- Velocidade de recuperação medida como % de drawdown recuperado por dia
- Target: > 2% de drawdown recuperado por dia após estabilização
- Se taxa de recuperação é muito lenta, pode indicar edge reduzido

**Qualidade de Recuperação**
- Recuperação é sustentável ou volátil?
- Se banca recupera mas volta a cair rapidamente, há problema cíclico
- Se recuperação é estável e sustentável, sistema está saudável

---

## 8. MONTE CARLO DE SOBREVIVÊNCIA

### 8.1 Objetivo

Simulações Monte Carlo são usadas para estimar a probabilidade de ruína (probabilidade de a banca cair a zero ou abaixo de um threshold crítico) sob diferentes cenários de edge, stake sizing e drawdown. Estas simulações permitem tomar decisões informadas sobre quão agressivo ou conservador ser.

### 8.2 Metodologia

A simulação executa milhares de trajetórias possíveis da banca ao longo do tempo, assumindo:
- Edge específico (ex: 3% CLV médio)
- Win rate derivada do edge
- Stake sizing específico (ex: 2% da banca por aposta)
- Número de apostas (ex: 1000 apostas)

Para cada trajetória, o sistema simula cada aposta como win ou loss baseado na probabilidade, atualiza a banca, e verifica se a banca caiu abaixo do threshold de ruína.

### 8.3 Interpretação de Resultados

Se a simulação mostra probabilidade de ruína de 5% com edge de 3% e stake de 2%, isso significa que em 5% das simulações a banca caiu abaixo do threshold de ruína. Se este risco é considerado inaceitável, reduzir stake (ex: para 1%) ou aumentar edge (melhorando o modelo) reduzirá a probabilidade de ruína.

---

## 9. BACKLOG TÉCNICO

- [ ] Implementar circuit breakers automáticos de drawdown
- [ ] Criar dashboard de drawdown em tempo real com visualizações
- [ ] Implementar sistema de diagnóstico automático de causas de drawdown
- [ ] Simular cenários de ruína com parâmetros reais do sistema
- [ ] Criar relatórios mensais de análise de drawdown
- [ ] Implementar alertas preditivos de drawdown (quando tendência indica drawdown iminente)
- [ ] Adicionar métricas de qualidade de recuperação ao dashboard
- [ ] Criar templates de análise post-mortem para drawdowns significativos

---

## 10. LINKS CRUZADOS

- [[08_Risk_Management/INDEX]] ← Secção mãe
- [[08_Risk_Management/KELLY_FRACIONADO]] → Sizing base
- [[08_Risk_Management/BANKROLL_SURVIVAL]] → Análise de sobrevivência detalhada
- [[08_Risk_Management/CIRCUIT_BREAKERS]] → Circuit breakers gerais
