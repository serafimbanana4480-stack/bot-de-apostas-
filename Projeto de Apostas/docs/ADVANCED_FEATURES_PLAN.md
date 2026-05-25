# VBQ-UNIFIED — Plano de Implementação: Funcionalidades Avançadas

> **Data**: 2026-05-20
> **Base**: Projeto de Apostas/ (VBQ-UNIFIED v4.0)
> **Princípio**: Zero-cost mode, CLV obrigatório, walk-forward, sem leakage

---

## Resumo Executivo

Das 9 funcionalidades propostas, **7 já têm código implementado** (esqueleto funcional),
1 é um stub (MarketSimulator) e 1 foi **excluída** (TimeGAN — ver justificação abaixo).

O bottleneck actual **não é escassez de dados** (3+ épocas de NBA, futebol, UFC + odds reais),
mas sim a **integração dos módulos avançados no pipeline de execução** e a **validação com CLV real**.

### Decisão: TimeGAN excluída

- Dados históricos suficientes para treino sem augmentation
- TimeGAN exige centenas de milhares de ticks para treino realista
- Risco de overfitting a dados sintéticos sem validação rigorosa
- Versão NumPy leve não captura dinâmica temporal não-linear
- As outras 8 funcionalidades têm ROI muito superior
- Se futuramente houver necessidade, reavaliar com PyTorch + GPU

---

## Estado Actual por Módulo

| # | Funcionalidade | Ficheiro | Estado | Prioridade |
|---|---|---|---|---|
| 1 | PPO Agent (RL) | `src/ml/rl/ppo_agent.py` (~729 linhas) | **Implementado, sem integração** | P2 |
| 2 | MAML (Meta-learning) | `src/ml/meta/maml.py` (~360 linhas) | **Implementado, sem integração** | P3 |
| 3 | LLM News | `src/ingestion/llm_news.py` (~531 linhas) | **Implementado, sem collector** | P1 |
| 4 | Order Book Sim | `src/simulations/market_simulator.py` (~45 linhas) | **Stub** | P2 |
| 5 | LinUCB Bandit | `src/ml/ensemble/contextual_bandit.py` (~284 linhas) | **Funcional** | P1 |
| 6 | Bandit Pipeline | `src/ml/ensemble/bandit_pipeline.py` (~498 linhas) | **Funcional** | P1 |
| 7 | Polymarket | `src/execution/adapters/polymarket.py` (~366 linhas) | **Semi-funcional** | P4 |
| 8 | Federated Learning | `src/ml/federated/fed_server.py` (~277 linhas) | **Funcional** | P5 |
| 9 | Counterfactual | `src/explainability/counterfactual.py` (~397 linhas) | **Funcional** | P1 |

---

## Fase 1: Quick Wins (2-4 semanas)

**Objectivo**: Integrar os módulos já funcionais no PipelineOrchestrator e validar CLV.

### 1.1 — Ensemble Dinâmico com Bandit no Orchestrator

**Problema actual**: O `PipelineOrchestrator` usa `RegimeClassifier` + blending fixo (70/30).
Não adapta pesos com base em CLV realizado.

**Solução**: Substituir blending fixo por `BanditEnsemblePipeline`.

```python
# ANTES (orchestrator.py linha ~93-104):
regime = self.regime_classifier.predict(ctx)
specialist = self.regime_classifier.get_specialist_model(regime)
# blending fixo 70/30

# DEPOIS:
regime = self.regime_classifier.predict(ctx)
context = self.bandit_pipeline.build_context(
    event_features=opp_features,
    regime=regime.value,
    liquidity=opp.get("liquidity", 0.5),
    volatility=opp.get("volatility", 0.1),
    time_to_kickoff=opp.get("hours_to_kickoff", 6),
)
model_name, prediction, weights = self.bandit_pipeline.predict(features, context)
```

**Arquivo a modificar**: `src/pipeline/orchestrator.py`

**Dependências**: Nenhuma nova (BanditEnsemblePipeline já importa LinUCB)

