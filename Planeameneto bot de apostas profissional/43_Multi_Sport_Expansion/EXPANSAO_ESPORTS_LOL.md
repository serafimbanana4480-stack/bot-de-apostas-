# EXPANSAO_ESPORTS_LOL — League of Legends

**ID:** `MSE-003` | **Fase:** #phase/19-21 (VBQ-003) | **Owner:** Product Manager | **Status:** #status/pending

---

## 1. OBJETIVO

Expandir o sistema de value betting para esports, especificamente League of Legends (LoL), aproveitando a natureza emergente deste mercado e a menor eficiência comparativa aos desportos tradicionais.

---

## 2. PORQUÊ ESPORTS (LOL)

Os esports representam uma fronteira de value betting com potencial de edge significativo devido à imaturidade do mercado e à complexidade do jogo.

**Vantagens Estratégicas:**

- **Mercado Ineficiente:** Menos sharp money, mais recreational bettors
- **Alta Volatilidade:** Meta changes, patches alteram dinamicamente o jogo
- **Dados Disponíveis:** APIs detalhadas de jogos, estatísticas granulares
- **Crescimento de Liquidez:** Liquidez aumentando rapidamente em principais torneios
- **Edge Potencial Alto:** Modelos quantitativos podem ter vantagem significativa vs bettors informais

**Desafios Específicos:**

- **Patch Cycles:** Mudanças frequentes de jogo invalidam modelos rapidamente
- **Roster Changes:** Transferências de jogadores são comuns e não previsíveis
- **Meta Shifts:** Estratégias dominantes mudam a cada patch
- **Regional Disparities:** Diferentes regiões têm níveis de competitividade muito diferentes
- **Menos Dados Históricos:** Esporte relativamente novo vs desportos tradicionais

---

## 3. DIFERENÇAS VS DESPORTOS TRADICIONAIS

| Aspecto | NBA/NFL | LoL Esports |
|---------|---------|-------------|
| Histórico de Dados | Décadas | ~8-10 anos |
| Frequência de Mudanças | Baixa (regras estáveis) | Alta (patches a cada 2 semanas) |
| Unidade de Análise | Equipa/Jogador | Equipa (5 jogadores) |
| Variáveis Chave | Stats físicas/técnicas | Champion picks, draft, macro |
| Efeito Roster | Médio | Extremo (sinergia crítica) |
| Volatilidade Odds | Média | Muito alta |
| Liquidez | Alta | Média (crescendo) |
| Sample Size | Grande | Pequeno (menos jogos/época) |
| Regional Consistency | Alta | Baixa (LCK vs LCS diferenças enormes) |

---

## 4. MERCADOS ALVO INICIAIS

### 4.1 Match Winner (1X2)
- **Liquidez:** Média em Worlds/MSI, baixa em regular season
- **Edge Estimado:** Muito alto (8-12% potencial)
- **Complexidade:** Alta
- **Prioridade:** 1

### 4.2 Map Winner (First Blood/First Tower)
- **Liquidez:** Baixa
- **Edge Estimado:** Alto (6-10% potencial)
- **Complexidade:** Muito alta
- **Prioridade:** 3

### 4.3 Total Maps (Over/Under)
- **Liquidez:** Média-baixa
- **Edge Estimado:** Alto (7-9% potencial)
- **Complexidade:** Alta
- **Prioridade:** 2

---

## 5. REQUISITOS DE DADOS

### 5.1 Fontes de Dados
- **Oracle's Elixir:** Estatísticas detalhadas de LoL (gratuito para research)
- **Riot Games API:** Dados oficiais de partidas
- **Gamer.gg/LoLalytics:** Champion statistics e win rates
- **PandaScore/Abios:** Odds históricas e live data
- **Leaguepedia:** Histórico de torneios e resultados

### 5.2 Features Críticas
- **Team Performance:** Win rate, KDA, gold difference, objective control
- **Champion Statistics:** Pick/ban rates, win rates por patch
- **Draft Analysis:** Team composition strength, synergy scores
- **Player Stats:** Individual KDA, champion pool, performance on key champions
- **Recent Form:** Últimos 10-20 jogos, weighted por recência
- **Regional Strength:** Historical performance inter-regional
- **Patch Impact:** Performance before/after recent patches
- **Schedule Fatigue:** Back-to-back games, travel impact
- **Roster Stability:** Time since last roster change

### 5.3 Pipeline de Dados
- Ingestão diária de resultados e odds
- Mapeamento de patches a versões de jogo
- Normalização de nomes de equipas/jogadores
- Feature engineering específica por patch
- Detecção de meta shifts (champion popularity changes)
- Tracking de roster changes

---

## 6. ARQUITETURA DO MODELO

### 6.1 Abordagem Inicial
- **Modelo Base:** XGBoost ou LightGBM
- **Target:** Probabilidade de vitória da equipa
- **Features:** 80-120 features iniciais
- **Validation:** Walk-forward CV com purged periods

### 6.2 Considerações Especiais
- **Patch-Aware Models:** Modelos treinados em janelas temporais por patch
- **Regional Segregation:** Modelos separados por região (LCK, LCS, LEC, LPL)
- **Champion Embedding:** Representação vetorial de champion picks
- **Roster Change Detection:** Reset ou reweight após mudanças significativas
- **Meta Adaptation:** Features que capturam shifts de meta

### 6.3 Adaptabilidade
- **Retraining Frequency:** Semanal ou quinzenal (vs mensal em desportos tradicionais)
- **Concept Drift Detection:** Monitorização contínua de performance por patch
- **Rolling Window:** Janelas mais curtas (3-6 meses) vs desportos tradicionais

---

## 7. CRITÉRIOS DE VALIDAÇÃO

