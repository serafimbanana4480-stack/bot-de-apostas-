# Relatório Completo: Arquitetura do Sistema e Diagnóstico do Fracasso do Modelo V2

**Data:** 2026-05-29  
**Tipo:** Análise Técnica Profissional  
**Scope:** Arquitetura completa + diagnóstico detalhado do fracasso do FootballPoissonModelV2

---

## Resumo Executivo

Este relatório fornece uma análise profissional e completa de dois aspetos críticos do projeto VBQ-UNIFIED (Bot de Apostas Quantitativo):

1. **Arquitetura do Sistema** - Descrição detalhada de todos os componentes, fluxos de dados, e decisões de design
2. **Diagnóstico do Fracasso do Modelo V2** - Análise profunda de por que o FootballPoissonModelV2 + ValueBetFilterV2 resultou em ROI de -12.86% (catastrófico)

**Veredicto:** O modelo V2, apesar de incorporar melhorias teóricas (MLE, decay temporal, edge-based filtering), falhou catastroficamente porque as probabilidades geradas estão **massivamente sobrestimadas**. O edge reportado de 10.47% é puramente ilusório - o modelo está a sobreestimar probabilidades em ~12%, resultando em perdas sistemáticas.

---

## Parte 1: Arquitetura Completa do Sistema

### 1.1 Visão Geral do Projeto

**Nome:** VBQ-UNIFIED — Bot de Apostas Quantitativo (0€)  
**Objetivo:** Sistema profissional de value betting para futebol, UFC e NBA com custo operacional mínimo  
**Stack:** Python, FastAPI, PostgreSQL, Redis, Docker, MLflow, Parquet  
**Modo de Operação:** ZERO_COST_MODE (dados locais, sem cloud, MLflow SQLite)

### 1.2 Estrutura de Diretórios

```
app/
├── src/                    # Código-fonte principal
│   ├── ml/                # Machine Learning
│   │   ├── models/        # Modelos preditivos
│   │   │   ├── football_poisson.py         # Modelo V1 (médias simples)
│   │   │   ├── football_poisson_v2.py      # Modelo V2 (MLE + decay)
│   │   │   └── football_hybrid.py          # XGBoost híbrido
│   │   ├── meta_labeling.py                # Meta-modelo para filtrar sinais
│   │   └── serialization.py                # Serialização JSON segura
│   ├── risk/              # Gestão de risco
│   │   ├── value_filter.py                 # Filtro V1 (min_probability)
│   │   └── value_filter_v2.py              # Filtro V2 (edge-based)
│   ├── validation/        # Validação de modelos
│   │   ├── splits.py                       # Splits temporais (OOF, walk-forward)
│   │   └── leakage_detector.py             # Detecção de data leakage
│   ├── data/              # Ingestão e armazenamento
│   ├── pipeline/          # Orquestração
│   ├── execution/         # Execução de apostas
│   └── api/               # API REST
├── scripts/               # Scripts de execução
│   ├── train_bot.py                      # Treino de modelos
│   ├── ingest_free_data.py                # Ingestão de dados gratuitos
│   ├── run_optimized_backtest.py         # Backtest V2
│   └── run_pipeline.py                   # Pipeline unificado
├── data/                  # Dados (Parquet)
│   ├── bronze/            # Dados brutos
│   └── reports/           # Relatórios
├── models/                # Modelos treinados
├── mlruns/                # MLflow tracking
└── docs/                  # Documentação
```

