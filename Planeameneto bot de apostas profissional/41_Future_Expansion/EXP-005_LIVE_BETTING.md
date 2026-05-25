# EXP-005 — Live Betting (In-Play)

**ID:** `EXP-005` | **Fase:** #phase/9-14 | **Owner:** Product Manager / Strategy Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Implementar sistema de value betting para apostas em tempo real (live/in-play), capitalizando na volatilidade de odds durante eventos e na ineficiência causada por reações emocionais do mercado.

---

## 2. CONTEXTO

Live betting consiste em apostar durante o desenrolar de um evento desportivo, com odds atualizadas em tempo real baseadas no estado atual do jogo.

**Características do Live Betting:**
- **Odds voláteis**: Mudam drasticamente a cada segundo
- **Alta frequência**: Milhares de oportunidades por evento
- **Reação emocional**: Mercado overreact a eventos recentes
- **Informação assimétrica**: Quem assiste tem vantagem
- **Latência crítica**: Segundos fazem diferença
- **Maior edge potencial**: Mercados menos eficientes

**Por que Live Betting é atrativo:**
- Edge potencial muito maior que pre-match
- Overreaction do mercado a eventos recentes
- Recency bias dos apostadores
- Informação em tempo real não incorporada nas odds
- Volume massivo de oportunidades

**Desafios significativos:**
- Requer streaming de dados em tempo real
- Latência crítica (milissegundos importam)
- Complexidade de modelagem muito maior
- Requer features em tempo real
- Infraestrutura mais cara e complexa
- Maior risco de erro de execução

---

## 3. ANÁLISE DE MERCADO

### 3.1 Volume e Liquidez

| Desporto | Volume Live | Liquidez | Edge Potencial | Complexidade |
|----------|-------------|----------|----------------|--------------|
| NBA | Muito Alto | Muito Alta | Alto | Alta |
| NFL | Alto | Alta | Muito Alto | Muito Alta |
| Ténis | Alto | Alta | Muito Alto | Muito Alta |
| Futebol | Muito Alto | Alta | Alto | Alta |
| Esports | Médio-Alto | Média | Muito Alto | Extrema |

### 3.2 Mercados Live Disponíveis

**Mercados Principais:**
- Moneyline atualizado
- Spread/Hadicape atualizado
- Totals atualizados
- Next team to score
- Winner of next quarter/set/period

**Mercados de Prop:**
- Next 3-point shot made
- Next team to score 10 points
- Player performance props em tempo real
- Team to win next possession

**Mercados Especiais:**
- Method of next score
- Exact score em tempo real
- Race to X points

### 3.3 Eficiência de Mercado

- **Pre-match**: Relativamente eficiente (especialmente closing lines)
- **Live**: Muito menos eficiente
- **Imediatamente após eventos**: Extremamente ineficiente (overreaction)
- **Final de períodos**: Ineficiente (recency bias)
- **Momentum situations**: Ineficiente (overestimado)

---

## 4. ARQUITETURA DO SISTEMA

### 4.1 Componentes Principais

**Data Streaming Layer:**
- Streaming de dados em tempo real (WebSocket, SSE)
- Play-by-play data (cada ponto, jogada, evento)
- Odds streaming (atualizações milissegundos)
- Sincronização temporal precisa

**Feature Engineering Real-Time:**
- Features de estado atual (score, tempo, posse)
- Features de momentum (últimos eventos)
- Features de performance recente (últimos 5 min)
- Features de contexto (fatigue, lesões durante jogo)

**Prediction Engine:**
- Modelo de previsão em tempo real
- Atualização contínua de probabilidades
- Calibração dinâmica
- Ensemble de modelos (pre-match + live)

**Execution Engine:**
- Detecção de valor em tempo real
- Priorização de oportunidades
- Execução ultra-rápida (< 500ms)
- Gestão de stakes dinâmica

**Risk Management:**
- Circuit breakers para situações extremas
- Limites de exposição
- Gestão de latência
- Proteção contra odds stale

### 4.2 Fluxo de Dados

```
1. Streaming de play-by-play (freq: 100-1000ms)
2. Streaming de odds (freq: 50-500ms)
3. Feature engineering em tempo real
4. Atualização de modelo
5. Cálculo de probabilidades
6. Comparação com odds do mercado
7. Deteção de valor
8. Execução (se valor > threshold)
9. Monitorização e logging
```

### 4.3 Requisitos de Latência

- **Data streaming**: < 100ms
- **Feature engineering**: < 50ms
- **Prediction**: < 100ms
- **Detecção de valor**: < 50ms
- **Execução**: < 200ms
- **Latência total**: < 500ms ideal (máximo 1s)

---

## 5. REQUISITOS DE DADOS

### 5.1 Dados em Tempo Real