**Validação**:
- `run_clv_report.py` com bandit vs. blending fixo
- Teste: `tests/test_bandit_integration.py` (novo)
- Critério: CLV do bandit >= CLV do blending fixo em walk-forward

**Risco**: Baixo. Bandit já funcional, integração é "wiring".

---

### 1.2 — Counterfactual no Audit Log

**Problema actual**: O `DecisionAuditLogger` regista a decisão mas não explica
*porquê* uma aposta foi recusada.

**Solução**: Adicionar `CounterfactualExplainer` ao audit flow.

```python
# Em orchestrator.py, após opp = self.strategy.decide(opp, ctx):
if opp.get("decision") not in ("BET_NOW", "BET"):
    cf = self.counterfactual_explainer.explain(
        current_features=opp_to_feature_dict(opp),
        desired_outcome=True,
        method="search",
    )
    opp["counterfactual"] = {
        "summary": cf.summary,
        "top_features": cf.top_features,
        "distance": cf.distance,
    }
```

**Arquivos a modificar**:
- `src/pipeline/orchestrator.py` — adicionar explainer
- `src/decision_engine/audit_logger.py` — incluir campo counterfactual

**Dependências**: `shap` já em pyproject.toml

**Validação**:
- Teste: `tests/test_counterfactual_integration.py` (novo)
- Verificar que cada decisão NO_BET tem explicação contrafactual

---

### 1.3 — LLM News: Adicionar RSS/Reddit Collector

**Problema actual**: `NewsFeatureExtractor` funciona mas não tem fonte de dados.
Precisa de um collector que traga headlines.

**Solução**: Criar `src/ingestion/news_collector.py` com:
- RSS feeds (ESPN, BBC Sport, The Athletic)
- Reddit (r/nba, r/soccer, r/MMA) via PRAW (gratuito)
- Cache local em Parquet para não repetir chamadas LLM

```python
class NewsCollector:
    """Collects sports headlines from free sources for LLM analysis."""

    def __init__(self, sports: List[str] = None, cache_dir: str = "data/news"):
        self.rss_feeds = {
            "football": ["https://www.espn.com/espn/rss/soccer/news",
                         "https://www.bbc.co.uk/sport/football/rss.xml"],
            "nba": ["https://www.espn.com/espn/rss/nba/news"],
            "mma": ["https://www.espn.com/espn/rss/mma/news"],
        }
        self.reddit_subs = {
            "nba": ["nba"],
            "football": ["soccer"],
            "mma": ["MMA"],
        }

    def collect(self, sport: str, max_items: int = 20) -> List[HeadlineItem]:
        """Collect headlines from RSS + Reddit for a sport."""
        ...

    def deduplicate(self, items: List[HeadlineItem]) -> List[HeadlineItem]:
        """Remove duplicates by URL hash."""
        ...
```

**Dependências novas**: `feedparser`, `praw` (ambas gratuitas)

**Validação**:
- Teste: `tests/test_news_collector.py` (novo)
- Integrar no `ingest_free_data.py` como step opcional
- Verificar que features LLM são ingeridas no FeaturePipeline

---

## Fase 2: Order Book + Slippage (4-6 semanas)

**Objectivo**: Simulação de mercado realista para treino do PPO e backtesting honesto.

### 2.1 — Order Book Simulado

**Problema actual**: `MarketSimulator` é apenas um random walk (45 linhas).
Não modela profundidade, slippage, nem impacto da própria aposta.

**Solução**: Expandir `src/simulations/market_simulator.py` com:

