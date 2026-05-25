# EXPANSAO_SOCCER_EPL — Premier League Inglesa

**ID:** `MSE-004` | **Fase:** #phase/22-24 (VBQ-003) | **Owner:** Product Manager | **Status:** #status/pending

---

## 1. OBJETIVO

Expandir o sistema de value betting para futebol, especificamente a Premier League Inglesa, o mercado de futebol mais liquido e eficiente do mundo.

---

## 2. PORQUÊ FUTEBOL (EPL)

O futebol é o desporto mais popular globalmente, com a maior liquidez e o maior número de mercados. No entanto, esta eficiência também torna mais difícil encontrar edge.

**Vantagens Estratégicas:**

- **Liquidez Máxima:** Maiores volumes de aposta do mundo
- **Mercados Diversos:** 1X2, Asian Handicap, Over/Under, Correct Score, Both Teams to Score
- **Dados Abundantes:** Séries temporais longas (décadas de dados)
- **Global Coverage:** Múltiplas ligas para expansão futura
- **Infraestrutura Madura:** APIs bem estabelecidas, dados de alta qualidade

**Desafios Específicos:**

- **Mercado Extremamente Eficiente:** Sharp money dominante, edge difícil de encontrar
- **Baixa Volatilidade:** Empates comuns, scores baixos aumentam variância
- **Complexidade Tática:** Estratégias complexas difíceis de modelar
- **Home Advantage Significativo:** Fator casa muito importante
- **Injury Information:** Lesões não reportadas ou sub-reportadas
- **Motivation Variables:** Jogadores "tank" em jogos sem importância

---

## 3. DIFERENÇAS VS OUTROS ESPORTES

| Aspecto | NBA | Tennis | LoL | Soccer EPL |
|---------|-----|--------|-----|------------|
| Jogos/época | 1230 | ~2000 | ~500 | 380 |
| Frequência | Diária | Quase diária | Semanal | Semanal |
| Unidade de Análise | Equipa | Jogador | Equipa | Equipa |
| Resultados Possíveis | 2 (ignorando empate) | 2 | 2 | 3 (1X2) |
| Volatilidade Odds | Média | Alta | Muito Alta | Baixa |
| Liquidez | Alta | Média | Média | Muito Alta |
| Mercado Eficiência | Média | Média-alta | Baixa | Muito Alta |
| Edge Estimado | 3-5% | 4-6% | 8-12% | 1-3% |
| Sample Size | Grande | Médio | Pequeno | Médio |
| Home Advantage | Médio | N/A | N/A | Muito Alto |

---

## 4. MERCADOS ALVO INICIAIS

### 4.1 1X2 (Match Winner)
- **Liquidez:** Muito alta
- **Edge Estimado:** Baixo (1-2% potencial)
- **Complexidade:** Alta
- **Prioridade:** 2

### 4.2 Asian Handicap
- **Liquidez:** Muito alta
- **Edge Estimado:** Médio-baixo (2-3% potencial)
- **Complexidade:** Muito alta
- **Prioridade:** 1

### 4.3 Over/Under 2.5 Goals
- **Liquidez:** Muito alta
- **Edge Estimado:** Médio (2-4% potencial)
- **Complexidade:** Alta
- **Prioridade:** 3

### 4.4 Both Teams to Score (BTTS)
- **Liquidez:** Alta
- **Edge Estimado:** Médio (3-5% potencial)
- **Complexidade:** Média
- **Prioridade:** 4

---

## 5. REQUISITOS DE DADOS

### 5.1 Fontes de Dados
- **Football-Data.co.uk:** Dados históricos gratuitos de alta qualidade
- **Understat:** Estatísticas avançadas (xG, xA, etc.)
- **FBref:** Estatísticas detalhadas de jogadores e equipas
- **Opta/Stats Perform:** Dados premium (requer subscrição)
- **Betfair API:** Odds históricas e live data
- **The Sports DB:** Metadados de competições

