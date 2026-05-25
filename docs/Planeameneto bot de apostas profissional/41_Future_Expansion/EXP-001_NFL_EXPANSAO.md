# EXP-001 — NFL Moneyline + Spread

**ID:** `EXP-001` | **Fase:** #phase/13-15 (VBQ-003) | **Owner:** Product Manager / Strategy Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Expandir o sistema de value betting para incluir NFL (National Football League), focando inicialmente em mercados de Moneyline e Spread, validando se o edge existente em NBA pode ser replicado neste desporto.

---

## 2. CONTEXTO

A NFL é o desporto mais popular nos EUA, com volumes de apostas massivos durante a temporada regular (setembro-janeiro) e playoffs. Diferente da NBA, a NFL tem:

- **Menos jogos**: 17 jogos por equipa (vs 82 na NBA)
- **Maior variância**: Menos eventos = maior impacto de cada jogo
- **Ciclo semanal**: Jogos principalmente aos domingos + segunda/thursday
- **Influência climática**: Tempo afeta significativamente o desempenho
- **Lesões mais críticas**: Cada jogador tem impacto proporcionalmente maior

A NFL apresenta oportunidades de edge porque:
- Mercados menos eficientes em jogos de menor visibilidade
- Overreaction a resultados recentes (recency bias)
- Linhas movem-se significativamente com news (lesões, tempo)
- Spreads mais estáveis que odds de moneyline

---

## 3. ANÁLISE DE MERCADO

### 3.1 Volume e Liquidez

- **Temporada regular**: ~270 jogos
- **Volume médio por jogo**: $50M-$200M (Betfair)
- **Liquidez**: Alta em jogos principais, baixa em jogos de menor visibilidade
- **Picos**: Playoffs, Super Bowl (volume 10x+)

### 3.2 Características de Mercado

| Mercado | Volume | Edge Potencial | Complexidade |
|---------|--------|----------------|--------------|
| Moneyline | Alto | Médio | Baixa |
| Spread | Muito Alto | Alto | Média |
| Totals (Over/Under) | Alto | Médio | Média |
| Props (Jogador) | Médio | Alto | Alta |
| Live/In-Play | Médio | Muito Alto | Muito Alta |

### 3.3 Eficiência de Mercado

- **Linhas de abertura**: Menos eficientes que NBA
- **Closing lines**: Mais eficientes, mas ainda com oportunidades
- **Movimento de linhas**: Mais reativo a news
- **Arbitrage**: Oportunidades limitadas mas existentes

---

## 4. REQUISITOS DE DADOS

### 4.1 Dados Necessários

- **Estatísticas de equipa**: Yards, pontos, turnovers, sacks
- **Estatísticas ofensivas/defensivas**: Por jogo, por situação
- **Histórico de lesões**: Status, impacto esperado
- **Condições climáticas**: Temperatura, vento, precipitação
- **Rest days**: Dias de descanso entre jogos
- **Travel distance**: Miles viajadas
- **Home/Away splits**: Desempenho em casa vs fora
- **Coaching changes**: Mudanças de staff tático
- **Line movement**: Histórico de movimentos de odds

### 4.2 Fontes de Dados Potenciais

- **NFL API**: Dados oficiais da liga
- **Sportradar**: Feed de dados premium
- **Stats Perform**: Advanced analytics
- **Pro-Football-Reference**: Dados históricos
- **Action Network**: Betting data e movement

### 4.3 Volume de Dados

- **Histórico**: 5-10 temporadas (2014-2024)
- **Freqüência**: Diário durante temporada
- **Latência**: < 5 segundos para odds em tempo real
- **Armazenamento**: ~50GB para dados históricos completos

---

## 5. ABORDAGEM DE MODELAGEM

### 5.1 Features Principais

**Features de Equipa:**
- PPG (Points Per Game) ofensivo/defensivo
- Yards per game (passing, rushing, total)
- Turnover differential
- Red zone efficiency
- Third down conversion rate
- Time of possession
- Penalties por jogo

**Features de Contexto:**
- Rest days (dias de descanso)
- Travel distance (milhas)
- Weather conditions (temperatura, vento, chuva/neve)
- Injuries (número de jogadores key out)
- Home field advantage (ajustado por estádio)
- Motivation (playoff race, division implications)

**Features de Mercado:**
- Opening line vs current line
- Line movement direction e magnitude
- Public betting percentage
- Sharp money indicators
- Historical line movement patterns

### 5.2 Estratégia de Modelagem

**Fase 1 (Baseline):**
- Modelo XGBoost similar ao NBA
- Features simples (PPG, YPG, home/away)
- Target: Moneyline e Spread separadamente
- Backtest em 3 temporadas

