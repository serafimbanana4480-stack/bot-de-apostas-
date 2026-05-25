# EXP-002 — Tennis ATP/WTA

**ID:** `EXP-002` | **Fase:** #phase/16-18 (VBQ-003) | **Owner:** Product Manager / Strategy Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Expandir o sistema de value betting para incluir ténis profissional (ATP e WTA), capitalizando na alta frequência de jogos e na natureza individual do desporto que pode criar ineficiências de mercado.

---

## 2. CONTEXTO

O ténis apresenta características únicas que o diferenciam de desportos de equipa:

- **Alta frequência**: ~11 meses de temporada, torneios semanais
- **Individual**: Psicologia e forma física são críticos
- **Superfícies variadas**: Hard, clay, grass - jogadores têm preferências
- **Best-of-3 vs Best-of-5**: Formatos diferentes em torneios
- **Fatigue management**: Jogadores participam em múltiplos torneios
- **No draws**: Sempre há vencedor (exceto retiradas)
- **In-play opportunities**: Mercado massivo para live betting

O ténis é atrativo para value betting porque:
- Mercados menos eficientes em torneios menores (Challenger, ITF)
- Overreaction a resultados recentes
- Psicologia individual cria padrões previsíveis
- Dados granulares disponíveis (ponto a ponto)
- Liquidez decente em torneios principais

---

## 3. ANÁLISE DE MERCADO

### 3.1 Estrutura do Ténis Profissional

**ATP (Masculino):**
- **ATP 1000**: 9 torneios/ano (Masters)
- **ATP 500**: 13 torneios/ano
- **ATP 250**: ~40 torneios/ano
- **Grand Slams**: 4 torneios/ano (best-of-5)
- **Challenger**: ~150 torneios/ano
- **Futures**: ~600 torneios/ano

**WTA (Feminino):**
- **WTA 1000**: 9 torneios/ano
- **WTA 500**: 12 torneios/ano
- **WTA 250**: ~30 torneios/ano
- **Grand Slams**: 4 torneios/ano
- **ITF**: Circuitos de desenvolvimento

### 3.2 Volume e Liquidez

| Categoria | Jogos/Ano | Volume Médio | Liquidez | Edge Potencial |
|-----------|-----------|--------------|----------|----------------|
| Grand Slams | ~500 | $100K-$500K | Muito Alta | Médio |
| ATP/WTA 1000 | ~1,200 | $50K-$200K | Alta | Médio-Alto |
| ATP/WTA 500 | ~800 | $20K-$100K | Média-Alta | Alto |
| ATP/WTA 250 | ~2,000 | $5K-$50K | Média | Alto |
| Challenger | ~3,000 | $1K-$10K | Baixa-Média | Muito Alto |
| ITF Futures | ~5,000 | <$1K | Baixa | Muito Alto |

### 3.3 Mercados Disponíveis

- **Moneyline**: Vencedor do match
- **Handicap Games**: Spread em número de games
- **Totals Games**: Over/Under total de games
- **Set Betting**: Resultado exato em sets
- **Correct Score**: Scoreline exato
- **In-Play**: Odds em tempo real durante o match

---

## 4. REQUISITOS DE DADOS

### 4.1 Dados Necessários

**Dados de Jogador:**
- Ranking ATP/WTA (live e histórico)
- Histórico head-to-head (H2H)
- Performance por superfície (hard/clay/grass)
- Win-loss record recente (últimos 30 dias)
- Estatísticas de serviço: Aces, double faults, first serve %
- Estatísticas de return: Break points converted, return points won
- Tempo de jogo médio
- Lesões e retiradas recentes
- Idade e forma física

**Dados de Torneio:**
- Categoria (Grand Slam, 1000, 500, 250, Challenger)
- Superfície (hard indoor/outdoor, clay, grass)
- Localização e altitude
- Premiação e importância
- Histórico do torneio

**Dados de Match:**
- Resultado anterior no torneio
- Dias de descanso desde último jogo
- Horário do jogo (manhã/tarde/noite)
- Condições climáticas (para torneios outdoor)
- Fator casa (se aplicável)