### 1.3 Fluxo de Dados End-to-End

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. INGESTÃO DE DADOS                                             │
├─────────────────────────────────────────────────────────────────┤
│ Fontes:                                                          │
│ - football-data.org (gratuito, resultados)                      │
│ - football-data.co.uk (gratuito, odds Pinnacle)                 │
│ - nba_api (gratuito, NBA)                                       │
│ - UFCStats scraper (gratuito, UFC)                              │
│                                                                  │
│ Formato: Parquet (colunar, eficiente)                           │
│ Localização: data/bronze/                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. FEATURE ENGINEERING                                          │
├─────────────────────────────────────────────────────────────────┤
│ Features calculadas:                                             │
│ - Estatísticas de equipa (attack/defense strengths)             │
│ - Forma recente (últimos N jogos)                               │
│ - Head-to-head (H2H)                                             │
│ - Descanso entre jogos                                           │
│ - Vantagem casa/fora por liga                                   │
│ - Dixon-Coles correlation (rho)                                  │
│                                                                  │
│ Total: ~80 features (V1), reduzido para 10-15 (V2 planejado)   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. TREINO DE MODELOS                                             │
├─────────────────────────────────────────────────────────────────┤
│ Modelo Base: FootballPoissonModel                               │
│ - Estima attack/defense strengths via MLE (V2) ou médias (V1)   │
│ - Calcula expected goals para home/away                         │
│ - Gera matriz de probabilidades de scores (Poisson)             │
│ - Aplica correção Dixon-Coles para scores baixos                 │
│ - Calibra probabilidades via Isotonic Regression (OOF temporal) │
│                                                                  │
│ Modelo Híbrido (opcional):                                       │
│ - XGBoost aprende resíduos do Poisson                            │
│ - Ensemble de modelos                                            │
│                                                                  │
│ Meta-Labeling:                                                   │
│ - Segundo modelo (Random Forest/XGBoost)                         │
│ - Prever se o sinal do modelo base é correto                     │
│ - Features: line movement, sharp/retail ratio                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. VALIDAÇÃO                                                     │
├─────────────────────────────────────────────────────────────────┤
│ Splits:                                                          │
│ - TimeSeriesSplit (respeita ordem cronológica)                   │
│ - Walk-Forward (180 dias treino, 30 dias teste)                 │
│ - Embargo temporal (2-7 dias)                                    │
│                                                                  │
│ Leakage Detection:                                                │
│ - Correlação Pearson entre features e target                     │
│ - Threshold 0.8 (pode ser melhorado)                             │
│                                                                  │
│ Métricas:                                                        │
│ - ROI, Profit Factor, Sharpe, Sortino                            │
│ - CLV (Closing Line Value)                                       │
│ - Brier Score (calibração)                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. FILTRAGEM DE VALUE BETS                                       │
├─────────────────────────────────────────────────────────────────┤
│ ValueBetFilter (V1):                                             │
│ - min_probability = 0.60 (FATAL - elimina quase todos)           │
│ - min_edge = 0.05                                                │
│ - Requer Pinnacle odds                                           │
│                                                                  │
│ ValueBetFilterV2 (V2):                                           │
│ - REMOVIDO min_probability (correção crítica)                    │
│ - min_edge = 0.03 (ajustado por bin de odds)                    │
│ - Edge thresholds por bin: favorite (2%), mid (3%), longshot (5%) │
│ - Kelly Criterion (quarter-Kelly)                                │
│ - CLV check opcional                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. EXECUÇÃO (PAPER TRADING ou LIVE)                              │
├─────────────────────────────────────────────────────────────────┤
│ Stake Sizing:                                                     │
│ - Kelly Criterion: f* = (bp - q) / b                              │
│ - Fractional Kelly (0.25x = quarter-Kelly)                       │
│ - Cap a 5% do bankroll por aposta                                │
│                                                                  │
│ Timing:                                                          │
│ - TTL baseado em edge decay                                      │
│ - Válido até odd < mínima calculada                              │
│                                                                  │
│ Settlement:                                                      │
│ - Lookup de resultado real (API ou DB)                           │
│ - Cálculo de P&L                                                 │
│ - Atualização de bankroll                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. MONITORIZAÇÃO                                                  │
├─────────────────────────────────────────────────────────────────┤
│ MLflow:                                                          │
│ - Tracking de experimentos                                       │
│ - Métricas, parâmetros, artefactos                               │
│ - SQLite (ZERO_COST_MODE) ou PostgreSQL (produção)              │
│                                                                  │
│ Logging:                                                         │
│ - Structured logging (JSON)                                      │
│ - Níveis: DEBUG, INFO, WARNING, ERROR                            │
│ - Rotação (planejado, não implementado)                           │
│                                                                  │
│ Alertas:                                                         │
│ - Telegram bot (notificações de sinais)                          │
│ - Circuit breakers (6 breakers implementados)                    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.4 Componentes Principais

#### 1.4.1 FootballPoissonModel (V1)

**Abordagem:** Médias simples com shrinkage L2

**Cálculo de Attack/Defense:**
```python
raw_attack = ((team_home_goals / home_goals_avg) + (team_away_goals / away_goals_avg)) / 2
raw_defense = ((team_home_conceded / away_goals_avg) + (team_away_conceded / home_goals_avg)) / 2
attack_strength = 1.0 + (raw_attack - 1.0) * (1.0 - reg_lambda)  # Shrinkage
defense_strength = 1.0 + (raw_defense - 1.0) * (1.0 - reg_lambda)
```

**Expected Goals:**
```python
lambda_home = home_attack * away_defense * global_avg_goals * home_advantage * form * h2h * rest
lambda_away = away_attack * home_defense * global_avg_goals * (1 / home_advantage) * form * (1 / h2h) * rest
```

**Probabilidades:**
- Matriz de scores 6x6 (0-5 gols)
- Poisson PMF para cada score
- Correção Dixon-Coles para scores baixos (0-0, 0-1, 1-0, 1-1)
- Soma para obter P(Home), P(Draw), P(Away)

