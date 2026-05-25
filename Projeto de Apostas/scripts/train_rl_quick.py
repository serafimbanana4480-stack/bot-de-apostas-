#!/usr/bin/env python3
"""Quick RL training test — 500 steps only."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("train_rl_quick")

import numpy as np
from scripts.train_rl_agent import generate_synthetic_data
from src.ml.rl.ppo_agent import BettingEnv, PPOBettingAgent

logger.info("Generating synthetic data...")
df = generate_synthetic_data("football", n_rows=500)

logger.info("Creating environment...")
env = BettingEnv(
    historical_df=df, commission_rate=0.05, initial_bankroll=1000.0,
    max_steps_per_episode=50, min_edge=0.03, clv_weight=0.7, roi_weight=0.3,
    use_order_book=True, slippage_penalty_weight=0.1,
)

logger.info("Creating agent...")
agent = PPOBettingAgent(
    state_dim=env.state_dim,
    action_dim_type=env.action_dim_type,
    action_dim_stake=env.action_dim_stake,
    lr=3e-4, gamma=0.99, gae_lambda=0.95,
    clip_epsilon=0.2, value_coef=0.5, entropy_coef=0.01,
)

logger.info("Starting training: 500 steps")
summary = agent.train(env, n_steps=500, eval_every=250, verbose=True)
logger.info("Training complete: best_eval_reward=%.4f", summary.get("best_eval_reward", 0.0))