**Dados em Tempo Real:**
- Score atual
- Estatísticas do match em curso
- Momentum indicators
- Injury indicators durante o jogo

### 4.2 Fontes de Dados Potenciais

- **ATP/WTA APIs**: Dados oficiais
- **Tennis Abstract**: Estatísticas avançadas
- **Tennis Explorer**: Histórico detalhado
- **Sportradar**: Feed premium de dados
- **Betfair Streaming**: Odds em tempo real
- **Inplay Tennis**: Dados de live betting

### 4.3 Volume de Dados

- **Histórico**: 5-10 anos (2014-2024)
- **Freqüência**: Diário durante temporada
- **Granularidade**: Match-level + point-level (para live)
- **Armazenamento**: ~100GB para dados históricos completos

---

## 5. ABORDAGEM DE MODELAGEM

### 5.1 Features Principais

**Features de Jogador:**
- Ranking difference (delta entre jogadores)
- Recent form (win% últimos 30/60/90 dias)
- Surface performance (win% em cada superfície)
- Service hold % (últimos 20 jogos)
- Break point conversion % (últimos 20 jogos)
- Fatigue indicator (jogos jogados últimos 30 dias)
- Age factor (jovens vs veteranos)
- H2H record (histórico direto)
- Injury history (retiradas últimos 6 meses)

**Features de Contexto:**
- Surface type (hard/clay/grass)
- Tournament importance (pontos em jogo)
- Round (1st round vs final)
- Rest days desde último jogo
- Travel distance entre torneios
- Time of day
- Weather conditions (outdoor)

**Features de Mercado:**
- Opening odds vs current odds
- Odds movement direction
- Public vs sharp money indicators
- Historical line movement patterns
- Volume de apostas

### 5.2 Estratégia de Modelagem

**Fase 1 (Baseline - ATP/WTA 250+):**
- Modelo XGBoost para Moneyline
- Features simples (ranking, form, surface)
- Focar em torneios com liquidez adequada
- Backtest em 3 temporadas

**Fase 2 (Avançado):**
- Adicionar features granulares (service/return stats)
- Modelos separados por superfície
- Calibração por categoria de torneio
- Incorporar live betting features
- Expansão para handicaps e totals

**Fase 3 (Challenger/ITF):**
- Modelos especializados para torneios menores
- Edge hunting em mercados menos eficientes
- Higher stakes em lower liquidity
- Risk management específico

### 5.3 Desafios Específicos do Ténis

- **Retiradas**: Jogadores desistem frequentemente
- **Fatigue**: Schedule extremamente denso
- **Superfície variance**: Jogadores specialists em certas superfícies
- **Mental game**: Psicologia impacta performance
- **Low liquidity em torneios menores**: Difícil executar stakes grandes
- **Data quality**: Menos padronizado que NBA/NFL

---

## 6. VALIDAÇÃO E BACKTESTING

### 6.1 Período de Backtest

- **Training**: 2016-2020 (5 temporadas)
- **Validation**: 2021-2022 (2 temporadas)
- **Test**: 2023-2024 (2 temporadas)

### 6.2 Estratificação por Categoria

Backtest separado para:
- Grand Slams (liquidez máxima, edge mínimo)
- ATP/WTA 1000 & 500 (liquidez alta, edge médio)
- ATP/WTA 250 (liquidez média, edge alto)
- Challenger (liquidez baixa, edge muito alto)

### 6.3 Métricas de Sucesso

- **Edge mínimo**: 2-4% em closing line value
- **ROI alvo**: 4-7% em torneios 250+, 8-12% em Challenger
- **Sharpe ratio**: > 1.5
- **Max drawdown**: < 25%
- **Number of bets**: 1,000-1,500 por ano (volume alto)
- **Hit rate**: 52-55% (suficiente para edge)

### 6.4 Testes de Robustez

- Performance por superfície
- Performance por categoria de torneio
- Performance por round (early vs late rounds)
- Performance em diferentes momentos da temporada
- Sensibilidade a thresholds de edge