**Play-by-Play Data:**
- Score atual (preciso)
- Tempo/jogada atual
- Possession
- Últimos eventos (pontos, turnovers, etc.)
- Estatísticas acumuladas (shots, turnovers, etc.)
- Substituições/lesões durante jogo
- Momentum indicators

**Odds Streaming:**
- Odds atualizadas em tempo real
- Volume de liquidez
- Timestamps precisos
- Histórico de movimentos de odds

**Contexto em Tempo Real:**
- Fadiga (minutos jogados, dias de descanso)
- Lesões durante jogo
- Condições climáticas (se outdoor)
- Atmosfera do estádio (se disponível)

### 5.2 Fontes de Dados

**NBA:**
- NBA Stats API (play-by-play)
- Betfair Streaming (odds)
- Sportradar (premium feed)

**NFL:**
- NFL Game Pass (play-by-play)
- Betfair Streaming
- Stats Perform

**Ténis:**
- ATP/WTA APIs
- Tennis Abstract (live stats)
- Betfair Streaming

**Esports:**
- Riot Games API (LoL)
- Valve API (CS)
- Strafe/GamerLegion

### 5.3 Volume de Dados

- **Freqüência**: 100-1000ms updates
- **Eventos simultâneos**: 10-50 jogos
- **Dados por segundo**: ~10-50KB
- **Armazenamento**: ~500GB/mês para dados históricos

---

## 6. ABORDAGEM DE MODELAGEM

### 6.1 Features em Tempo Real

**Features de Estado Atual:**
- Score difference
- Tempo/jogada restante
- Possession
- Field court position
- Timeout remaining

**Features de Momentum:**
- Últimos 5 eventos (pontos, turnovers)
- Run atual (pontos consecutivos)
- Momentum score (baseado em eventos recentes)
- Recency bias adjustment

**Features de Performance Recente:**
- Field goal % últimos 5 min
- Turnovers últimos 5 min
- Offensive/defensive rating últimos 5 min
- Efficiency metrics em janela móvel

**Features de Fadiga:**
- Minutos jogados por jogador
- Dias de descanso
- Back-to-back games
- Travel fatigue

**Features de Contexto:**
- Lesões durante jogo
- Substituições
- Condições climáticas
- Atmosfera do estádio

### 6.2 Estratégia de Modelagem

**Fase 1 (Baseline - Momentum):**
- Modelo simples baseado em momentum
- Features: score diff, últimos eventos, tempo
- Focar em overreactions após runs
- Backtest em dados históricos de live

**Fase 2 (Avançado):**
- Adicionar features granulares (performance recente)
- Modelo ensemble (pre-match + live)
- Calibração dinâmica por situação
- Incorporar machine learning em tempo real

**Fase 3 (Especializado):**
- Modelos específicos por situação (clutch, garbage time)
- Player-level modeling
- Prop bets live
- Cross-sport models

### 6.3 Desafios Específicos de Live Betting

- **Latência crítica**: Milissegundos importam
- **Overfitting a situações específicas**: Cada jogo é único
- **Dados não estacionários**: Distribuições mudam durante jogo
- **Feature drift**: Features perdem poder preditivo
- **Complexidade extrema**: Muitas variáveis em tempo real
- **Custo de infraestrutura**: Requer hardware potente

---

## 7. VALIDAÇÃO E BACKTESTING

### 7.1 Período de Backtest

- **Training**: 2021-2022 (2 temporadas)
- **Validation**: 2023 (1 temporada)
- **Test**: 2024 (1 temporada)

### 7.2 Backtest em Tempo Real

**Desafio**: Backtest de live betting é diferente porque requer simulação de execução em tempo real.

**Abordagem:**
- Usar dados históricos de play-by-play com timestamps
- Simular execução em cada timestamp
- Considerar latência de execução
- Usar odds históricas em cada timestamp
- Validar que execução seria possível (não odds stale)

### 7.3 Métricas de Sucesso

- **Edge mínimo**: 4-6% em closing line value (mais alto que pre-match)
- **ROI alvo**: 8-12% (devido à maior volatilidade)
- **Sharpe ratio**: > 1.2 (aceitando maior volatilidade)
- **Max drawdown**: < 30%
- **Number of bets**: 5,000-10,000 por ano (volume muito alto)
- **Execution success rate**: > 95%

### 7.4 Testes de Robustez

- Performance por situação (clutch, normal, garbage time)
- Performance por momento do jogo (1Q vs 4Q)
- Performance após runs de pontos
- Sensibilidade a latência de execução
- Performance em diferentes desportos

---

## 8. IMPLEMENTAÇÃO

### 8.1 Fase 1: MVP Live Betting (4-6 meses)

- Coleta de dados históricos de play-by-play
- Pipeline de streaming em tempo real
- Feature engineering básico em tempo real
- Modelo baseline (momentum-based)
- Backtest em dados históricos
- Documentação de resultados

