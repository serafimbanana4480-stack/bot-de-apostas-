# EXPANSAO_TENNIS_ATP — Ténis ATP

**ID:** `MSE-002` | **Fase:** #phase/16-18 (VBQ-003) | **Owner:** Product Manager | **Status:** #status/pending

---

## 1. OBJETIVO

Expandir o sistema de value betting para o circuito ATP de ténis, aproveitando as características únicas do desporto que podem oferecer edge significativo.

---

## 2. PORQUÊ TÉNIS ATP

O ténis apresenta oportunidades únicas para value betting devido à sua natureza de desporto individual e à alta variabilidade de desempenho.

**Vantagens Estratégicas:**

- **Desporto Individual:** Sem dependência de teammates, performance mais previsível através de estatísticas individuais
- **Alta Volatilidade:** Pequenas alterações de estado físico têm impacto desproporcional no resultado
- **Mercados Diversos:** Match winner, sets, games, handicaps oferecem múltiplas oportunidades
- **Dados Disponíveis:** Estatísticas detalhadas de serve, return, surface performance
- **Menos Eficiência:** Menos liquidez que NBA/NFL = mais ineficiências a explorar

**Desafios Específicos:**

- **Lesões Frequentes:** Lesões não reportadas podem invalidar modelos rapidamente
- **Surface Variability:** Clay vs Grass vs Hard Court requer modelos separados
- **Motivation Variável:** Jogadores podem desistir em torneios menos importantes
- **Fadiga Acumulada:** Torneios consecutivos afetam performance drasticamente

---

## 3. DIFERENÇAS VS NBA

| Aspecto | NBA | Tennis ATP |
|---------|-----|------------|
| Jogos/época | 1230 | ~2000 (todos os torneios) |
| Frequência | Diária | Quase diária (torneios diferentes) |
| Unidade de Análise | Equipa | Jogador Individual |
| Variáveis Chave | Team stats, rest days | Serve %, return %, surface, H2H |
| Efeito Lesão | Mitigado por roster | Devastador (single point failure) |
| Volatilidade Odds | Média | Alta (in-game swings) |
| Liquidez | Alta | Média (exceto Grand Slams) |
| Sample Size por Entidade | 82 jogos/época | 50-80 jogos/época |

---

## 4. MERCADOS ALVO INICIAIS

### 4.1 Match Winner (1X2)
- **Liquidez:** Média-alta em Grand Slams, baixa em ATP 250
- **Edge Estimado:** Alto (4-6% potencial)
- **Complexidade:** Média
- **Prioridade:** 1

### 4.2 Set Betting (Correct Score)
- **Liquidez:** Baixa
- **Edge Estimado:** Muito alto (8-12% potencial)
- **Complexidade:** Alta
- **Prioridade:** 3

### 4.3 Total Games (Over/Under)
- **Liquidez:** Média
- **Edge Estimado:** Médio-alto (5-7% potencial)
- **Complexidade:** Média
- **Prioridade:** 2

---

## 5. REQUISITOS DE DADOS

### 5.1 Fontes de Dados
- **Tennis Abstract:** Estatísticas históricas gratuitas
- **ATP Tour API:** Dados oficiais (requer subscrição)
- **Oddshark/Flashscore:** Odds históricas
- **In-play Data:** Para validação de modelos de live betting (futuro)

### 5.2 Features Críticas
- **Serve Statistics:** 1st serve %, aces, double faults, serve points won
- **Return Statistics:** Return points won, break points converted/saved
- **Surface Performance:** Split stats por clay, grass, hard court
- **Recent Form:** Últimos 10-20 jogos, weighted por recência
- **Head-to-Head:** Histórico direto (importante em ténis)
- **Fatigue Metrics:** Dias desde último jogo, sets jogados recentemente
- **Ranking Points:** ATP ranking, live ranking
- **Tournament Importance:** Grand Slam vs Masters 1000 vs ATP 250

### 5.3 Pipeline de Dados
- Ingestão diária de resultados e odds
- Normalização de nomes de jogadores (múltiplas grafias)
- Agregação de estatísticas rolling window
- Feature engineering específica por surface
- Detecção de outliers (retirements, walkovers)

---

## 6. ARQUITETURA DO MODELO