---

## 7. IMPLEMENTAÇÃO

### 7.1 Fase 1: MVP Ténis (3-4 meses)

- Coleta de dados históricos ATP/WTA
- Pipeline ETL específico para ténis
- Modelo baseline XGBoost (Moneyline)
- Backtest em torneios principais (250+)
- Documentação de resultados

### 7.2 Fase 2: Produção (2-3 meses)

- Integração com sistema existente
- Data feed em tempo real
- Execução manual em torneios selecionados
- Monitorização por categoria de torneio
- Ajustes baseados em resultados reais

### 7.3 Fase 3: Expansão (contínuo)

- Adicionar features avançadas (service/return stats)
- Modelos por superfície
- Expansão para handicaps e totals
- Entry em torneios Challenger (edge hunting)
- Live betting capabilities

### 7.4 Fase 4: Otimização (futuro)

- Point-level modeling para live betting
- Ensemble de modelos
- Calibração dinâmica por jogador
- Machine learning para detecção de padrões de momentum

---

## 8. RISCOS E MITIGAÇÃO

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Retiradas frequentes | Alta | Médio | Regras para handling de retiradas, insurance bets |
| Overfitting em superfícies | Média | Alto | Modelos separados por superfície, cross-validation |
| Liquidez insuficiente em Challenger | Alta | Alto | Limitar stakes, focar em torneios principais inicialmente |
| Dados inconsistentes | Média | Médio | Múltiplas fontes, validação cruzada |
| Fadiga não capturada | Média | Médio | Features de fatigue avançadas, monitorização |
| Edge inexistente em top tier | Média | Alto | Backtest rigoroso, focar em categorias com edge comprovado |

---

## 9. DEPENDÊNCIAS

- **Dados**: Acesso a dados históricos e em tempo real ATP/WTA
- **Modelo**: Framework de ML já estabelecido
- **Infraestrutura**: Capacidade de processar dados granulares
- **Capital**: Bankroll separado para testes (recomendado: $3K-$5K)
- **Validação**: 6+ meses de backtest antes de produção
- **Conhecimento de domínio**: Understanding de ténis profissional

---

## 10. CRITÉRIOS DE SUCESSO

- [ ] Edge validado em backtest (≥ 2% CLV)
- [ ] ROI positivo em 3 temporadas consecutivas
- [ ] Sharpe ratio > 1.5
- [ ] Volume de apostas ≥ 800/ano
- [ ] Performance consistente por superfície
- [ ] Sistema integrado em produção
- [ ] Monitorização por categoria de torneio
- [ ] Documentação completa

---

## 11. BACKLOG

- [ ] Coletar dados históricos ATP/WTA (2016-2024)
- [ ] Identificar e contratar provedor de dados em tempo real
- [ ] Desenvolver pipeline ETL específico para ténis
- [ ] Feature engineering para ténis (ranking, form, surface)
- [ ] Treinar modelo baseline XGBoost (Moneyline)
- [ ] Backtest estratificado por categoria de torneio
- [ ] Backtest estratificado por superfície
- [ ] Implementar regras para handling de retiradas
- [ ] Calibrar probabilidades por categoria
- [ ] Integrar com sistema de value detection existente
- [ ] Testar manualmente em torneios 250+ por 1 temporada
- [ ] Expandir para handicaps e totals
- [ ] Avaliar entrada em torneios Challenger
- [ ] Documentar aprendizados e best practices

---

## 12. LINKS CRUZADOS

- [[41_Future_Expansion/INDEX]] ← Secção mãe
- [[43_Multi_Sport_Expansion/INDEX]] → Expansão multi-desporto detalhada
- [[05_Machine_Learning/XGBoost_BASELINE]] → Modelo baseline aplicável
- [[06_Backtesting/INDEX]] → Framework de backtest
- [[04_Data_Engineering/INDEX]] → Pipeline de dados
- [[EXP-005_LIVE_BETTING]] → Live betting em ténis