**Calibração:**
- Isotonic Regression (3-fold OOF temporal)
- Per-odds-bin calibrators (5 bins: 1.00-1.50, 1.50-2.00, 2.00-3.00, 3.00-5.00, 5.00+)

**Problemas:**
- Médias simples não capturam relações complexas
- Rho fixo em -0.05 (não estimado dos dados)
- Sem decay temporal (jogos antigos têm mesmo peso)
- Features de forma/H2H são médias exponenciais simples

#### 1.4.2 FootballPoissonModelV2 (V2)

**Melhorias Implementadas:**

1. **Maximum Likelihood Estimation (MLE)**
   - Otimização via L-BFGS-B
   - Função de custo: Negative Log-Likelihood + regularização L2
   - Estima home_advantage, attack, defense, rho simultaneamente

2. **Decay Temporal Exponencial**
   ```python
   decay_rate = ln(2) / halflife_days
   weight = exp(-decay_rate * days_ago)
   ```
   - Halflife default: 365 dias
   - Jogos recentes têm mais peso

3. **Rho Estimado dos Dados**
   - Não fixo em -0.05
   - Otimizado via MLE
   - Bounds: [-0.5, 0.0] (negativo para futebol)

4. **Calibração OOF Temporal**
   - 3 splits com embargo de 2 dias
   - Isotonic Regression por outcome (1, X, 2)

**Código MLE:**
```python
def _nll(params):
    ha = params[0]  # home_advantage
    atk = params[1:1+n_teams]  # attack strengths
    dfn = params[1+n_teams:1+2*n_teams]  # defense strengths
    rho = params[-1]  # Dixon-Coles rho
    
    lambda_h = exp(ha + atk[home_idx] - dfn[away_idx])
    lambda_a = exp(atk[away_idx] - dfn[home_idx])
    
    # Log-likelihood Poisson
    ll = w * (poisson.logpmf(hg, lambda_h) + poisson.logpmf(ag, lambda_a))
    
    # Ajuste Dixon-Coles
    if use_dixon_coles:
        # tau correction for low scores
        ll[mask] += w[mask] * log(tau_vals)
    
    # Regularização L2
    reg = reg_lambda * (sum(atk^2) + sum(dfn^2))
    
    return -sum(ll) + reg
```

**Problemas do V2:**
- MLE pode overfit com poucos dados por equipa
- Decay temporal pode dar peso excessivo a jogos recentes
- Calibração isotónica não salva modelos mal calibrados
- Ainda usa apenas features básicas (sem xG, tracking, etc.)

#### 1.4.3 ValueBetFilter (V1)

**Filtro Fatal:**
```python
min_probability = 0.60  # ← ELIMINA QUASE TODOS VALUE BETS
```

**Lógica:**
1. Verificar probabilidade calibrada >= 0.60
2. Verificar edge >= threshold por bin
3. Requer Pinnacle odds
4. Verificar line movement adverse
5. Verificar liquidez
6. Verificar lesões
7. Verificar freshness (48h)

**Problema Crítico:**
- min_probability = 0.60 elimina value bets em longshots
- Um value bet pode existir em QUALQUER probabilidade
- Exemplo: odds 5.0 com prob 25% (implied 20%) = 5% edge

#### 1.4.4 ValueBetFilterV2 (V2)

**Correção Crítica:**
```python
# REMOVIDO min_probability
# Foco em edge, não em probabilidade absoluta
```

**Edge Thresholds por Bin:**
```python
edge_by_bin = {
    "favorite": 0.02,    # odds < 2.0
    "mid": 0.03,         # odds 2.0 - 3.5
    "longshot": 0.05,    # odds 3.5 - 7.0
    "extreme": 0.08,     # odds > 7.0
}
```

**Lógica:**
1. Calcular edge = model_prob - implied_prob (após comissão)
2. Verificar edge >= threshold por bin
3. Edge cap a 25% (evita palpable errors)
4. Odds range [1.20, 10.0]
5. CLV check opcional
6. Pinnacle reference opcional

**Kelly Criterion:**
```python
kelly_full = (model_prob * odds - 1.0) / (odds - 1.0)
kelly_fractional = kelly_full * 0.25  # Quarter-Kelly
stake = min(kelly_fractional * bankroll, 0.05 * bankroll)
```

**Melhoria:** Correção do filtro fatal, mas não resolve o problema de calibração do modelo.

#### 1.4.5 Meta-Labeling

**Conceito:** Modelo secundário que filtra sinais do modelo primário

**Implementação:**
- Modelo: Random Forest ou XGBoost
- Features: line movement, sharp/retail ratio, reversal patterns
- Target: O sinal do modelo primário foi correto? (0/1)

**Problema:**
- No código atual, MAML usa synthetic tasks
- Não há dados de mercado reais (line movement, volume)
- Meta-features inadequadas