### 8.2 Fase 2: Produção Piloto (3-4 meses)

- Integração com sistema existente
- Streaming de dados em tempo real
- Execução manual semi-automatizada
- Monitorização de latência
- Ajustes baseados em resultados reais
- Validação de edge em produção

### 8.3 Fase 3: Automatização Completa (2-3 meses)

- Execução totalmente automatizada
- Otimização de latência
- Modelos avançados ensemble
- Expansão para mais desportos
- Prop bets live

### 8.4 Fase 4: Otimização (contínuo)

- Machine learning em tempo real
- Modelos específicos por situação
- Cross-sport expansion
- Advanced features (player tracking, etc.)

---

## 9. RISCOS E MITIGAÇÃO

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Latência insuficiente | Alta | Muito Alto | Infraestrutura otimizada, edge computing |
| Odds stale | Muito Alta | Alto | Validação de odds, timeout curto |
| Overfitting a situações | Alta | Alto | Cross-validation temporal, regularização |
| Custo de infraestrutura | Média | Alto | Cloud auto-scaling, otimização de código |
| Dados não estacionários | Alta | Alto | Modelos adaptativos, retraining contínuo |
| Edge inexistente | Média | Alto | Backtest rigoroso, piloto em produção |
| Erro de execução | Média | Alto | Circuit breakers, validação antes de execução |

---

## 10. CUSTOS E INVESTIMENTO

### 10.1 Custos Iniciais

- **Desenvolvimento**: 6-9 meses de desenvolvimento
- **Infraestrutura**: Servidor de alta performance, bandwidth
- **Dados**: Subscriptions premium para streaming
- **Capital**: Bankroll para testes (recomendado: $5K-$10K)

### 10.2 Custos Recorrentes

- **Infraestrutura**: $200-$500/mês (servidor de alta performance)
- **Dados**: $300-$1,000/mês (streaming premium)
- **Manutenção**: Tempo contínuo para debugging e otimização

### 10.3 Retorno Esperado

- **Edge potencial**: 4-8% (maior que pre-match)
- **Volume**: 5,000-10,000 apostas/ano
- **ROI alvo**: 8-12%
- **Lucro potencial**: Significativamente maior que pre-match

*Nota: Retornos são conservadores e dependem de qualidade de execução*

---

## 11. DEPENDÊNCIAS

- **Dados em tempo real**: Acesso a streaming de play-by-play e odds
- **Infraestrutura**: Servidor de alta performance com baixa latência
- **Modelo**: Framework de ML adaptado para tempo real
- **Capital**: Bankroll separado para testes
- **Validação**: 6+ meses de backtest em dados históricos
- **Expertise**: Conhecimento de streaming e low-latency systems

---

## 12. CRITÉRIOS DE SUCESSO

- [ ] Edge validado em backtest (≥ 4% CLV)
- [ ] ROI positivo em backtest de 2 temporadas
- [ ] Sharpe ratio > 1.2
- [ ] Latência de execução < 500ms
- [ ] Execution success rate > 95%
- [ ] Volume de apostas ≥ 3,000/ano
- [ ] Sistema automatizado em produção
- [ ] Monitorização contínua de latência
- [ ] Documentação completa

---

## 13. BACKLOG

- [ ] Coletar dados históricos de play-by-play (2021-2024)
- [ ] Identificar e contratar provedor de streaming em tempo real
- [ ] Desenvolver pipeline de streaming (WebSocket/SSE)
- [ ] Implementar feature engineering em tempo real
- [ ] Desenvolver modelo baseline (momentum-based)
- [ ] Backtest em dados históricos com simulação de execução
- [ ] Analisar performance por situação (clutch, garbage time)
- [ ] Implementar sistema de deteção de valor em tempo real
- [ ] Desenvolver engine de execução ultra-rápida
- [ ] Implementar circuit breakers e gestão de risco
- [ ] Testar manualmente em produção por 2-3 meses
- [ ] Automatizar execução completa
- [ ] Otimizar latência (< 500ms)
- [ ] Expandir para mais desportos
- [ ] Documentar aprendizados e best practices

---

## 14. LINKS CRUZADOS

- [[41_Future_Expansion/INDEX]] ← Secção mãe
- [[43_Multi_Sport_Expansion/INDEX]] → Expansão multi-desporto detalhada
- [[05_Machine_Learning/INDEX]] → Framework de ML
- [[06_Backtesting/INDEX]] → Framework de backtest
- [[04_Data_Engineering/INDEX]] → Pipeline de dados
- [[09_Execution_System/INDEX]] → Sistema de execução
- [[13_Infrastructure/INDEX]] → Infraestrutura de baixa latência
- [[14_APIs/INDEX]] → APIs de streaming