### 7.1 Métricas Mínimas
- **CLV (Closed Line Value):** > 3% (mais alto devido à ineficiência)
- **Brier Score:** < mercado de referência
- **ROI Backtest:** > 8% (comissões incluídas)
- **Sharpe Ratio:** > 1.2 (mais volátil aceitável)
- **Max Drawdown:** < 20% (maior tolerância devido à volatilidade)

### 7.2 Backtest Requirements
- Mínimo 2 temporadas completas (2023-2024)
- Purged CV com look-forward periods adequados
- Slippage modelado (3-4% para esports)
- Comissões incluídas (5% padrão)
- Stress test por patch e por região
- Análise de performance após meta shifts

### 7.3 Paper Trading
- 1 mês de paper trading antes de dinheiro real
- Foco em torneios de média-alta liquidez (Worlds, MSI, playoffs regionais)
- Tracking de divergências backtest vs real
- Monitorização de impacto de patches recentes

---

## 8. RISCOS ESPECÍFICOS

### 8.1 Riscos de Dados
- **Patch Changes:** Modelos obsoletos rapidamente após novo patch
- **Data Inconsistencies:** Diferentes fontes com dados inconsistentes
- **Regional Bias:** Dados de uma região não generalizam para outra
- **Champion Name Changes:** Riot renomeia champions periodicamente

### 8.2 Riscos de Modelo
- **Overfitting a Patch:** Modelo de patch X não funciona em patch Y
- **Meta Shifts:** Mudanças drásticas de estratégia invalidam features
- **Roster Instability:** Transferências não previsíveis afetam performance
- **Small Sample Size:** Menos jogos/época vs desportos tradicionais

### 8.3 Riscos de Execução
- **Muito Baixa Liquidez:** Torneios menores podem ter limites muito baixos
- **Rapid Odds Movement:** Rumores de patches/rosters movem odds instantaneamente
- **Schedule Uncertainty:** Atrasos e adiamentos comuns em esports
- **Market Immaturity:** Menos casas de aposta aceitam esports

---

## 9. ROADMAP DE IMPLEMENTAÇÃO

### Fase 1: Research (Semanas 1-6)
- [ ] Explorar fontes de dados disponíveis (Oracle's Elixir, Riot API)
- [ ] Analisar qualidade e completeness de dados históricos
- [ ] Estudar patch cycles e seu impacto em performance
- [ ] Definir feature set inicial
- [ ] Analisar regional differences

### Fase 2: Data Pipeline (Semanas 7-12)
- [ ] Implementar ingestão de dados Oracle's Elixir
- [ ] Criar mapeamento de patches e versões
- [ ] Build feature engineering pipeline
- [ ] Implementar tracking de roster changes
- [ ] Validar qualidade de dados

### Fase 3: Model Development (Semanas 13-18)
- [ ] Treinar baseline XGBoost model
- [ ] Implementar walk-forward CV patch-aware
- [ ] Tuning de hyperparameters com Optuna
- [ ] Calibração de probabilidades
- [ ] Implementar regional segmentation

### Fase 4: Backtesting (Semanas 19-24)
- [ ] Executar backtest 2 temporadas
- [ ] Analisar CLV, ROI, drawdown
- [ ] Stress test por patch e região
- [ ] Analisar performance após meta shifts
- [ ] Comparar vs mercado de referência

### Fase 5: Validation (Semanas 25-30)
- [ ] Paper trading 1 mês
- [ ] Monitorizar impacto de patches em tempo real
- [ ] Ajustar modelo baseado em resultados reais
- [ ] Documentar divergências backtest vs real
- [ ] Preparar para produção se critérios cumpridos

---

## 10. CONSIDERAÇÕES ADICIONAIS

### 10.1 Priorização vs Outros Esportes
- **Complexidade:** Alta (requer conhecimento de jogo)
- **ROI Potencial:** Muito alto
- **Liquidez:** Média (mas crescendo)
- **Risco:** Alto (volatilidade de patches)
- **Fase Recomendada:** 13 (após validação NBA + 1 esporte tradicional)

### 10.2 Synergies com Outros Esportes
- **Feature Engineering:** Técnicas de time series aplicáveis
- **Model Architecture:** XGBoost baseline reutilizável
- **Validation Framework:** Walk-forward CV adaptável
- **Risk Management:** Kelly e circuit breakers transferíveis

### 10.3 Future Expansion
- **Outros Esports:** Dota 2, CS:GO, Valorant (similar architecture)
- **Live Betting:** In-play betting em esports (alta volatilidade = alto edge)
- **Prop Bets:** First blood, first tower, total kills (mercados específicos)

---

## 11. LINKS CRUZADOS

- [[43_Multi_Sport_Expansion/INDEX]] ← Secção mãe
- [[43_Multi_Sport_Expansion/ARQUITETURA_MULTI_ESPORTE]] → Arquitetura compartilhada
- [[43_Multi_Sport_Expansion/APIs_ESPORTOS]] → APIs para esports
- [[43_Multi_Sport_Expansion/EXPANSAO_NFL]] → Comparação com NFL expansion
- [[43_Multi_Sport_Expansion/EXPANSAO_TENNIS_ATP]] → Comparação com tennis expansion
- [[01_Vision_And_Strategy/FILOSOFIA_MVP]] → Regra: um desporto de cada vez
- [[05_Machine_Learning/WALK_FORWARD_CV]] → Metodologia de validação
- [[11_MLOps/FEATURE_DRIFT]] → Crítico para patches de LoL

---

**Data de Criação:** 2026-05-13
**Revisão Obrigatória:** Após conclusão de Fase 1 (Research)
**Owner:** Product Manager