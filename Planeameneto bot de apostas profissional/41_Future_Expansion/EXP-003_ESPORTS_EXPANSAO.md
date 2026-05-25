# EXP-003 — Esports (LoL, CS:GO)

**ID:** `EXP-003` | **Fase:** #phase/19-21 (VBQ-003) | **Owner:** Product Manager / Strategy Lead | **Status:** #status/pending

---

## 1. OBJETIVO

Expandir o sistema de value betting para incluir esports, focando inicialmente em League of Legends (LoL) e Counter-Strike: Global Offensive (CS:GO), capitalizando na natureza emergente destes mercados e na ineficiência decorrente da menor maturidade.

---

## 2. CONTEXTO

Os esports representam uma classe de ativos emergente com características únicas:

- **Mercado imaturo**: Menos eficiente que desportos tradicionais
- **Alta volatilidade**: Odds movem-se drasticamente com news
- **Rápida evolução**: Metagame muda constantemente
- **Jovem demografia**: Apostadores menos sofisticados em média
- **Dados granulares**: Estatísticas detalhadas disponíveis
- **Crescimento exponencial**: Volume aumentando consistentemente
- **Global**: Torneios 24/7 em diferentes regiões

Os esports são atrativos para value betting porque:
- Mercados menos eficientes (menos sharp money)
- Overreaction a resultados recentes
- Conhecimento de domínio é barreira de entrada
- Dados não são amplamente utilizados ainda
- Edge potencial muito alto mas volátil

---

## 3. ANÁLISE DE MERCADO

### 3.1 Principais Títulos

**League of Legends (LoL):**
- **World Championship**: Torneio anual principal
- **MSI (Mid-Season Invitational)**: Torneio inter-regional
- **Regional Leagues**: LCK (Coreia), LPL (China), LCS (América), LEC (Europa)
- **Temporada**: Contínua, splits primavera/verão/outono
- **Formato**: Best-of-1, Best-of-3, Best-of-5

**Counter-Strike (CS:GO / CS2):**
- **Majors**: 2-3 torneios principais por ano
- **Tier 1 Tournaments**: IEM, ESL Pro League, BLAST
- **Tier 2/3 Tournaments**: Circuitos regionais
- **Temporada**: Quase contínua
- **Formato**: Best-of-1, Best-of-3 (MR12 ou MR15)

**Outros títulos (futuro):**
- Dota 2
- Valorant
- Overwatch
- FIFA/eFootball

### 3.2 Volume e Liquidez

| Título | Categoria | Jogos/Ano | Volume Médio | Liquidez | Edge Potencial |
|--------|-----------|-----------|--------------|----------|----------------|
| LoL | World Championship | ~100 | $50K-$200K | Alta | Médio |
| LoL | Regional Major | ~500 | $20K-$100K | Média-Alta | Alto |
| LoL | Regional Minor | ~1,000 | $5K-$30K | Média | Muito Alto |
| CS:GO | Majors | ~150 | $30K-$150K | Alta | Médio |
| CS:GO | Tier 1 Tournaments | ~600 | $10K-$50K | Média-Alta | Alto |
| CS:GO | Tier 2/3 | ~1,500 | $2K-$15K | Baixa-Média | Muito Alto |

### 3.3 Mercados Disponíveis

- **Moneyline**: Vencedor do match
- **Map Handicap**: Spread em número de maps
- **Map Totals**: Over/Under total de maps
- **Correct Map Score**: Resultado exato em maps
- **First Blood/First Tower**: Prop bets específicas
- **Live/In-Play**: Odds em tempo real durante o match

---

## 4. REQUISITOS DE DADOS

### 4.1 Dados Necessários

**Dados de Equipa:**
- Ranking regional e mundial
- Histórico head-to-head (H2H)
- Form recente (últimos 10-20 jogos)
- Win-loss record por split/season
- Performance por mapa (CS) ou champion (LoL)
- Draft statistics (LoL): Picks/bans, win rates
- Economy statistics (CS): Buy rounds, force buys
- Roster changes: Transferências, substituições
- Coach e staff changes

**Dados de Jogador:**
- Estatísticas individuais (KDA, ACS, etc.)
- Form recente
- Role-specific performance
- Agent/Champion pool (LoL/Valorant)
- Mechanical skill metrics

**Dados de Torneio:**
- Categoria (Major, Tier 1, Tier 2)
- Formato (BO1, BO3, BO5)
- Premiação e importância
- Localização (online vs LAN)
- Patch version (especialmente crítico em LoL)

**Dados de Contexto:**
- Patch version e metagame
- Dias desde último jogo
- Travel (para torneios LAN)
- Fatigue indicators
- Motivation (qualificação para playoffs, etc.)