### 5.2 Features Críticas
- **Team Performance:** Points, goal difference, recent form (last 5-10 games)
- **Advanced Metrics:** Expected Goals (xG), Expected Assists (xA), xG difference
- **Home/Away Splits:** Performance separada casa/fora
- **Head-to-Head:** Histórico direto entre equipas
- **Player Availability:** Injuries, suspensions, rotation risk
- **Schedule Factors:** Days since last game, travel distance, Champions League fatigue
- **Season Context:** Relegation battle, title race, European qualification
- **Manager Tactics:** Tactical style (possession, counter-attack, pressing)
- **Market Value:** Squad value as proxy for quality

### 5.3 Pipeline de Dados
- Ingestão semanal de resultados e odds
- Normalização de nomes de equipas/jogadores
- Cálculo de rolling statistics (últimos 5, 10, 20 jogos)
- Feature engineering de advanced metrics
- Tracking de injuries e suspensions
- Agregação de dados por temporada

---

## 6. ARQUITETURA DO MODELO

### 6.1 Abordagem Inicial
- **Modelo Base:** XGBoost ou CatBoost (CatBoost bom para categorical features)
- **Target:** Probabilidade de resultado (1X2) ou linha de handicap/goals
- **Features:** 100-150 features iniciais
- **Validation:** Walk-forward CV com purged periods

### 6.2 Considerações Especiais
- **Home Advantage Modeling:** Feature explícita para home advantage
- **Draw Handling:** Modelos separados ou ternary classification
- **League Segregation:** Modelos específicos por liga (EPL, La Liga, etc.)
- **Seasonality:** Performance varia ao longo da temporada
- **Cup Competitions:** Diferente performance em copas vs liga

### 6.3 Advanced Features
- **Expected Goals (xG):** Métrica avançada de qualidade de chances
- **Possession-Based Metrics:** Territory control, pass completion
- **Set Piece Performance:** Corners, free kicks, penalties
- **Style Clustering:** Agrupamento de equipas por estilo tático

---

## 7. CRITÉRIOS DE VALIDAÇÃO

### 7.1 Métricas Mínimas
- **CLV (Closed Line Value):** > 1.5% (mais baixo devido à eficiência)
- **Brier Score:** < mercado de referência
- **ROI Backtest:** > 3% (comissões incluídas)
- **Sharpe Ratio:** > 2.0 (menos volátil requerido)
- **Max Drawdown:** < 10% (mais conservador)

### 7.2 Backtest Requirements
- Mínimo 5 temporadas completas (2019-2024)
- Purged CV com look-forward periods adequados
- Slippage modelado (1-2% para futebol de alta liquidez)
- Comissões incluídas (5% padrão)
- Stress test por temporada e por mercado
- Análise de performance em diferentes contextos (title race, relegation)

### 7.3 Paper Trading
- 2 meses de paper trading antes de dinheiro real
- Foco em mercados de alta liquidez
- Tracking de divergências backtest vs real
- Análise de impacto de injuries/suspensions não previstas

---

## 8. RISCOS ESPECÍFICOS

### 8.1 Riscos de Dados
- **Injury Uncertainty:** Lesões não reportadas ou gravidade desconhecida
- **Lineup Uncertainty:** Titulares confirmados apenas 1h antes do jogo
- **Data Quality:** Diferentes fontes com dados inconsistentes
- **Scoreline Outliers:** High-scoring games raros mas impactantes

### 8.2 Riscos de Modelo
- **Market Efficiency:** Edge muito pequeno, difícil de detectar
- **Low Scoring Nature:** Alta variância em poucos jogos
- **Draw Frequency:** Empates (25-30%) aumentam complexidade
- **Tactical Shifts:** Mudanças de manager/tática invalidam modelos
- **Motivation Factors:** Jogos sem importância têm performance imprevisível

### 8.3 Riscos de Execução
- **Tight Margins:** Pequeno edge requer execução perfeita
- **Rapid Odds Movement:** News de lineups movem odds instantaneamente
- **Market Limits:** Altos limites mas também alta competição
- **Commission Impact:** 5% de comissão impacta mais em edge pequeno

---

## 9. ROADMAP DE IMPLEMENTAÇÃO

### Fase 1: Research (Semanas 1-8)
- [ ] Explorar fontes de dados disponíveis (Football-Data, Understat, FBref)
- [ ] Analisar qualidade e completeness de dados históricos (5+ temporadas)
- [ ] Estudar literatura de soccer betting models
- [ ] Analisar eficiência de mercado em diferentes mercados (1X2 vs AH vs O/U)
- [ ] Definir feature set inicial