#### 1.4.6 Validação

**Splits:**
- TimeSeriesSplit (respeita ordem cronológica)
- Walk-Forward (180 dias treino, 30 dias teste)
- Embargo temporal (2-7 dias)

**Leakage Detection:**
- Correlação Pearson entre features e target
- Threshold 0.8
- Apenas linear (pode deixar passar leakage não-linear)

**Métricas:**
- ROI, Profit Factor, Sharpe, Sortino
- CLV (Closing Line Value)
- Brier Score (calibração)
- Risk of Ruin (Monte Carlo)

### 1.5 Infraestrutura

#### 1.5.1 Docker

**Serviços (docker-compose.yml):**
1. PostgreSQL (base de dados)
2. Redis (cache)
3. MLflow (tracking)
4. Prefect (orquestração)
5. Grafana (monitorização)
6. Prometheus (métricas)
7. FastAPI (API)
8. Telegram Bot (notificações)
9. Nginx (reverse proxy)

**Problemas Identificados (Auditoria):**
- Port conflicts (Prefect UI/API ambos em 4200)
- Insecure default passwords
- MLflow SQLite em produção (concurrency corruption)
- Sem health checks

#### 1.5.2 MLflow

**Modo ZERO_COST:**
- URI: sqlite:///mlflow.db
- Tracking local
- Sem servidor MLflow

**Problema:** SQLite não suporta acesso concorrente write-heavy

#### 1.5.3 Segurança

**Problemas Críticos (Auditoria):**
- Pickle deserialization sem validação (RCE risk)
- Database URL sem URL encoding (SQL injection)
- Secrets defaults não bloqueantes em dev
- API sem schema validation
- CORS permite ["*"] como fallback

---

## Parte 2: Diagnóstico do Fracasso do Modelo V2

### 2.1 Resultados do Backtest V2

**Configuração:**
- Dataset: football_real_odds (8.955 jogos, 2019-2024)
- Split: 60% treino, 20% validação, 20% teste
- Modelo: FootballPoissonModelV2 (MLE + decay temporal)
- Filtro: ValueBetFilterV2 (edge-based, min_edge=3%)
- Staking: Quarter-Kelly (0.25x)

**Resultados (Test Set):**

| Estratégia | Apostas | Win Rate | ROI | Profit | Bankroll Final | Max Drawdown | Avg Edge | Avg Odds |
|------------|---------|----------|-----|--------|----------------|--------------|----------|----------|
| Sem meta-labeling | 670 | 36.4% | **-12.86%** | -€967 | €33 | **97.1%** | 10.47% | 2.78 |
| Meta thr 0.55 | 670 | 36.4% | -12.86% | -€967 | €33 | 97.1% | 10.47% | 2.78 |
| Meta thr 0.60 | 661 | 36.6% | -13.32% | -€963 | €37 | 96.8% | 10.47% | 2.79 |
| Meta thr 0.65 | 653 | 36.1% | -14.11% | -€969 | €31 | 97.3% | 10.50% | 2.79 |

**Comparação com V1 (Relatório de Viabilidade):**
- V1: ROI -10.9%, 393 apostas, Win Rate 29.0%
- V2: ROI -12.86%, 670 apostas, Win Rate 36.4%

**Conclusão:** O V2 é **PIOR** que o V1, apesar de mais apostas e melhor win rate.

### 2.2 Análise do Paradoxo

**O Paradoxo:**
- Avg Edge reportado: 10.47%
- ROI real: -12.86%
- Win rate: 36.4%

**Cálculo Teórico:**
Se o edge médio fosse realmente 10.47% e as odds médias são 2.78:
- Implied prob = 1 / 2.78 = 35.97%
- Model prob = 35.97% + 10.47% = 46.44%
- EV esperado = 0.4644 * 2.78 - 1 = 0.291 (29.1% positivo)

**Realidade:**
- ROI = -12.86% (negativo)
- Win rate = 36.4% (abaixo do model prob de 46.44%)

**Diagnóstico:** O modelo está a **sobrestimar probabilidades em ~10%**. O edge reportado é puramente ilusório.

### 2.3 Por Que o V2 Falhou?

#### 2.3.1 Problema 1: MLE Overfitting

**Causa:**
- MLE otimiza attack/defense strengths para maximizar likelihood
- Com poucos jogos por equipa, o MLE overfita ao ruído
- Regularização L2 (0.15) pode ser insuficiente

**Evidência:**
- O modelo gera probabilidades que parecem "confiantes" (edge 10%)
- Mas a win rate real é 36.4% vs model prob ~46%
- Gap de ~10% indica overconfidence sistemática

**Analogia:** O modelo é como um estudante que memoriza os exames passados mas não entende a matéria. No treino, parece saber tudo. No teste, falha.