```python
@dataclass
class OrderBookLevel:
    price: float      # Decimal odds
    volume: float     # Available stake at this level
    side: str         # "back" or "lay"

class OrderBookSimulator:
    """
    Simulated order book with 5 depth levels per side.

    Models:
    - Top 5 back/lay levels with volume
    - Market impact: price_move = alpha * sqrt(stake / available_liquidity)
    - Time-dependent slippage (higher near kickoff)
    - Regime-dependent depth (thin in low-liquidity markets)
    """

    def __init__(self, initial_odds: float, total_liquidity: float = 5000.0,
                 n_levels: int = 5, spread_bps: float = 50):
        ...

    def get_depth(self, side: str) -> List[OrderBookLevel]:
        """Return order book depth for back or lay side."""
        ...

    def simulate_fill(self, stake: float, side: str) -> FillResult:
        """Simulate order execution with slippage across levels."""
        ...

    def market_impact(self, stake: float) -> float:
        """Quadratic market impact model: delta = alpha * (stake/liq)^2."""
        ...
```

**Arquivos a criar/modificar**:
- `src/simulations/order_book.py` (novo)
- `src/simulations/slippage_model.py` (novo)
- `src/simulations/market_simulator.py` (expandir)

**Dependências**: Nenhuma nova (numpy only)

**Validação**:
- Teste: `tests/test_order_book.py` (novo)
- Backtest com slippage vs. sem slippage — verificar que CLV realista diminui
- Calibrar contra dados históricos de profundidade (se disponíveis)

---

### 2.2 — Integração PPO com Order Book

**Problema actual**: `BettingEnv` simula outcomes mas não modela slippage.
O agente PPO não aprende a evitar apostas em mercados illiquid.

**Solução**: Conectar `OrderBookSimulator` ao `BettingEnv`.

```python
# Em ppo_agent.py, BettingEnv.step():
if action_type == BetAction.BET:
    stake_frac = STAKE_FRACTIONS[stake_idx]
    stake = self.bankroll * stake_frac

    # NOVO: Simular fill com slippage
    fill = self.order_book.simulate_fill(stake, side="back")
    effective_odds = fill.avg_fill_price  # Pior que odds pedidas
    actual_stake = fill.filled_volume      # Pode ser parcial

    # Se slippage > threshold, penalizar reward
    slippage_penalty = (fill.slippage_bps / 100) * 0.1
    reward -= slippage_penalty
```

**Arquivo a modificar**: `src/ml/rl/ppo_agent.py`

**Validação**:
- Treinar PPO com vs. sem order book
- Verificar que agente aprende a evitar mercados illiquid
- Comparar CLV do PPO vs. Kelly baseline

---

## Fase 3: PPO no Pipeline (6-8 semanas)

**Objectivo**: PPO como decisão de timing/stake no PipelineOrchestrator.

### 3.1 — PPO Training Script

```python
# scripts/train_rl_agent.py (novo)
"""
Train PPO agent on historical data with order book simulation.

Usage:
    poetry run python scripts/train_rl_agent.py --sport football --steps 100000
"""
```

**Fluxo**:
1. Carregar dados históricos de `data/`
2. Construir `BettingEnv` com `OrderBookSimulator`
3. Treinar PPO por N steps
4. Avaliar contra Kelly baseline
5. Loggar métricas em MLflow
6. Salvar modelo em `models/rl/`

**Dependências**: Nenhuma nova (ppo_agent.py já é numpy-only)

---

### 3.2 — PPO no Orchestrator

**Problema actual**: `PipelineOrchestrator._execute()` usa heurísticas para timing.
Não há aprendizagem de *quando* apostar vs. esperar.

**Solução**: Modo opcional onde PPO decide timing e stake.

```python
# Em orchestrator.py, nova opção:
if self.use_rl_timing:
    state = self._build_rl_state(opp, ctx)
    action_type, stake_idx = self.rl_agent.act(state)
    if action_type == BetAction.BET:
        stake = self.bankroll * STAKE_FRACTIONS[stake_idx]
        opp["decision"] = "BET_NOW"
        opp["recommended_stake"] = stake
    elif action_type == BetAction.WAIT:
        opp["decision"] = "WAIT"
    else:
        opp["decision"] = "NO_BET"
```

**Validação**:
- Walk-forward: PPO vs. heurística actual
- Critério: CLV do PPO > CLV da heurística em pelo menos 2 de 3 desportos
- **Nunca** promover PPO a produção sem CLV > 1% validado