### 6.1 Abordagem Inicial
- **Modelo Base:** XGBoost (similar ao NBA)
- **Target:** Probabilidade de vitória do jogador
- **Features:** 50-80 features iniciais
- **Validation:** Walk-forward CV com purged periods

### 6.2 Considerações Especiais
- **Surface-Specific Models:** Modelos separados para clay, grass, hard court
- **Tournament Tier Weights:** Grand Slams têm mais peso que ATP 250
- **Retirement Handling:** Excluir ou tratar separadamente jogos com retirement
- **Live Betting Potential:** Pré-engineering para future in-play models

---

## 7. CRITÉRIOS DE VALIDAÇÃO

### 7.1 Métricas Mínimas
- **CLV (Closed Line Value):** > 2.5%
- **Brier Score:** < mercado de referência
- **ROI Backtest:** > 6% (comissões incluídas)
- **Sharpe Ratio:** > 1.5
- **Max Drawdown:** < 15%

### 7.2 Backtest Requirements
- Mínimo 3 temporadas completas (2022-2024)
- Purged CV com look-forward periods adequados
- Slippage modelado (2-3% para ténis)
- Comissões incluídas (5% padrão)
- Stress test em Grand Slams vs torneios menores

### 7.3 Paper Trading
- 1 mês de paper trading antes de dinheiro real
- Foco em torneios de média-alta liquidez
- Tracking de divergências backtest vs real

---

## 8. RISCOS ESPECÍFICOS

### 8.1 Riscos de Dados
- **Retirements Não Reportados:** Jogadores desistem mid-match sem pré-aviso
- **Nome Inconsistências:** Mesmo jogador com grafias diferentes em fontes
- **Surface Classification:** Alguns torneios têm surfaces híbridas

### 8.2 Riscos de Modelo
- **Overfitting a Surface:** Modelo clay não generaliza para grass
- **Motivation Noise:** Jogadores "tank" em torneios menos importantes
- **Injury Information:** Lesões privadas não refletem em dados públicos

### 8.3 Riscos de Execução
- **Baixa Liquidez:** Torneios ATP 250 podem ter limites baixos
- **Rapid Odds Movement:** News de lesões movem odds instantaneamente
- **Schedule Changes:** Jogos adiados/transferidos com pouco aviso

---

## 9. ROADMAP DE IMPLEMENTAÇÃO

### Fase 1: Research (Semanas 1-4)
- [ ] Explorar fontes de dados disponíveis
- [ ] Analisar qualidade e completeness de dados históricos
- [ ] Definir feature set inicial
- [ ] Estudar literatura de tennis betting models

### Fase 2: Data Pipeline (Semanas 5-8)
- [ ] Implementar ingestão de dados Tennis Abstract
- [ ] Criar normalização de nomes de jogadores
- [ ] Build feature engineering pipeline
- [ ] Validar qualidade de dados (missing values, outliers)

### Fase 3: Model Development (Semanas 9-12)
- [ ] Treinar baseline XGBoost model
- [ ] Implementar walk-forward CV
- [ ] Tuning de hyperparameters com Optuna
- [ ] Calibração de probabilidades

### Fase 4: Backtesting (Semanas 13-16)
- [ ] Executar backtest 3 temporadas
- [ ] Analisar CLV, ROI, drawdown
- [ ] Stress test por surface e tournament tier
- [ ] Comparar vs mercado de referência

### Fase 5: Validation (Semanas 17-20)
- [ ] Paper trading 1 mês
- [ ] Ajustar modelo baseado em resultados reais
- [ ] Documentar divergências backtest vs real
- [ ] Preparar para produção se critérios cumpridos

---

## 10. LINKS CRUZADOS

- [[43_Multi_Sport_Expansion/INDEX]] ← Secção mãe
- [[43_Multi_Sport_Expansion/ARQUITETURA_MULTI_ESPORTE]] → Arquitetura compartilhada
- [[43_Multi_Sport_Expansion/EXPANSAO_NFL]] → Comparação com NFL expansion
- [[01_Vision_And_Strategy/FILOSOFIA_MVP]] → Regra: um desporto de cada vez
- [[05_Machine_Learning/WALK_FORWARD_CV]] → Metodologia de validação
- [[06_Backtesting/BACKTEST_VS_REAL]] → Diferenças backtest vs real

---

**Data de Criação:** 2026-05-13
**Revisão Obrigatória:** Após conclusão de Fase 1 (Research)
**Owner:** Product Manager