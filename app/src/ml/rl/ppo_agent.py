"""
PPO (Proximal Policy Optimization) agent for betting timing and stake sizing.

State: event features, model probability, current odds, odds movement history, bankroll.
Action: (BET, WAIT, SKIP) × stake fraction of bankroll.
Reward: CLV change / volatility (risk-adjusted).

Trains on a simulated market environment that replays historical odds
with realistic slippage and fill simulation.

Usage:
    from src.ml.rl.ppo_agent import PPOBettingAgent, BettingEnv

    env = BettingEnv(historical_df, model_predict_fn)
    agent = PPOBettingAgent(state_dim=env.state_dim, action_dim=env.action_dim)
    agent.train(env, n_steps=50_000)
    action = agent.act(state)  # (action_type, stake_frac)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger("ppo_agent")

# ---------------------------------------------------------------------------
# Action space definition
# ---------------------------------------------------------------------------
class BetAction(IntEnum):
    BET = 0   # Place bet now
    WAIT = 1  # Wait for better odds
    SKIP = 2  # Skip this opportunity

# Stake fractions (discretised for PPO)
STAKE_FRACTIONS = np.array([0.005, 0.01, 0.02, 0.04, 0.06, 0.08, 0.10, 0.15])


@dataclass
class Transition:
    """Single environment transition."""
    state: np.ndarray
    action_type: int
    action_stake_idx: int
    log_prob_type: float
    log_prob_stake: float
    reward: float
    next_state: np.ndarray
    done: bool
    value: float = 0.0
    advantage: float = 0.0


# ---------------------------------------------------------------------------
# Betting Environment (Gym-like)
# ---------------------------------------------------------------------------
class BettingEnv:
    """
    Simulated betting environment that replays historical odds data.

    For each event:
    1. Agent observes state (features, odds, bankroll, etc.)
    2. Agent chooses action: (BET/WAIT/SKIP) + stake fraction
    3. Environment simulates outcome and returns reward

    Reward = CLV_change / volatility (risk-adjusted CLV improvement).
    """

    def __init__(
        self,
        historical_df: Any,
        model_predict_fn: Optional[Callable] = None,
        commission_rate: float = 0.05,
        initial_bankroll: float = 1000.0,
        max_steps_per_episode: int = 200,
        min_edge: float = 0.03,
        clv_weight: float = 0.7,
        roi_weight: float = 0.3,
        use_order_book: bool = True,
        slippage_penalty_weight: float = 0.1,
    ):
        self.historical_df = historical_df
        self.model_predict_fn = model_predict_fn
        self.commission_rate = commission_rate
        self.initial_bankroll = initial_bankroll
        self.max_steps = max_steps_per_episode
        self.min_edge = min_edge
        self.clv_weight = clv_weight
        self.roi_weight = roi_weight
        self.use_order_book = use_order_book
        self.slippage_penalty_weight = slippage_penalty_weight

        # State dimensions
        self.state_dim = 20  # event features + model prob + odds + bankroll + history
        self.action_dim_type = 3  # BET, WAIT, SKIP
        self.action_dim_stake = len(STAKE_FRACTIONS)

        self._reset()

    def _reset(self) -> None:
        """Reset episode state."""
        self.bankroll = self.initial_bankroll
        self.step_count = 0
        self.current_idx = 0
        self.returns_history: List[float] = []
        self.clv_history: List[float] = []
        self.odds_movement_buffer: List[float] = [0.0] * 5

    def reset(self) -> np.ndarray:
        """Start a new episode."""
        self._reset()
        start_idx = np.random.randint(0, max(1, len(self.historical_df) - self.max_steps))
        self.current_idx = start_idx
        return self._get_state()

    def _get_state(self) -> np.ndarray:
        """Build state vector for current event."""
        if self.current_idx >= len(self.historical_df):
            return np.zeros(self.state_dim)

        row = self.historical_df.iloc[self.current_idx]

        # Extract features (normalized)
        features = np.zeros(self.state_dim)
        idx = 0

        # Model probability (if available)
        if self.model_predict_fn is not None:
            try:
                prob = self.model_predict_fn(row)
                features[idx] = np.clip(prob, 0, 1)
            except Exception:
                features[idx] = 0.5
        idx += 1

        # Opening odds
        features[idx] = np.clip(row.get("odd_1", 2.0) / 10.0, 0, 1)
        idx += 1

        # Closing odds (if available)
        features[idx] = np.clip(row.get("closing_odd", 2.0) / 10.0, 0, 1)
        idx += 1

        # Implied probability
        odd_1 = row.get("odd_1", 2.0)
        features[idx] = np.clip(1.0 / odd_1 if odd_1 > 0 else 0.5, 0, 1)
        idx += 1

        # Edge (model prob - implied prob)
        features[idx] = np.clip(features[0] - features[3], -1, 1)
        idx += 1

        # Line movement
        features[idx] = np.clip(row.get("line_movement_home", 0.0), -1, 1)
        idx += 1

        # Odds movement history (last 5)
        for m in self.odds_movement_buffer[:5]:
            features[idx] = np.clip(m, -1, 1)
            idx += 1

        # Bankroll (normalized)
        features[idx] = np.clip(self.bankroll / (2 * self.initial_bankroll), 0, 1)
        idx += 1

        # Recent CLV average
        if self.clv_history:
            features[idx] = np.clip(np.mean(self.clv_history[-20:]) / 10.0, -1, 1)
        idx += 1

        # Recent volatility
        if len(self.returns_history) > 5:
            features[idx] = np.clip(np.std(self.returns_history[-20:]) * 10, 0, 1)
        idx += 1

        # Time decay (position in episode)
        features[idx] = np.clip(self.step_count / self.max_steps, 0, 1)
        idx += 1

        # Win rate recent
        if self.returns_history:
            recent = self.returns_history[-20:]
            features[idx] = np.clip(sum(1 for r in recent if r > 0) / max(len(recent), 1), 0, 1)
        idx += 1

        # Fill remaining with zeros
        return features

    def step(
        self, action_type: int, stake_idx: int
    ) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        Execute one step in the environment.

        Args:
            action_type: 0=BET, 1=WAIT, 2=SKIP
            stake_idx: Index into STAKE_FRACTIONS

        Returns:
            (next_state, reward, done, info)
        """
        if self.current_idx >= len(self.historical_df):
            return np.zeros(self.state_dim), 0.0, True, {}

        row = self.historical_df.iloc[self.current_idx]
        done = False
        info: Dict[str, Any] = {"action": BetAction(action_type).name}

        if action_type == BetAction.SKIP:
            reward = 0.0
            info["reason"] = "Skipped"

        elif action_type == BetAction.WAIT:
            # Small negative reward for waiting (opportunity cost)
            reward = -0.001
            info["reason"] = "Waited"

        elif action_type == BetAction.BET:
            stake_frac = STAKE_FRACTIONS[stake_idx]
            stake = self.bankroll * stake_frac
            odd_1 = row.get("odd_1", 2.0)
            closing_odd = row.get("closing_odd", odd_1)

            # --- Order book simulation with slippage ---
            effective_odds = odd_1
            slippage_bps = 0.0
            actual_stake = stake

            if self.use_order_book:
                try:
                    from src.simulations.order_book import OrderBookSimulator
                    from src.simulations.slippage_model import SlippageModel

                    # Build order book for this event
                    liquidity = float(row.get("liquidity_usd", 5000))
                    ob = OrderBookSimulator(
                        initial_odds=odd_1,
                        total_liquidity=liquidity,
                        n_levels=5,
                    )
                    fill = ob.simulate_fill(
                        stake=stake,
                        side="back",
                        hours_to_kickoff=float(row.get("hours_to_kickoff", 6)),
                        regime_volatility=0.1,
                    )
                    effective_odds = fill.avg_fill_price
                    slippage_bps = fill.slippage_bps
                    actual_stake = fill.filled_stake

                    # If partial fill, reduce stake proportionally
                    if fill.partial_fill:
                        stake = actual_stake

                except ImportError:
                    logger.debug("Order book simulation unavailable, using simple model")

            # Compute edge (using effective odds after slippage)
            implied_prob = 1.0 / effective_odds if effective_odds > 0 else 0.5
            model_prob = self._get_state()[0] if self._get_state() is not None else 0.5
            edge = model_prob - implied_prob

            # Simulate outcome (using effective odds after slippage)
            actual_outcome = str(row.get("actual_outcome", "X"))
            won = actual_outcome == "1"

            # CLV reward (using effective odds)
            clv = (np.log(closing_odd) - np.log(effective_odds)) if effective_odds > 0 and closing_odd > 0 else 0.0
            clv_pct = clv * 100

            # ROI reward (using effective odds)
            if won:
                pnl = stake * (effective_odds - 1) * (1 - self.commission_rate)
            else:
                pnl = -stake

            roi = pnl / self.bankroll if self.bankroll > 0 else 0.0

            # Combined reward: CLV-weighted + ROI-weighted, risk-adjusted
            vol = np.std(self.returns_history[-20:]) if len(self.returns_history) > 5 else 0.01
            risk_adj = 1.0 / (1.0 + vol * 10)

            reward = (self.clv_weight * clv_pct + self.roi_weight * roi * 100) * risk_adj

            # Penalty for betting with negative edge
            if edge < self.min_edge:
                reward -= 0.5

            # Slippage penalty: discourage betting in illiquid markets
            if self.use_order_book and slippage_bps > 0:
                reward -= self.slippage_penalty_weight * (slippage_bps / 100.0)

            # Update bankroll
            self.bankroll += pnl
            self.returns_history.append(roi)
            self.clv_history.append(clv_pct)

            info.update({
                "reason": "Bet placed",
                "stake": round(stake, 2),
                "won": won,
                "pnl": round(pnl, 2),
                "clv": round(clv_pct, 2),
                "edge": round(edge, 4),
            })

            # Episode ends if bankroll drops below 10%
            if self.bankroll < self.initial_bankroll * 0.1:
                done = True
                reward -= 5.0  # Severe penalty for ruin

        # Update odds movement buffer
        line_move = row.get("line_movement_home", 0.0)
        self.odds_movement_buffer.append(line_move)
        self.odds_movement_buffer = self.odds_movement_buffer[-5:]

        self.step_count += 1
        self.current_idx += 1

        if self.step_count >= self.max_steps:
            done = True

        next_state = self._get_state()
        return next_state, reward, done, info


