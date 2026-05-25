# VBQ-UNIFIED — Architecture Roadmap (Medium & Long Term)

This document describes the architectural vision for features that are
too complex for immediate implementation but are planned for the future.

---

## Medium Term (3-6 months)

### 6. RL Agent for Timing & Stake (PPO)

**Status**: Architecture designed, implementation pending.

**Components needed**:
- `src/ml/rl/betting_env.py` — OpenAI Gym environment
  - State: [model_prob, odds, line_movement, bankroll, hours_to_kickoff, liquidity, regime_onehot]
  - Action: (BET/WAIT/SKIP, stake_fraction) — continuous stake in [0, 0.5]
  - Reward: CLV per bet / volatility (risk-adjusted)
  - Episode: One match day (all matches processed sequentially)
- `src/ml/rl/ppo_agent.py` — PPO with clipped objective
  - Actor-Critic network (shared backbone, separate heads)
  - Input: state vector (dim ~20)
  - Actor output: action probabilities + stake fraction
  - Critic output: value estimate
- `src/ml/rl/train_rl.py` — Training loop
  - Self-play against MarketSimulator
  - Train for 1M steps, evaluate every 100K
  - Compare against Kelly baseline
- Integration: `orchestrator.py` calls `rl_agent.act(state)` instead of heuristics

**Dependencies**: torch, gymnasium (or stable-baselines3)

**Risk**: RL can be unstable; need extensive evaluation before production.

---

### 7. Meta-Learning (MAML) for New Sports

**Status**: Research phase.

**Components needed**:
- `src/ml/meta/maml_trainer.py` — MAML inner/outer loop
  - Inner loop: adapt to a task (sport) with K=5 gradient steps
  - Outer loop: meta-optimize initialization across tasks
  - Tasks: [NBA, Football, UFC] — each is a few-shot learning problem
- `src/ml/meta/base_network.py` — Shared neural backbone
  - Input: [features] (sport-agnostic)
  - Output: probability (regression head)
  - Sport-specific adapter layers (lightweight)
- `src/ml/meta/few_shot.py` — Fine-tune for new sport with 20-30 games
  - Load meta-learned initialization
  - 5 gradient steps on new sport data
  - Evaluate on held-out games

**Dependencies**: torch, higher (for MAML differentiation)

**Risk**: MAML requires careful task design; may not outperform simple transfer learning.

---

### 8. LLM Integration for News Analysis

**Status**: Pipeline designed, API integration pending.

**Components needed**:
- `src/ingestion/llm_news_pipeline.py` — News → Features pipeline
  - Step 1: Collect headlines from RSS/Twitter API
  - Step 2: Filter by sport relevance (keyword + LLM)
  - Step 3: LLM analysis → extract structured data:
    - `injury_severity`: 0-1 score
    - `player_return_probability`: 0-1
    - `emotional_impact`: -1 to +1 (morale boost/loss)
    - `source_reliability`: 0-1
  - Step 4: Merge as features into pipeline
- `src/ingestion/llm_client.py` — LLM API client
  - Support: OpenAI API, local LLaMA (via ollama), or HuggingFace
  - Rate limiting and caching
  - Prompt templates for structured extraction

**Dependencies**: openai or ollama, feedparser, tweepy

**Risk**: LLM hallucinations; need confidence scoring and human review loop.

---

### 9. Order Book Simulation

**Status**: Enhancement to existing MarketSimulator.

**Components needed**:
- `src/simulations/order_book.py` — Simplified order book
  - Top 5 price levels per side (back/lay)
  - Depth at each level (from historical data or synthetic)
  - Market impact model: price_move = α * sqrt(stake / liquidity)
- `src/simulations/slippage_model.py` — Dynamic slippage
  - Base slippage: function of stake / available_liquidity
  - Time-dependent: higher slippage close to kickoff
  - Regime-dependent: higher slippage in low-liquidity markets
- Integration: `historical_simulator.py` uses order book for execution simulation

**Dependencies**: None (pure Python/numpy)

**Risk**: Need historical depth data for calibration; may not be available for all sports.

---

## Long Term (6-12 months)

### 11. GAN/Synthetic Data Generation

**Architecture**:
- `src/ml/generative/time_gan.py` — TimeGAN for odds series generation
  - Generator: LSTM → synthetic odds sequence
  - Discriminator: LSTM → real/fake classification
  - Supervisor: Enforces temporal dynamics
  - Embedder: Maps real data to latent space
- Use: Augment rare regime data (playoffs, injuries)
- Validate: Discriminative score + predictive score

**Dependencies**: torch

---

### 12. Blockchain Betting (Polymarket/Augur)

**Architecture**:
- `src/execution/adapters/polymarket_adapter.py` — web3.py integration
  - Connect to Polygon network
  - Query CLOB (Central Limit Order Book) API
  - Place bets via smart contracts
  - Handle AMM liquidity pools
- `src/execution/adapters/augur_adapter.py` — Augur v2 integration
  - Event creation and market resolution
  - Share token trading

**Dependencies**: web3, eth-account, polygon-client

---

### 13. Federated Learning

**Architecture**:
- `src/ml/federated/server.py` — Aggregation server
  - FedAvg: Average model weights from N clients
  - Secure aggregation: weights encrypted before sending
  - Differential privacy: add noise to gradients
- `src/ml/federated/client.py` — Local training client
  - Train on local data
  - Send only weight updates (not raw data)
- `src/ml/federated/communication.py` — gRPC/REST protocol

**Dependencies**: grpcio, cryptography

---

### 14. Counterfactual Explanations

**Architecture**:
- `src/explainability/counterfactual.py` — Generate counterfactuals
  - For each rejected bet: "What would need to change for this to be accepted?"
  - Compute minimal feature perturbation (using SHAP or LIME)
  - Format as natural language via LLM
  - Example: "If the odds were 2.10 instead of 2.05, the bet would be accepted with stake €5.20"
- `src/explainability/explanation_renderer.py` — Render explanations
  - Console output
  - Telegram message
  - Dashboard panel

**Dependencies**: shap, openai (optional, for NL generation)

---

## Implementation Priority

| Item | Impact | Effort | Priority |
|------|--------|--------|----------|
| 6. RL Agent | High | Very High | P2 (after Tier E validation) |
| 7. MAML | Medium | High | P3 (when adding new sports) |
| 8. LLM News | High | Medium | P1 (next quarter) |
| 9. Order Book | Medium | Medium | P2 (before live trading at scale) |
| 11. GAN | Low-Med | High | P4 (research) |
| 12. Blockchain | Medium | High | P4 (market expansion) |
| 13. Federated | Low | Very High | P5 (if multi-user) |
| 14. Counterfactual | Medium | Low | P1 (quick win) |