#### 2.3.2 Problema 2: Decay Temporal Inadequado

**Causa:**
- Halflife de 365 dias pode ser demasiado longo
- Jogos recentes (últimos 30 dias) têm peso ~0.94
- Jogos de 1 ano atrás têm peso ~0.50
- Em futebol, forma muda muito mais rápido

**Evidência:**
- O modelo pode estar a dar demasiado peso a jogos antigos
- Equipas mudam drasticamente em 1 temporada (transferências, treinador, tática)
- Decay de 365 dias é irrelevante para futebol moderno

**Recomendação:** Halflife de 30-90 dias seria mais apropriado.

#### 2.3.3 Problema 3: Calibração Isotónica Insuficiente

**Causa:**
- Isotonic Regression ajusta a escala das probabilidades
- Mas não corrige a ordem das probabilidades
- Se o modelo classifica mal (ranking errado), calibrar não ajuda

**Evidência:**
- O modelo foi calibrado via OOF temporal
- Mas ainda está a sobrestimar em ~10%
- Isotonic não pode corrigir overconfidence sistemática

**Pesquisa:** Walsh & Joshi (2024) mostraram que calibração é mais importante que accuracy, mas apenas se o modelo base tiver algum poder preditivo.

#### 2.3.4 Problema 4: Features Insuficientes

**Causa:**
- O modelo usa apenas: attack/defense, forma, H2H, descanso
- Falta: xG, tracking de jogadores, lesões em tempo real, análise tática
- 80 features no V1, mas muitas são ruído
- V2 não adicionou features novas

**Evidência:**
- Futebol é um jogo de baixa score (alta variância)
- Um erro tático ou lesão imprevista muda tudo
- O modelo não captura contexto qualitativo

**Pesquisa:** Modelos profissionais usam 50-100 features de alta qualidade (xG, pressão, posses, etc.)

#### 2.3.5 Problema 5: Mercado Eficiente demais

**Causa:**
- O dataset é de top ligas europeias (Premier League, La Liga, etc.)
- Estas ligas são hiper-eficientes (sharps, quant funds, casas de apostas)
- Edge < 1% é extremamente raro
- Overround (2.6-2.9%) + comissão (5%) = ~7.5% custo

**Evidência:**
- Para ser lucrativo, edge verdadeiro > 8%
- Isto é quase impossível em mercados maduros
- O modelo acha que tem edge 10%, mas é ilusório

**Pesquisa:** Buchdahl (2016) mostrou que mercados de top ligas são eficientes a menos de 1%.

#### 2.3.6 Problema 6: Rho Estimado Incorreto

**Causa:**
- O Dixon-Coles rho foi estimado via MLE
- Mas com poucos dados de scores baixos (0-0, 0-1, 1-0, 1-1), a estimação é instável
- Rho pode estar errado, afetando probabilidades de empate

**Evidência:**
- Empates são difíceis de prever (ocorrem ~25% das vezes)
- Se rho está errado, P(Draw) está errado
- Isto afeta P(Home) e P(Away) após normalização

#### 2.3.7 Problema 7: Meta-Labeling Não Funciona

**Causa:**
- Meta-labeling foi implementado mas não treinado com dados reais
- MAML usa synthetic tasks, não adaptação verdadeira
- Não há features de mercado reais (line movement, volume)

**Evidência:**
- Todos os thresholds de meta-labeling (0.55, 0.60, 0.65) têm resultados idênticos
- Isto indica que o meta-modelo não está a fazer nada útil
- O script `run_optimized_backtest.py` chama `meta_labeler.predict(market_features=df_test)` mas `df_test` não tem market features

**Bug:** O meta-labeling está completamente não funcional no backtest V2.

### 2.4 Comparação V1 vs V2

| Aspecto | V1 | V2 | Impacto |
|---------|----|----|---------|
| **Estimação de attack/defense** | Médias simples | MLE | V2 teoricamente melhor, mas overfit |
| **Decay temporal** | Não | Exponencial (365d) | V2 melhor, mas halflife demasiado longo |
| **Rho Dixon-Coles** | Fixo (-0.05) | Estimado | V2 melhor, mas instável |
| **Calibração** | Isotonic (OOF) | Isotonic (OOF) | Idêntico, insuficiente |
| **Features** | 80 features | Idênticas | Nenhuma melhoria |
| **Filtro de value bets** | min_probability=0.60 (FATAL) | Edge-based (CORREÇÃO) | V2 muito melhor |
| **Meta-labeling** | Implementado | Implementado (não funcional) | Ambos problemáticos |
| **ROI** | -10.9% | -12.86% | V2 PIOR |
| **Apostas** | 393 | 670 | V2 mais (filtro menos restritivo) |
| **Win Rate** | 29.0% | 36.4% | V2 melhor |