# ---------------------------------------------------------------------------
# PPO Neural Network (pure NumPy — no PyTorch dependency required)
# ---------------------------------------------------------------------------
class _PolicyNetwork:
    """
    Simple 2-layer neural network for policy and value functions.
    Implemented in pure NumPy for zero-dependency operation.
    Supports optional PyTorch backend if available.
    """

    def __init__(
        self,
        state_dim: int,
        action_dim_type: int,
        action_dim_stake: int,
        hidden_dim: int = 64,
        lr: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        entropy_coef: float = 0.01,
        value_coef: float = 0.5,
    ):
        self.state_dim = state_dim
        self.action_dim_type = action_dim_type
        self.action_dim_stake = action_dim_stake
        self.hidden_dim = hidden_dim
        self.lr = lr
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.entropy_coef = entropy_coef
        self.value_coef = value_coef

        # Xavier initialization
        scale1 = np.sqrt(2.0 / (state_dim + hidden_dim))
        scale2 = np.sqrt(2.0 / (hidden_dim + hidden_dim))

        # Shared feature extractor
        self.W1 = np.random.randn(state_dim, hidden_dim) * scale1
        self.b1 = np.zeros(hidden_dim)

        # Policy head (action type)
        self.W_type = np.random.randn(hidden_dim, action_dim_type) * scale2
        self.b_type = np.zeros(action_dim_type)

        # Policy head (stake fraction)
        self.W_stake = np.random.randn(hidden_dim, action_dim_stake) * scale2
        self.b_stake = np.zeros(action_dim_stake)

        # Value head
        self.W_value = np.random.randn(hidden_dim, 1) * scale2
        self.b_value = np.zeros(1)

    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        e = np.exp(x - np.max(x))
        return e / (e.sum() + 1e-10)

    def forward(self, state: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        """
        Forward pass.

        Returns:
            (action_type_probs, stake_probs, value, hidden)
        """
        h = self._relu(state @ self.W1 + self.b1)

        type_logits = h @ self.W_type + self.b_type
        stake_logits = h @ self.W_stake + self.b_stake

        type_probs = self._softmax(type_logits)
        stake_probs = self._softmax(stake_logits)

        value = float((h @ self.W_value + self.b_value)[0])

        return type_probs, stake_probs, value, h

    def act(self, state: np.ndarray) -> Tuple[int, int, float, float]:
        """
        Sample action from policy.

        Returns:
            (action_type, stake_idx, log_prob_type, log_prob_stake)
        """
        type_probs, stake_probs, value, _ = self.forward(state)

        action_type = np.random.choice(len(type_probs), p=type_probs)
        stake_idx = np.random.choice(len(stake_probs), p=stake_probs)

        log_prob_type = np.log(type_probs[action_type] + 1e-10)
        log_prob_stake = np.log(stake_probs[stake_idx] + 1e-10)

        return action_type, stake_idx, log_prob_type, log_prob_stake

    def evaluate(
        self, state: np.ndarray, action_type: int, stake_idx: int
    ) -> Tuple[float, float, float, float]:
        """
        Evaluate log probabilities and value for given state-action pair.
        """
        type_probs, stake_probs, value, _ = self.forward(state)

        log_prob_type = np.log(type_probs[action_type] + 1e-10)
        log_prob_stake = np.log(stake_probs[stake_idx] + 1e-10)

        # Entropy for exploration bonus
        type_entropy = -np.sum(type_probs * np.log(type_probs + 1e-10))
        stake_entropy = -np.sum(stake_probs * np.log(stake_probs + 1e-10))

        return log_prob_type, log_prob_stake, value, type_entropy + stake_entropy


# ---------------------------------------------------------------------------
# PPO Agent
# ---------------------------------------------------------------------------
class PPOBettingAgent:
    """
    PPO agent for betting timing and stake sizing.

    Learns a policy that maps (event features, model prob, odds, bankroll)
    to (BET/WAIT/SKIP, stake_fraction) with risk-adjusted CLV reward.

    Training:
        agent = PPOBettingAgent(state_dim=20, action_dim_type=3, action_dim_stake=8)
        agent.train(env, n_steps=50_000)

    Inference:
        action_type, stake_frac = agent.act(state)
    """

    def __init__(
        self,
        state_dim: int = 20,
        action_dim_type: int = 3,
        action_dim_stake: int = 8,
        hidden_dim: int = 64,
        lr: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        entropy_coef: float = 0.01,
        value_coef: float = 0.5,
        n_epochs_per_update: int = 4,
        batch_size: int = 64,
        rollout_length: int = 2048,
    ):
        self.state_dim = state_dim
        self.action_dim_type = action_dim_type
        self.action_dim_stake = action_dim_stake
        self.n_epochs = n_epochs_per_update
        self.batch_size = batch_size
        self.rollout_length = rollout_length

        self.network = _PolicyNetwork(
            state_dim=state_dim,
            action_dim_type=action_dim_type,
            action_dim_stake=action_dim_stake,
            hidden_dim=hidden_dim,
            lr=lr,
            gamma=gamma,
            gae_lambda=gae_lambda,
            clip_epsilon=clip_epsilon,
            entropy_coef=entropy_coef,
            value_coef=value_coef,
        )

        self._training_history: List[Dict[str, float]] = []

    def act(self, state: np.ndarray, deterministic: bool = False) -> Tuple[int, float]:
        """
        Select action for given state.

        Args:
            state: State vector (shape: state_dim,)
            deterministic: If True, pick argmax instead of sampling

        Returns:
            (action_type, stake_idx)
        """
        state = np.array(state).flatten()
        if len(state) < self.state_dim:
            state = np.pad(state, (0, self.state_dim - len(state)))
        else:
            state = state[:self.state_dim]

        if deterministic:
            type_probs, stake_probs, _, _ = self.network.forward(state)
            action_type = int(np.argmax(type_probs))
            stake_idx = int(np.argmax(stake_probs))
        else:
            action_type, stake_idx, _, _ = self.network.act(state)

        return action_type, stake_idx

    def train(
        self,
        env: BettingEnv,
        n_steps: int = 50_000,
        eval_every: int = 5_000,
        eval_episodes: int = 5,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """
        Train the PPO agent on the betting environment.

        Args:
            env: BettingEnv instance
            n_steps: Total training steps
            eval_every: Evaluate every N steps
            eval_episodes: Episodes per evaluation
            verbose: Log progress

        Returns:
            Training summary with rewards and metrics
        """
        total_updates = 0
        best_eval_reward = -np.inf
        state = env.reset()

        for step in range(0, n_steps, self.rollout_length):
            # Collect rollout
            transitions = self._collect_rollout(env, state)

            if not transitions:
                state = env.reset()
                continue

            # Compute advantages (GAE)
            self._compute_advantages(transitions)

            # PPO update
            for epoch in range(self.n_epochs):
                self._ppo_update(transitions)

            total_updates += 1

            # Periodic evaluation
            if total_updates % max(1, eval_every // self.rollout_length) == 0:
                eval_reward = self._evaluate(env, eval_episodes)
                if eval_reward > best_eval_reward:
                    best_eval_reward = eval_reward

                if verbose:
                    avg_reward = np.mean([t.reward for t in transitions[-100:]])
                    logger.info(
                        "Step %d/%d | Avg reward: %.4f | Eval: %.4f | Best: %.4f",
                        step + self.rollout_length, n_steps,
                        avg_reward, eval_reward, best_eval_reward,
                    )

                self._training_history.append({
                    "step": step,
                    "avg_reward": float(np.mean([t.reward for t in transitions[-100:]])),
                    "eval_reward": eval_reward,
                    "best_eval_reward": best_eval_reward,
                })

            # Reset for next rollout
            if transitions[-1].done:
                state = env.reset()
            else:
                state = transitions[-1].next_state

        return {
            "total_steps": n_steps,
            "total_updates": total_updates,
            "best_eval_reward": best_eval_reward,
            "training_history": self._training_history,
        }

    def _collect_rollout(
        self, env: BettingEnv, initial_state: np.ndarray
    ) -> List[Transition]:
        """Collect a rollout of transitions."""
        transitions = []
        state = initial_state

        for _ in range(self.rollout_length):
            action_type, stake_idx, log_prob_type, log_prob_stake = self.network.act(state)
            _, _, value, _ = self.network.forward(state)

            next_state, reward, done, info = env.step(action_type, stake_idx)

            transitions.append(Transition(
                state=state.copy(),
                action_type=action_type,
                action_stake_idx=stake_idx,
                log_prob_type=log_prob_type,
                log_prob_stake=log_prob_stake,
                reward=reward,
                next_state=next_state.copy(),
                done=done,
                value=value,
            ))

            state = next_state
            if done:
                break

        return transitions

    def _compute_advantages(self, transitions: List[Transition]) -> None:
        """Compute GAE advantages for the rollout."""
        net = self.network
        gae = 0.0

        for i in reversed(range(len(transitions))):
            t = transitions[i]

            if t.done:
                next_value = 0.0
            else:
                _, _, next_value, _ = net.forward(t.next_state)

            delta = t.reward + net.gamma * next_value - t.value
            gae = delta + net.gamma * net.gae_lambda * gae
            t.advantage = gae

    def _ppo_update(self, transitions: List[Transition]) -> None:
        """Perform one PPO update epoch."""
        net = self.network
        n = len(transitions)

        # Normalize advantages
        advantages = np.array([t.advantage for t in transitions])
        adv_mean = advantages.mean()
        adv_std = advantages.std() + 1e-8
        norm_advantages = (advantages - adv_mean) / adv_std

        # Mini-batch updates
        indices = np.random.permutation(n)
        for start in range(0, n, self.batch_size):
            batch_idx = indices[start:start + self.batch_size]
            if len(batch_idx) == 0:
                continue

            grad_W1 = np.zeros_like(net.W1)
            grad_b1 = np.zeros_like(net.b1)
            grad_W_type = np.zeros_like(net.W_type)
            grad_b_type = np.zeros_like(net.b_type)
            grad_W_stake = np.zeros_like(net.W_stake)
            grad_b_stake = np.zeros_like(net.b_stake)
            grad_W_value = np.zeros_like(net.W_value)
            grad_b_value = np.zeros_like(net.b_value)

            for i, idx in enumerate(batch_idx):
                t = transitions[idx]
                adv = norm_advantages[idx]

                # Current log probs
                new_log_type, new_log_stake, new_value, entropy = net.evaluate(
                    t.state, t.action_type, t.action_stake_idx
                )

                # PPO ratio
                ratio_type = np.exp(new_log_type - t.log_prob_type)
                ratio_stake = np.exp(new_log_stake - t.log_prob_stake)

                # Clipped surrogate
                clip_type = np.clip(ratio_type, 1 - net.clip_epsilon, 1 + net.clip_epsilon)
                clip_stake = np.clip(ratio_stake, 1 - net.clip_epsilon, 1 + net.clip_epsilon)

                policy_loss_type = -min(ratio_type * adv, clip_type * adv)
                policy_loss_stake = -min(ratio_stake * adv, clip_stake * adv)
                policy_loss = policy_loss_type + policy_loss_stake

                # Value loss
                value_loss = (new_value - t.reward) ** 2

                # Total loss (we minimize, so negate entropy bonus)
                total_loss = policy_loss + net.value_coef * value_loss - net.entropy_coef * entropy

                # Backprop (manual gradients for 2-layer net)
                h = net._relu(t.state @ net.W1 + net.b1)

                # Value gradient
                d_value = 2 * (new_value - t.reward)
                grad_W_value += d_value * h.reshape(-1, 1)
                grad_b_value += d_value

                # Policy gradient (simplified — uses advantage direction)
                d_h = np.zeros_like(h)
                if h.max() > 0:  # ReLU mask
                    d_type = -adv * ratio_type * (1 - t.action_type)  # simplified
                    d_stake = -adv * ratio_stake * (1 - t.action_stake_idx)

                    grad_W_type += d_type * h.reshape(-1, 1)
                    grad_b_type += d_type
                    grad_W_stake += d_stake * h.reshape(-1, 1)
                    grad_b_stake += d_stake

                    d_h += (d_type * net.W_type.T[0] + d_stake * net.W_stake.T[0])

                # Hidden layer gradient
                relu_mask = (h > 0).astype(float)
                grad_W1 += np.outer(t.state, d_h * relu_mask)
                grad_b1 += d_h * relu_mask

            # Apply gradients (averaged over batch)
            bs = len(batch_idx)
            net.W1 -= net.lr * grad_W1 / bs
            net.b1 -= net.lr * grad_b1 / bs
            net.W_type -= net.lr * grad_W_type / bs
            net.b_type -= net.lr * grad_b_type / bs
            net.W_stake -= net.lr * grad_W_stake / bs
            net.b_stake -= net.lr * grad_b_stake / bs
            net.W_value -= net.lr * grad_W_value / bs
            net.b_value -= net.lr * grad_b_value / bs

    def _evaluate(self, env: BettingEnv, n_episodes: int) -> float:
        """Evaluate agent without exploration noise."""
        total_rewards = []
        for _ in range(n_episodes):
            state = env.reset()
            episode_reward = 0.0
            done = False
            while not done:
                action_type, stake_frac = self.act(state, deterministic=True)
                stake_idx = int(np.argmin(np.abs(STAKE_FRACTIONS - stake_frac)))
                state, reward, done, _ = env.step(action_type, stake_idx)
                episode_reward += reward
            total_rewards.append(episode_reward)
        return float(np.mean(total_rewards))

    @property
    def status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "state_dim": self.state_dim,
            "action_dim_type": self.action_dim_type,
            "action_dim_stake": self.action_dim_stake,
            "training_steps": len(self._training_history),
            "best_eval_reward": (
                max(h["best_eval_reward"] for h in self._training_history)
                if self._training_history else None
            ),
        }