**Dados em Tempo Real:**
- Score atual do match
- Estatísticas do match em curso
- Draft atual (LoL)
- Economy atual (CS)
- Momentum indicators

### 4.2 Fontes de Dados Potenciais

- **Riot Games API**: Dados oficiais LoL
- **Valve API**: Dados oficiais CS:GO/CS2
- **HLTV**: Estatísticas detalhadas CS
- **Oracle's Elixir**: Estatísticas avançadas LoL
- **GamerLegion**: Dados de múltiplos títulos
- **Pandascore**: Feed de dados esports
- **Betfair Streaming**: Odds em tempo real
- **Strafe**: Dados e analytics esports

### 4.3 Volume de Dados

- **Histórico**: 3-5 anos (2020-2024) - esports evoluem rápido
- **Freqüência**: Diário, torneios 24/7
- **Granularidade**: Match-level + game/map-level
- **Armazenamento**: ~80GB para dados históricos completos

---

## 5. ABORDAGEM DE MODELAGEM

### 5.1 Features Principais

**Features de Equipa (LoL):**
- Ranking difference
- Recent form (win% últimos 30 dias)
- Head-to-head record
- Draft win rate (por champion combination)
- Objective control (dragons, barons, towers)
- Gold difference at 15 min
- First blood rate
- Roster stability (dias desde última mudança)

**Features de Equipa (CS):**
- Ranking difference
- Recent form (win% últimos 30 dias)
- Map win rates (por mapa individual)
- Pistol round win rate
- Economy efficiency (rounds won per buy)
- CT vs T side performance
- Roster stability
- LAN vs online performance delta

**Features de Contexto:**
- Patch version (crítico - metagame shifts)
- Tournament importance
- Online vs LAN
- Rest days desde último jogo
- Time zone (jet lag)
- Motivation (playoff implications)

**Features de Mercado:**
- Opening odds vs current odds
- Odds movement direction
- Public vs sharp money indicators
- Volume de apostas

### 5.2 Estratégia de Modelagem

**Fase 1 (Baseline - LoL LCK/LPL):**
- Modelo XGBoost para Moneyline
- Features simples (ranking, form, H2H)
- Focar em ligas principais com liquidez adequada
- Backtest em 2-3 temporadas
- Modelos específicos por patch version

**Fase 2 (Avançado):**
- Adicionar features granulares (draft, economy)
- Modelos separados por formato (BO1 vs BO3 vs BO5)
- Calibração por região (Coreia, China, Europa, América)
- Incorporar patch version como feature crítica
- Expansão para CS:GO

**Fase 3 (Tier 2/3):**
- Modelos especializados para torneios menores
- Edge hunting em mercados menos eficientes
- Higher stakes em lower liquidity
- Risk management específico
- Live betting capabilities

### 5.3 Desafios Específicos de Esports

- **Patch volatility**: Metagame muda drasticamente a cada 2 semanas
- **Roster instability**: Jogadores mudam de equipa frequentemente
- **Online vs LAN**: Performance pode variar drasticamente
- **Data quality**: Menos padronizado que desportos tradicionais
- **Rapid obsolescence**: Modelos envelhecem muito rápido
- **Low liquidity em tier 2/3**: Difícil executar stakes grandes
- **Knowledge barrier**: Requer entendimento profundo do jogo

---

## 6. VALIDAÇÃO E BACKTESTING

### 6.1 Período de Backtest

- **Training**: 2021-2022 (2 temporadas)
- **Validation**: 2023 (1 temporada)
- **Test**: 2024 (1 temporada)

*Nota: Dados mais antigos são menos relevantes devido à rápida evolução dos esports*

### 6.2 Estratificação

Backtest separado para:
- Por título (LoL vs CS:GO)
- Por região (LCK, LPL, LCS, LEC para LoL)
- Por categoria (Major vs Tier 1 vs Tier 2)
- Por patch version (crítico)
- Por formato (BO1 vs BO3 vs BO5)

### 6.3 Métricas de Sucesso

- **Edge mínimo**: 3-5% em closing line value (mais alto devido à volatilidade)
- **ROI alvo**: 6-10% em tier 1, 10-15% em tier 2/3
- **Sharpe ratio**: > 1.2 (aceitando maior volatilidade)
- **Max drawdown**: < 30%
- **Number of bets**: 1,500-2,000 por ano (volume muito alto)
- **Model decay**: Retraining a cada 2-4 semanas

### 6.4 Testes de Robustez