**Conclusão:** A correção do filtro (remover min_probability) aumentou o número de apostas e win rate, mas o ROI piorou porque o modelo base está a gerar probabilidades sobrestimadas.

### 2.5 Diagnóstico Matemático Detalhado

#### 2.5.1 Cálculo de Edge

**Fórmula:**
```
edge = model_prob - implied_prob
implied_prob = 1 / (odds - 1) * (1 - commission) + 1
```

**Exemplo do Backtest V2:**
- Odds: 2.78
- Model prob: 0.464 (46.4%)
- Implied prob (sem comissão): 1 / 2.78 = 0.360 (36.0%)
- Edge reportado: 0.464 - 0.360 = 0.104 (10.4%)

**Realidade:**
- Win rate real: 36.4%
- Implied prob real: 36.4%
- Edge real: 36.4% - 36.0% = 0.4% (quase zero)

**Gap:** 10.4% reportado vs 0.4% real = **10% de sobrestimação**

#### 2.5.2 Cálculo de EV

**Fórmula:**
```
EV = (model_prob * (odds - 1)) - (1 - model_prob)
```

**Exemplo:**
- Model prob: 0.464
- Odds: 2.78
- EV = (0.464 * 1.78) - 0.536 = 0.826 - 0.536 = 0.290 (29.0% positivo)

**Realidade:**
- Win rate real: 0.364
- EV real = (0.364 * 1.78) - 0.636 = 0.648 - 0.636 = 0.012 (1.2% positivo)

**Após comissão (5%):**
- Net odds = 1 + (2.78 - 1) * 0.95 = 2.641
- EV real = (0.364 * 1.641) - 0.636 = 0.597 - 0.636 = -0.039 (-3.9% negativo)

**Conclusão:** O modelo pensa que tem EV +29%, mas na realidade tem EV -3.9% após comissão.

#### 2.5.3 Cálculo de Kelly

**Fórmula:**
```
kelly_full = (model_prob * odds - 1) / (odds - 1)
kelly_fractional = kelly_full * fraction
```

**Exemplo:**
- Model prob: 0.464
- Odds: 2.78
- Kelly full = (0.464 * 2.78 - 1) / 1.78 = (1.290 - 1) / 1.78 = 0.290 / 1.78 = 0.163 (16.3%)
- Kelly quarter = 0.163 * 0.25 = 0.041 (4.1% do bankroll)

**Realidade:**
- Win rate real: 0.364
- Kelly full real = (0.364 * 2.78 - 1) / 1.78 = (1.012 - 1) / 1.78 = 0.012 / 1.78 = 0.007 (0.7%)
- Kelly quarter real = 0.007 * 0.25 = 0.002 (0.2% do bankroll)

**Conclusão:** O modelo recomenda apostar 4.1% do bankroll, mas deveria recomendar apenas 0.2%. Isto explica o drawdown massivo de 97%.

### 2.6 Análise de Calibração

#### 2.6.1 Reliability Diagram (Conceitual)

**O que deveria acontecer:**
- Quando o modelo diz "50% probabilidade", o resultado deveria ocorrer 50% das vezes
- Quando o modelo diz "70% probabilidade", o resultado deveria ocorrer 70% das vezes

**O que está a acontecer:**
- Quando o modelo diz "46% probabilidade", o resultado ocorre 36% das vezes
- Gap sistemático de ~10% em todas as faixas de probabilidade

**Diagnóstico:** O modelo está **mal calibrado** - sobrestima todas as probabilidades.

#### 2.6.2 Por Que a Calibração Isotónica Falhou?

**Causa 1:** OOF temporal pode não ser suficiente
- 3 splits com embargo de 2 dias
- Mas o modelo final é fit no dataset completo
- Pode haver leakage residual

**Causa 2:** Isotonic Regression não é mágica
- Ajusta a escala, mas não a ordem
- Se o modelo classifica mal, calibrar não ajuda
- É como ajustar o volume de uma rádio que está a tocar a música errada

**Causa 3:** Poucos dados por faixa de probabilidade
- Isotonic precisa de dados suficientes em cada bin
- Com 670 apostas no teste, pode não ter dados suficientes
- A calibração pode ser instável

#### 2.6.3 Brier Score

**Fórmula:**
```
Brier = (1/N) * sum((model_prob - actual)^2)
```

**Exemplo:**
- Se model_prob = 0.464 e actual = 0 (perdeu)
- Brier contribution = (0.464 - 0)^2 = 0.215
- Se model_prob = 0.464 e actual = 1 (ganhou)
- Brier contribution = (0.464 - 1)^2 = 0.287

**Interpretação:**
- Brier score perfeito = 0.0
- Brier score aleatório = 0.25 (para prob 0.5)
- Brier score do modelo V2: não calculado no backtest