---

## Fase 4: MAML para Novos Desportos (8-12 semanas)

**Objectivo**: Fine-tune rápido para ténis, esports, etc. com 20-30 jogos.

### 4.1 — Preparação de Dados Multi-Sport

**Problema actual**: MAML está implementado mas não tem tarefas (tasks) definidas.
Cada desporto precisa de support/query sets.

**Solução**: Criar `scripts/prepare_meta_tasks.py`:

```python
"""
Prepare meta-learning tasks from existing sport data.

For each sport:
- Split into K episodes (each episode = 1 matchday)
- Support set: first 5-10 matches of season
- Query set: remaining matches

Output: data/meta_tasks/{sport}_tasks.npz
"""
```

**Dependências**: Dados já em `data/` (Parquet)

---

### 4.2 — MAML Training + Adaptation

```python
# scripts/train_meta_model.py (novo)
"""
Meta-train across NBA, Football, UFC.
Then adapt to a new sport with few-shot fine-tuning.

Usage:
    poetry run python scripts/train_meta_model.py --sports nba,football,ufc
    poetry run python scripts/train_meta_model.py --adapt tennis --samples 25
"""
```

**Validação**:
- Comparar MAML adaptado (5 gradient steps, 25 jogos) vs. treino from scratch (200 jogos)
- Critério: MAML atinge mesmo Brier score com 10x menos dados
- Walk-forward no novo desporto

---

## Fase 5: Polymarket + Blockchain (12+ semanas)

**Objectivo**: Execução descentralizada em mercados de previsão.

### 5.1 — Polymarket CLOB Integration

**Problema actual**: `PolymarketAdapter` tem REST API + AMM impact mas
não coloca ordens reais no CLOB.

**Solução**: Implementar `place_bet()` com:
- CLOB API order placement (limit orders)
- Assinatura de transacções com `eth-account`
- Fallback para REST API se web3 indisponível

**Dependências novas**: `web3`, `eth-account`

**Risco**: Alto. Mercados de previsão têm regulamento variado.
Implementar apenas após validação em sandbox.

---

### 5.2 — Federated Learning (Opcional)

**Problema actual**: `FederatedServer` funciona mas não tem clientes.

**Solução**: Criar `FederatedClient` + protocolo de comunicação.

**Dependências novas**: `grpcio` (para comunicação entre clientes)

**Risco**: Muito alto. Só faz sentido com múltiplos utilizadores reais.
**Recomendação**: Adiar até haver pelo menos 3 utilizadores activos.

---

## Dependências e Pré-requisitos

### Dependências novas (por fase)

| Fase | Pacote | Custo | Propósito |
|------|--------|-------|-----------|
| F1 | `feedparser` | 0€ | RSS parsing |
| F1 | `praw` | 0€ | Reddit API (rate-limited gratuito) |
| F2 | — | 0€ | Numpy-only |
| F3 | — | 0€ | PPO já é numpy-only |
| F4 | — | 0€ | MAML já é numpy-only |
| F5 | `web3`, `eth-account` | 0€ | Blockchain (gas costs em POL) |
| F5 | `grpcio` | 0€ | Federated communication |

### Pré-requisitos críticos (bloqueantes)

1. **CLV > 1% validado** — Nenhuma funcionalidade avançada deve ir para produção
   sem CLV positivo em walk-forward com dados reais
2. **LeakageDetector** — Deve correr antes de qualquer treino (já implementado)
3. **WalkForwardValidator** — Nunca random split em odds (já implementado)
4. **pandas** — `ensemble/base.py` importa pandas mas não está instalado.
   Adicionar ao pyproject.toml ou refactoring para numpy

### Pré-requisitos recomendados

- `poetry install` funcional (dependências em pyproject.toml)
- 81+ testes pytest a passar
- `ingest_free_data.py` executado com dados reais (não só mock)

---

## Arquitectura de Integração