- Performance por patch version
- Performance por região
- Performance por formato (BO1 vs BO3 vs BO5)
- Performance online vs LAN
- Sensibilidade a thresholds de edge
- Model decay analysis (quanto tempo até modelo ficar obsoleto)

---

## 7. IMPLEMENTAÇÃO

### 7.1 Fase 1: MVP Esports (4-5 meses)

- Coleta de dados históricos LoL (LCK, LPL principais)
- Pipeline ETL específico para esports
- Modelo baseline XGBoost (Moneyline)
- Backtest em 2-3 temporadas
- Análise de patch version impact
- Documentação de resultados

### 7.2 Fase 2: Produção (2-3 meses)

- Integração com sistema existente
- Data feed em tempo real
- Execução manual em torneios selecionados
- Monitorização por patch version
- Retraining quinzenal
- Ajustes baseados em resultados reais

### 7.3 Fase 3: Expansão (contínuo)

- Adicionar features granulares (draft, economy)
- Expansão para CS:GO
- Modelos por formato (BO1/BO3/BO5)
- Entry em torneios tier 2 (edge hunting)
- Live betting capabilities

### 7.4 Fase 4: Otimização (futuro)

- Patch-aware modeling (features específicas por patch)
- Ensemble de modelos por região
- Calibração dinâmica por patch
- Machine learning para detecção de metagame shifts
- Expansão para outros títulos (Valorant, Dota 2)

---

## 8. RISCOS E MITIGAÇÃO

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Patch volatility | Muito Alta | Muito Alto | Retraining frequente (2-4 semanas), features de patch |
| Roster instability | Alta | Alto | Features de roster stability, monitoring contínuo |
| Model obsolescence | Muito Alta | Alto | Retraining automatizado, model decay monitoring |
| Liquidez insuficiente | Alta | Alto | Limitar stakes, focar em tier 1 inicialmente |
| Dados inconsistentes | Média | Médio | Múltiplas fontes, validação cruzada |
| Conhecimento de domínio | Média | Alto | Consultoria com expertos, learning contínuo |
| Edge inexistente | Média | Alto | Backtest rigoroso, piloto em produção |

---

## 9. DEPENDÊNCIAS

- **Dados**: Acesso a dados históricos e em tempo real de esports
- **Modelo**: Framework de ML já estabelecido
- **Infraestrutura**: Capacidade de retraining frequente
- **Capital**: Bankroll separado para testes (recomendado: $2K-$4K)
- **Validação**: 3-4 meses de backtest antes de produção
- **Conhecimento de domínio**: Understanding profundo de LoL/CS
- **Retraining pipeline**: Automatização de retraining frequente

---

## 10. CRITÉRIOS DE SUCESSO

- [ ] Edge validado em backtest (≥ 3% CLV)
- [ ] ROI positivo em backtest de 2 temporadas
- [ ] Sharpe ratio > 1.2
- [ ] Volume de apostas ≥ 1,000/ano
- [ ] Performance consistente por patch version
- [ ] Sistema de retraining automatizado
- [ ] Sistema integrado em produção
- [ ] Monitorização contínua de model decay
- [ ] Documentação completa

---

## 11. BACKLOG

- [ ] Coletar dados históricos LoL (2021-2024)
- [ ] Identificar e contratar provedor de dados esports
- [ ] Desenvolver pipeline ETL específico para esports
- [ ] Feature engineering para LoL (ranking, form, draft)
- [ ] Analisar impacto de patch version em odds
- [ ] Treinar modelo baseline XGBoost (Moneyline)
- [ ] Backtest estratificado por patch version
- [ ] Backtest estratificado por região
- [ ] Implementar sistema de retraining automatizado
- [ ] Calibrar probabilidades por patch
- [ ] Integrar com sistema de value detection existente
- [ ] Testar manualmente em torneios tier 1 por 2 meses
- [ ] Expandir para CS:GO
- [ ] Avaliar entrada em torneios tier 2
- [ ] Documentar aprendizados e best practices
- [ ] Criar guia de conhecimento de domínio LoL/CS

---

## 12. LINKS CRUZADOS

- [[41_Future_Expansion/INDEX]] ← Secção mãe
- [[43_Multi_Sport_Expansion/INDEX]] → Expansão multi-desporto detalhada
- [[05_Machine_Learning/XGBoost_BASELINE]] → Modelo baseline aplicável
- [[06_Backtesting/INDEX]] → Framework de backtest
- [[04_Data_Engineering/INDEX]] → Pipeline de dados
- [[11_MLOps/RETRAINING_AUTO]] → Retraining frequente crítico para esports
- [[EXP-005_LIVE_BETTING]] → Live betting em esports