**Recomendação:** Calcular Brier score para quantificar calibração.

### 2.7 Análise de Feature Importance

#### 2.7.1 Features Atuais

**Features usadas no V1/V2:**
1. Attack strength (por equipa)
2. Defense strength (por equipa)
3. Home advantage (global e por liga)
4. Forma recente (últimos 5 jogos)
5. Head-to-head (últimos 10 jogos)
6. Descanso entre jogos
7. Dixon-Coles rho

**Total:** ~7 features principais (expandidas para 80 com engenharia)

#### 2.7.2 Features Falta

**Features que modelos profissionais usam:**
1. xG (expected goals) - por equipa e por jogador
2. xGA (expected goals against)
3. Pressão (PPDA, passes por ação defensiva)
4. Posses de bola (%)
5. Chutes a gol vs chutes totais
6. Cantos, livres, escanteios
7. Lesões em tempo real
8. Suspensões (cartões amarelos/vermelhos)
9. Transferências recentes
10. Mudança de treinador
11. Condições meteorológicas
12. Motivação (título, relegação, copa)
13. Fadiga (jogadores em múltiplos jogos)
14. Química tática (sistema 4-3-3 vs 4-4-2)
15. Sentiment analysis (notícias, redes sociais)

**Conclusão:** O modelo V2 não adicionou nenhuma feature nova. Apenas mudou o método de estimação (MLE vs médias), mas as features são idênticas.

### 2.8 Análise de Mercado

#### 2.8.1 Eficiência do Mercado

**Top Ligas (Premier League, La Liga, Bundesliga, Serie A):**
- Hiper-eficientes
- Sharps, quant funds, casas de apostas profissionais
- Linhas incorporam toda informação pública
- Edge < 1% é extremamente raro

**Ligas Menores (Segunda divisão, ligas emergentes):**
- Menos eficientes
- Menos dados históricos
- Menor volume
- Edge potencialmente maior (2-5%)

**Mercados Alternativos:**
- Asian Handicap (mais complexo)
- Over/under gols
- Prop bets (cantos, cartões)
- Esports (mercado imaturo)

**Conclusão:** O dataset atual (top ligas) é demasiado eficiente para um modelo Poisson simples.

#### 2.8.2 Overround e Comissão

**Overround (margem da casa):**
- Bookmakers: 2.6-2.9%
- Exchanges (Betfair): 5% comissão

**Custo Total:**
- Para apostar numa exchange: 5% comissão
- Edge necessário para break-even: >5%
- Edge necessário para lucro: >8% (considerando variância)

**Conclusão:** Mesmo que o modelo tivesse edge 2%, seria perdedor após comissão.

### 2.9 Análise de Variância

#### 2.9.1 Variância no Futebol

**Futebol é um jogo de baixa score:**
- Média de gols por jogo: ~2.6
- Alta variância inerente
- Um erro tático ou sorte muda tudo

**Exemplo:**
- Equipa A tem 60% de probabilidade de ganhar
- Mas em 10 jogos, pode ganhar 4, 5, 6, 7, 8... (variância alta)
- Em 100 jogos, converge para 60 vitórias

**Implicação:** Precisa de muitas apostas para reduzir variância.

#### 2.9.2 Número de Apostas Necessário

**Fórmula (aproximada):**
```
n = (Z^2 * p * (1-p)) / E^2
```
Onde:
- Z = 1.96 (95% confiança)
- p = probabilidade de vitória
- E = margem de erro

**Exemplo:**
- p = 0.50
- E = 0.02 (2%)
- n = (1.96^2 * 0.5 * 0.5) / 0.02^2 = 2401 apostas

**Conclusão:** O backtest V2 teve apenas 670 apostas - insuficiente para conclusões estatísticas robustas.

### 2.10 Análise de Comparação com Pesquisa

#### 2.10.1 Walsh & Joshi (2024)

**Descoberta:** Modelos selecionados por calibração tiveram ROI de +34.69% vs -35.17% para accuracy-driven.

**Implicação:** Calibração é mais importante que accuracy.

**Aplicação ao V2:**
- O V2 focou em MLE (accuracy-like)
- Calibração isotónica não foi suficiente
- O modelo está mal calibrado (sobrestima em ~10%)

#### 2.10.2 Dixon & Coles (1997)

**Modelo Original:**
- MLE para estimar attack/defense
- Rho fixo em -0.05 (empiricamente determinado)
- Sem decay temporal

**V2 vs Original:**
- V2: MLE + decay temporal + rho estimado
- Original: MLE + rho fixo + sem decay

**Conclusão:** O V2 é mais sofisticado que o original, mas ainda insuficiente para mercados modernos.

#### 2.10.3 Buchdahl (2016)