### Diagrama de Fluxo (pós-Fase 3)

```
                    ┌─────────────┐
                    │  RSS/Reddit │
                    │  Collector  │
                    └──────┬──────┘
                           │ headlines
                           ▼
                    ┌─────────────┐
                    │ LLM News    │──────┐
                    │ Extractor   │      │ features
                    └──────┬──────┘      │
                           │             ▼
┌──────────┐        ┌──────┴──────┐   ┌──────────────┐
│  Odds    │───────▶│  Feature    │──▶│  Bandit      │
│  Ingest  │        │  Pipeline   │   │  Ensemble    │
└──────────┘        └─────────────┘   │  Pipeline    │
                                       └──────┬───────┘
                                              │ selected model
                                              ▼
                                       ┌──────────────┐
                                       │  PPO Agent   │
                                       │  (timing +   │
                                       │   stake)     │
                                       └──────┬───────┘
                                              │ decision
                                              ▼
                                    ┌─────────────────────┐
                                    │  PipelineOrchestrator│
                                    │  ├─ Counterfactual   │
                                    │  ├─ Audit Log        │
                                    │  └─ Execution        │
                                    └──────────┬───────────┘
                                               │
                              ┌─────────────────┼─────────────────┐
                              ▼                 ▼                 ▼
                        ┌──────────┐     ┌──────────┐     ┌──────────┐
                        │ Betfair  │     │ Pinnacle │     │Polymarket│
                        │ Adapter  │     │ Adapter  │     │ Adapter  │
                        └──────────┘     └──────────┘     └──────────┘
```

### Interfaces Chave

```python
# Interface unificada para decisão de aposta
@dataclass
class BettingDecision:
    action: BetAction           # BET, WAIT, SKIP
    stake_fraction: float       # 0.0 - 0.15
    selected_model: str         # "xgb_v2", "lgbm_v3", etc.
    model_weights: np.ndarray   # Softmax weights do bandit
    counterfactual: Optional[str]  # Explicação se recusada
    confidence: float           # UCB score do bandit
    regime: str                 # "low_vol", "normal", "high_vol"
    slippage_estimate: float    # Do OrderBookSimulator
```

---

## Métricas de Sucesso

| Métrica | Baseline (actual) | Target (pós-implementação) |
|---------|-------------------|---------------------------|
| CLV médio (walk-forward) | ? (validar) | > 1% consistente |
| Bandit vs. blending fixo | N/A | CLV bandit >= blending |
| PPO vs. Kelly | N/A | Sharpe ratio PPO > Kelly |
| MAML few-shot | N/A | Brier <= from-scratch com 10x menos dados |
| Slippage modelado | 0 bps | Realista (10-50 bps em illiquid) |
| Counterfactual coverage | 0% | 100% das apostas recusadas |
| LLM news features | 6 zeros | 6 features com variância > 0 |

---

## Cronograma Estimado

| Fase | Duração | Funcionalidades | Bloqueante? |
|------|---------|-----------------|-------------|
| **F1** | 2-4 sem | Bandit + Counterfactual + LLM Collector | Não |
| **F2** | 4-6 sem | Order Book + Slippage | Não |
| **F3** | 6-8 sem | PPO Training + Integração | F2 completo |
| **F4** | 8-12 sem | MAML Multi-Sport | Dados de 3+ desportos |
| **F5** | 12+ sem | Polymarket + Federated | Regulamentação + utilizadores |

**Nota**: F1 e F2 podem decorrer em paralelo. F3 depende de F2. F4 é independente.
F5 é opcional e depende de factores externos.

---

## Próximos Passos Imediatos

1. **Corrigir `pandas` dependency** — `ensemble/base.py` falha sem pandas
2. **Validar CLV actual** — `run_clv_report.py` com dados reais
3. **Implementar F1.1** — Bandit no orchestrator (quick win de maior impacto)
4. **Implementar F1.2** — Counterfactual no audit (quick win de menor esforço)
5. **Implementar F1.3** — News collector + integração LLM