### Fase 2: Data Pipeline (Semanas 9-16)
- [ ] Implementar ingestão de dados Football-Data.co.uk
- [ ] Integrar dados avançados (Understat xG, FBref stats)
- [ ] Criar feature engineering pipeline
- [ ] Implementar tracking de injuries e suspensions
- [ ] Validar qualidade de dados

### Fase 3: Model Development (Semanas 17-24)
- [ ] Treinar baseline CatBoost model (bom para categoricals)
- [ ] Implementar walk-forward CV
- [ ] Tuning de hyperparameters com Optuna
- [ ] Calibração de probabilidades
- [ ] Experimentar com diferentes targets (1X2 vs AH vs O/U)

### Fase 4: Backtesting (Semanas 25-32)
- [ ] Executar backtest 5 temporadas
- [ ] Analisar CLV, ROI, drawdown
- [ ] Stress test por temporada e contexto
- [ ] Comparar performance por mercado
- [ ] Analisar sensibilidade a injuries/suspensions

### Fase 5: Validation (Semanas 33-40)
- [ ] Paper trading 2 meses
- [ ] Foco em mercados de maior liquidez
- [ ] Ajustar modelo baseado em resultados reais
- [ ] Documentar divergências backtest vs real
- [ ] Preparar para produção se critérios cumpridos

---

## 10. CONSIDERAÇÕES ADICIONAIS

### 10.1 Priorização vs Outros Esportes
- **Complexidade:** Muito alta (mercado eficiente)
- **ROI Potencial:** Baixo (1-3%)
- **Liquidez:** Muito alta (maior do mundo)
- **Risco:** Médio (mercado estável mas edge pequeno)
- **Fase Recomendada:** 22-24 (após validação NBA + Football + MMA + 2-3 esportes VBQ-003)

### 10.2 Synergies com Outros Esportes
- **Feature Engineering:** Técnicas de time series aplicáveis
- **Model Architecture:** CatBoost/XGBoost reutilizável
- **Validation Framework:** Walk-forward CV adaptável
- **Risk Management:** Kelly e circuit breakers transferíveis

### 10.3 Future Expansion
- **Outras Ligas:** La Liga, Serie A, Bundesliga (similar architecture)
- **Cup Competitions:** FA Cup, Champions League (diferentes dynamics)
- **Player Props:** Goalscorer, assists (mercados emergentes)
- **Live Betting:** In-play betting em futebol (alta liquidez)

### 10.4 Estratégia de Entrada
- **Começar Conservador:** Focar em um mercado inicialmente (Asian Handicap)
- **Edge Pequeno mas Consistente:** Aceitar ROI 2-3% se consistente
- **Alta Liquidez = Alto Volume:** Compensa edge pequeno com volume
- **Foco em Long-Term:** Futebol é jogo de longo prazo

---

## 11. LINKS CRUZADOS

- [[43_Multi_Sport_Expansion/INDEX]] ← Secção mãe
- [[43_Multi_Sport_Expansion/ARQUITETURA_MULTI_ESPORTE]] → Arquitetura compartilhada
- [[43_Multi_Sport_Expansion/APIs_ESPORTOS]] → APIs para futebol
- [[43_Multi_Sport_Expansion/PRIORIZACAO_ESPORTOS]] → Priorização de esportes
- [[43_Multi_Sport_Expansion/EXPANSAO_NFL]] → Comparação com NFL expansion
- [[43_Multi_Sport_Expansion/EXPANSAO_TENNIS_ATP]] → Comparação com tennis expansion
- [[43_Multi_Sport_Expansion/EXPANSAO_ESPORTS_LOL]] → Comparação com LoL expansion
- [[01_Vision_And_Strategy/FILOSOFIA_MVP]] → Regra: um desporto de cada vez
- [[05_Machine_Learning/WALK_FORWARD_CV]] → Metodologia de validação
- [[06_Backtesting/BACKTEST_VS_REAL]] → Diferenças backtest vs real

---

**Data de Criação:** 2026-05-13
**Revisão Obrigatória:** Após conclusão de Fase 1 (Research)
**Owner:** Product Manager