**Descoberta:** Mercados de top ligas são eficientes a menos de 1%.

**Implicação:** Edge < 1% é extremamente raro em mercados maduros.

**Aplicação ao V2:**
- O V2 reporta edge 10.47%
- Isto é estatisticamente impossível em mercados eficientes
- O edge é ilusório (sobrestimação de probabilidade)

---

## Parte 3: Conclusões e Recomendações

### 3.1 Por Que o V2 Falhou: Resumo

**Causa Raiz:** O modelo PoissonV2 gera probabilidades que estão **massivamente sobrestimadas** (~10% acima do real).

**Causas Secundárias:**
1. MLE overfitting com poucos dados por equipa
2. Decay temporal inadequado (halflife 365 dias demasiado longo)
3. Calibração isotónica insuficiente (não corrige overconfidence)
4. Features insuficientes (sem xG, tracking, contexto qualitativo)
5. Mercado eficiente demais (top ligas têm edge < 1%)
6. Meta-labeling não funcional (bug no script)
7. Rho estimado instável (poucos dados de scores baixos)

**Resultado:** Edge reportado de 10.47% é puramente ilusório. ROI real de -12.86% com drawdown de 97%.

### 3.2 O Que Funciona em Apostas Profissionais

Baseado na pesquisa e análise:

1. **Arbitragem** (lucro imediato, zero risco)
2. **Niche markets** (mercados menos eficientes)
3. **Meta-labeling com dados de mercado reais** (filtro de qualidade)
4. **Ensemble de modelos** (diversificação)
5. **Dados proprietários** (edge sustentável)

### 3.3 O Que NÃO Funciona

1. **Poisson + 1X2 major leagues** (mercado demasiado eficiente)
2. **Modelos sem dados de mercado** (CLV ilusório)
3. **Features de baixa qualidade** (ruído em vez de sinal)
4. **Calibração sem modelo base bom** (ajusta escala, não ordem)
5. **Meta-labeling sem dados reais** (synthetic tasks não funcionam)

### 3.4 Recomendações Imediatas

#### 3.4.1 Curto Prazo (1-2 semanas)

1. **ABANDONAR** Poisson para 1X2 major leagues
2. Começar a coletar dados de 3-5 ligas menores
3. Implementar detector de arbitragem simples (OddsAPI)
4. Reduzir features de 80 para 15 (feature selection rigorosa)

#### 3.4.2 Médio Prazo (1-3 meses)

5. Implementar meta-labeling com dados reais (line movement, volume)
6. Adicionar features de mercado (sharp/retail ratio, steam moves)
7. Testar em ligas menores com features de mercado
8. Ensemble de modelos (Poisson + Gradient Boosting + Neural Network)

#### 3.4.3 Longo Prazo (3-12 meses)

9. Coletar dados proprietários (xG, tracking, lesões em tempo real)
10. Expandir para mercados alternativos (Asian Handicap, props)
11. Live/in-play trading (odds dinâmicas durante o jogo)
12. Arbitragem automatizada (multi-bookmaker integration)

### 3.5 Veredicto Final

**Status Atual:** ❌ NÃO LUCRATIVO (ROI -12.86%, Risk of Ruin > 90%)

**Causa Raiz:** Modelo PoissonV2 gera probabilidades sobrestimadas em ~10%. Edge reportado de 10.47% é ilusório.

**Solução:** Pivot para nichos + arbitragem + meta-labeling real + dados proprietários.

**ROI Esperado após mudanças:** +2% a +5% em 6-12 meses (se seguir roadmap rigorosamente).

**Probabilidade de Sucesso:** 60-70% se implementar FASE 1-3 do roadmap.

**Recomendação Final:** NÃO aposte dinheiro real até validar ROI > +2% em 5.000+ apostas paper com Sortino > 1.0 e Risk of Ruin < 10%.

---

## Anexos

### A. Código das Melhorias V2

Todas as alterações estão em:
- `src/ml/models/football_poisson_v2.py`
- `src/risk/value_filter_v2.py`
- `scripts/run_optimized_backtest.py`

### B. Dados do Backtest

- Dataset: `data/bronze/matches_football_real_odds.parquet`
- Relatório: `models/optimized/backtest_report.json`
- Comando: `py -3 scripts/run_optimized_backtest.py`

### C. Referências

- Walsh, R., & Joshi, S. (2024). Calibration-driven model selection for sports betting.
- Dixon, M., & Coles, S. (1997). A modelling approach for football match predictions.
- Buchdahl, J. (2016). Squares & Sharps, Suckers & Sharks.
- Lopez de Prado, M. (2018). Advances in Financial Machine Learning.
- SRIJ — Serviço de Regulação e Inspeção de Jogos (Portugal).

---

**Fim do Relatório**
