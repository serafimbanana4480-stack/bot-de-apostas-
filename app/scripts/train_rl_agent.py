#!/usr/bin/env python3
"""
Train PPO agent for betting timing and stake sizing.

Uses historical odds data with order book simulation to train
a PPO agent that learns when to bet, wait, or skip, and how
much to stake.

Usage:
    poetry run python scripts/train_rl_agent.py --sport football --steps 50000
    poetry run python scripts/train_rl_agent.py --sport nba --steps 100000 --eval-every 10000
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import settings
from src.data.local_store import LocalDataStore
from src.ml.rl.ppo_agent import BettingEnv, PPOBettingAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("train_rl_agent")


def load_historical_data(sport: str) -> Any:
    """Load historical data for the given sport."""
    store = LocalDataStore(settings.DATA_DIR)
    try:
        df = store.load_parquet(f"{sport}_odds_history")
        if df is not None and len(df) > 0:
            logger.info("Loaded %d rows for %s", len(df), sport)
            return df
    except Exception:
        pass

    # Generate synthetic data if no real data available
    logger.warning("No historical data found for %s — generating synthetic data", sport)
    return generate_synthetic_data(sport, n_rows=5000)


def generate_synthetic_data(sport: str, n_rows: int = 5000) -> Any:
    """Generate synthetic betting data for training when real data is unavailable."""
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas required for synthetic data generation. Install: pip install pandas")
        sys.exit(1)

    rng = np.random.RandomState(42)

    # Generate realistic odds range based on sport
    if sport == "nba":
        odds_range = (1.2, 5.0)
    elif sport == "football":
        odds_range = (1.3, 8.0)
    else:
        odds_range = (1.2, 6.0)

    odd_1 = rng.uniform(odds_range[0], odds_range[1], n_rows)

    # Closing odds: slight regression to mean + noise
    closing_odd = odd_1 * rng.normal(1.0, 0.05, n_rows)
    closing_odd = np.clip(closing_odd, 1.01, 50.0)

    # Outcomes: implied probability + noise
    implied_prob = 1.0 / odd_1
    outcomes = (rng.random(n_rows) < implied_prob * rng.uniform(0.85, 1.15, n_rows)).astype(int)
    outcomes = np.clip(outcomes, 0, 1)

    # Additional features
    liquidity = rng.uniform(500, 20000, n_rows)
    hours_to_kickoff = rng.uniform(0.5, 48, n_rows)
    line_movement = rng.normal(0, 0.03, n_rows)

    df = pd.DataFrame({
        "odd_1": odd_1,
        "closing_odd": closing_odd,
        "actual_outcome": outcomes,
        "liquidity_usd": liquidity,
        "hours_to_kickoff": hours_to_kickoff,
        "line_movement_home": line_movement,
    })

    logger.info("Generated %d synthetic rows for %s", n_rows, sport)
    return df


def train(args: argparse.Namespace) -> None:
    """Main training loop."""
    sport = args.sport
    n_steps = args.steps
    eval_every = args.eval_every
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    df = load_historical_data(sport)

    # Create environment
    env = BettingEnv(
        historical_df=df,
        commission_rate=0.05,
        initial_bankroll=1000.0,
        max_steps_per_episode=200,
        min_edge=0.03,
        clv_weight=0.7,
        roi_weight=0.3,
        use_order_book=True,
        slippage_penalty_weight=0.1,
    )

    # Create agent
    agent = PPOBettingAgent(
        state_dim=env.state_dim,
        action_dim_type=env.action_dim_type,
        action_dim_stake=env.action_dim_stake,
        lr=3e-4,
        gamma=0.99,
        gae_lambda=0.95,
        clip_epsilon=0.2,
        value_coef=0.5,
        entropy_coef=0.01,
    )

    logger.info(
        "Starting PPO training: sport=%s, steps=%d, state_dim=%d",
        sport, n_steps, env.state_dim,
    )

    # Use built-in train method
    summary = agent.train(env, n_steps=n_steps, eval_every=eval_every, verbose=True)

    # Final save
    final_path = save_dir / f"ppo_{sport}_final.npz"
    agent.save(str(final_path))
    logger.info(
        "Training complete: %d steps, best_eval_reward=%.4f, saved to %s",
        summary.get("total_steps", n_steps),
        summary.get("best_eval_reward", 0.0),
        final_path,
    )

    # Log to MLflow if available
    try:
        import mlflow
        mlflow.set_tracking_uri(f"sqlite:///{PROJECT_ROOT / 'mlflow.db'}")
        with mlflow.start_run(run_name=f"ppo_{sport}"):
            mlflow.log_params({
                "sport": sport,
                "n_steps": n_steps,
                "state_dim": env.state_dim,
                "use_order_book": True,
                "clv_weight": 0.7,
                "roi_weight": 0.3,
            })
            mlflow.log_metrics({
                "best_avg_reward": best_avg_reward,
                "total_steps": total_steps,
            })
            mlflow.log_artifact(str(final_path))
            logger.info("Logged to MLflow")
    except ImportError:
        logger.info("MLflow not available — skipping logging")


def main():
    parser = argparse.ArgumentParser(description="Train PPO agent for betting timing/stake")
    parser.add_argument("--sport", type=str, default="football", help="Sport to train on")
    parser.add_argument("--steps", type=int, default=50000, help="Total training steps")
    parser.add_argument("--eval-every", type=int, default=10000, help="Evaluate every N steps")
    parser.add_argument("--save-dir", type=str, default="models/rl", help="Directory to save models")
    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