**Fase 2 (Avançado):**
- Adicionar features contextuais (weather, injuries)
- Ensemble de modelos (Moneyline + Spread)
- Calibração por tipo de jogo (primetime vs regular)
- Incorporar line movement como feature

**Fase 3 (Especializado):**
- Modelo específico para playoffs
- Integração de prop bets
- Live betting features
- Player-level modeling para props

### 5.3 Desafios Específicos da NFL

- **Baixa frequência**: Menos dados = overfitting risk
- **Alta variância**: Requer bankroll management mais conservador
- **Seasonality**: Desempenho muda drasticamente ao longo da temporada
- **Injury impact**: Difícil quantificar impacto de lesões
- **Weather noise**: Difícil prever impacto exato do tempo

---

## 6. VALIDAÇÃO E BACKTESTING

### 6.1 Período de Backtest

- **Training**: 2014-2020 (7 temporadas)
- **Validation**: 2021-2022 (2 temporadas)
- **Test**: 2023-2024 (2 temporadas)

### 6.2 Métricas de Sucesso

- **Edge mínimo**: 2-3% em closing line value
- **ROI alvo**: 3-5% em moneyline, 4-6% em spread
- **Sharpe ratio**: > 1.5
- **Max drawdown**: < 20%
- **Number of bets**: 300-500 por temporada (volume suficiente)

### 6.3 Testes de Robustez

- Sensibilidade a diferentes thresholds de edge
- Performance por mês da temporada
- Performance por dia da semana
- Performance em diferentes condições climáticas
- Performance em jogos primetime vs regular

---

## 7. IMPLEMENTAÇÃO

### 7.1 Fase 1: MVP NFL (3-4 meses)

- Coleta de dados históricos
- Pipeline ETL específico para NFL
- Modelo baseline XGBoost
- Backtest em dados históricos
- Documentação de resultados

### 7.2 Fase 2: Produção (2-3 meses)

- Integração com sistema existente
- Data feed em tempo real
- Execução manual inicial
- Monitorização de performance
- Ajustes baseados em resultados reais

### 7.3 Fase 3: Otimização (contínuo)

- Adicionar features avançadas
- Ensemble modeling
- Calibração dinâmica
- Expansão para props
- Live betting capabilities

---

## 8. RISCOS E MITIGAÇÃO

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Edge inexistente | Média | Alto | Backtest rigoroso antes de produção |
| Overfitting devido a baixo volume | Alta | Alto | Regularização agressiva, cross-validation |
| Dados insuficientes | Média | Médio | Múltiplas fontes de dados, feature engineering |
| Mudanças de regras | Baixa | Médio | Monitorização contínua, retraining |
| Liquidez insuficiente | Baixa | Médio | Focar em jogos principais, limitar stakes |

---

## 9. DEPENDÊNCIAS

- **Dados**: Acesso a dados históricos e em tempo real de NFL
- **Modelo**: Framework de ML já estabelecido em NBA
- **Infraestrutura**: Capacidade de processar dados adicionais
- **Capital**: Bankroll separado para testes (recomendado: $5K-$10K)
- **Validação**: 6+ meses de backtest antes de produção

---

## 10. CRITÉRIOS DE SUCESSO

- [ ] Edge validado em backtest (≥ 2% CLV)
- [ ] ROI positivo em 3 temporadas consecutivas
- [ ] Sharpe ratio > 1.5
- [ ] Volume de apostas ≥ 300/season
- [ ] Sistema integrado em produção
- [ ] Monitorização ativa implementada
- [ ] Documentação completa

---

## 11. BACKLOG

- [ ] Coletar dados históricos NFL (2014-2024)
- [ ] Identificar e contratar provedor de dados em tempo real
- [ ] Desenvolver pipeline ETL específico NFL
- [ ] Feature engineering para NFL
- [ ] Treinar modelo baseline XGBoost
- [ ] Backtest em 5 temporadas históricas
- [ ] Analisar resultados por regime (favorito/underdog, home/away)
- [ ] Implementar calibração de probabilidades
- [ ] Integrar com sistema de value detection existente
- [ ] Testar manualmente em 1 temporada
- [ ] Automatizar execução
- [ ] Documentar aprendizados e best practices

---

## 12. LINKS CRUZADOS

- [[41_Future_Expansion/INDEX]] ← Secção mãe
- [[43_Multi_Sport_Expansion/INDEX]] → Expansão multi-desporto detalhada
- [[05_Machine_Learning/XGBoost_BASELINE]] → Modelo baseline aplicável
- [[06_Backtesting/INDEX]] → Framework de backtest
- [[04_Data_Engineering/INDEX]] → Pipeline de dados