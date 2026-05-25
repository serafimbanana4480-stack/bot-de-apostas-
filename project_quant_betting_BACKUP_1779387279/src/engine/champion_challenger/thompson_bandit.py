"""
Thompson Sampling Bandit for Model Routing.

Implements Bayesian multi-armed bandit (Beta-Bernoulli) to route live
predictions between champion and challenger models.  Supports:
* Beta(α, β) posterior per arm.
* Temporal decay factor so recent performance is weighted higher.
* Exploration bonus and exploitation safeguards.
* Auto-promotion when challenger demonstrably outperforms champion.
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------

class ArmId(str, Enum):
    """Identifies a bandit arm."""
    CHAMPION = "champion"
    CHALLENGER = "challenger"


class SelectionReason(str, Enum):
    """Why a particular arm was selected."""
    THOMPSON_SAMPLE = "thompson_sample"
    EXPLORATION_BONUS = "exploration_bonus"
    FORCED_CHAMPION = "forced_champion"
    FORCED_CHALLENGER = "forced_challenger"


class ArmSelection(BaseModel):
    """Result of an arm-selection call."""
    selected: ArmId
    reason: SelectionReason
    champion_sample: float = Field(description="Thompson sample drawn for champion.")
    challenger_sample: float = Field(description="Thompson sample drawn for challenger.")
    champion_posterior: tuple[float, float] = Field(description="(α, β) for champion.")
    challenger_posterior: tuple[float, float] = Field(description="(α, β) for challenger.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PromotionVerdict(BaseModel):
    """Whether the challenger should be promoted to champion."""
    should_promote: bool
    challenger_win_probability: float = Field(description="P(challenger > champion).")
    champion_mean: float
    challenger_mean: float
    total_trials_champion: int
    total_trials_challenger: int
    reason: str


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class ThompsonConfig:
    """Tunable parameters for the Thompson bandit."""
    # Priors (weakly informative)
    prior_alpha: float = 1.0
    prior_beta: float = 1.0

    # Temporal decay: effective counts multiplied by γ^(age_in_days)
    decay_factor: float = 0.98                  # daily multiplicative decay
    min_effective_count: float = 1.0             # floor after decay

    # Exploration
    min_trials_before_exploit: int = 30          # force exploration until N trials each
    exploration_probability: float = 0.10        # ε-greedy exploration overlay

    # Promotion
    promotion_threshold: float = 0.95            # P(chall > champ) to auto-promote
    min_trials_for_promotion: int = 100          # need ≥ N challenger trials

    # Random seed for reproducibility (None → random)
    seed: int | None = None


# ---------------------------------------------------------------------------
# Arm state
# ---------------------------------------------------------------------------

@dataclass
class _ArmState:
    """Mutable state for one bandit arm."""
    arm_id: ArmId
    alpha: float
    beta_param: float   # avoid shadowing builtin `beta`
    total_successes: int = 0
    total_failures: int = 0
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_trials(self) -> int:
        return self.total_successes + self.total_failures

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta_param)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ThompsonBandit:
    """Bayesian Thompson Sampling bandit for champion / challenger routing.

    Usage::

        bandit = ThompsonBandit()
        selection = bandit.select_arm()
        # ... run prediction with selected model, observe outcome ...
        bandit.update(selection.selected, success=True)
        verdict = bandit.evaluate_promotion()

    Args:
        config: Tunable parameters.
    """

    def __init__(self, config: ThompsonConfig | None = None) -> None:
        self.config = config or ThompsonConfig()
        self._rng = random.Random(self.config.seed)

        self._arms: dict[ArmId, _ArmState] = {
            ArmId.CHAMPION: _ArmState(
                arm_id=ArmId.CHAMPION,
                alpha=self.config.prior_alpha,
                beta_param=self.config.prior_beta,
            ),
            ArmId.CHALLENGER: _ArmState(
                arm_id=ArmId.CHALLENGER,
                alpha=self.config.prior_alpha,
                beta_param=self.config.prior_beta,
            ),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_arm(self) -> ArmSelection:
        """Select which model to use for the next prediction.

        Returns:
            ``ArmSelection`` with the chosen arm and audit fields.
        """
        champ = self._arms[ArmId.CHAMPION]
        chall = self._arms[ArmId.CHALLENGER]
        cfg = self.config

        # Apply temporal decay before sampling
        self._apply_decay(champ)
        self._apply_decay(chall)

        # Force exploration phase
        if champ.total_trials < cfg.min_trials_before_exploit:
            return self._build_selection(ArmId.CHAMPION, SelectionReason.FORCED_CHAMPION, 0.0, 0.0)
        if chall.total_trials < cfg.min_trials_before_exploit:
            return self._build_selection(ArmId.CHALLENGER, SelectionReason.FORCED_CHALLENGER, 0.0, 0.0)

        # ε-greedy exploration overlay
        if self._rng.random() < cfg.exploration_probability:
            chosen = self._rng.choice([ArmId.CHAMPION, ArmId.CHALLENGER])
            return self._build_selection(chosen, SelectionReason.EXPLORATION_BONUS, 0.0, 0.0)

        # Thompson sampling
        sample_champ = self._rng.betavariate(champ.alpha, champ.beta_param)
        sample_chall = self._rng.betavariate(chall.alpha, chall.beta_param)

        chosen = ArmId.CHAMPION if sample_champ >= sample_chall else ArmId.CHALLENGER
        return self._build_selection(chosen, SelectionReason.THOMPSON_SAMPLE, sample_champ, sample_chall)

    def update(self, arm_id: ArmId | str, success: bool) -> None:
        """Record an observation for the given arm.

        Args:
            arm_id: Which arm produced the prediction.
            success: Whether the prediction was correct / profitable.
        """
        arm_id = ArmId(arm_id) if isinstance(arm_id, str) else arm_id
        arm = self._arms[arm_id]

        if success:
            arm.alpha += 1.0
            arm.total_successes += 1
        else:
            arm.beta_param += 1.0
            arm.total_failures += 1

        arm.last_update = datetime.now(timezone.utc)
        logger.debug(
            "Updated %s: α=%.1f β=%.1f (success=%s)",
            arm_id.value, arm.alpha, arm.beta_param, success,
        )

    def evaluate_promotion(self) -> PromotionVerdict:
        """Evaluate whether the challenger should be promoted to champion.

        Uses Monte-Carlo posterior sampling to estimate
        ``P(challenger_mean > champion_mean)``.

        Returns:
            ``PromotionVerdict`` with promotion recommendation.
        """
        champ = self._arms[ArmId.CHAMPION]
        chall = self._arms[ArmId.CHALLENGER]
        cfg = self.config

        if chall.total_trials < cfg.min_trials_for_promotion:
            return PromotionVerdict(
                should_promote=False,
                challenger_win_probability=0.0,
                champion_mean=champ.mean,
                challenger_mean=chall.mean,
                total_trials_champion=champ.total_trials,
                total_trials_challenger=chall.total_trials,
                reason=f"Insufficient challenger trials ({chall.total_trials} < {cfg.min_trials_for_promotion}).",
            )

        # Monte Carlo: draw 10 000 samples and compute win rate
        n_mc = 10_000
        wins = 0
        for _ in range(n_mc):
            s_champ = self._rng.betavariate(champ.alpha, champ.beta_param)
            s_chall = self._rng.betavariate(chall.alpha, chall.beta_param)
            if s_chall > s_champ:
                wins += 1

        p_win = wins / n_mc
        should = p_win >= cfg.promotion_threshold

        reason = (
            f"P(challenger > champion) = {p_win:.4f} "
            f"{'≥' if should else '<'} threshold {cfg.promotion_threshold:.4f}."
        )

        return PromotionVerdict(
            should_promote=should,
            challenger_win_probability=p_win,
            champion_mean=champ.mean,
            challenger_mean=chall.mean,
            total_trials_champion=champ.total_trials,
            total_trials_challenger=chall.total_trials,
            reason=reason,
        )

    def get_arm_stats(self) -> dict[str, dict[str, float | int]]:
        """Return current posterior statistics for both arms."""
        result = {}
        for arm_id, arm in self._arms.items():
            result[arm_id.value] = {
                "alpha": arm.alpha,
                "beta": arm.beta_param,
                "mean": arm.mean,
                "total_trials": arm.total_trials,
                "successes": arm.total_successes,
                "failures": arm.total_failures,
            }
        return result

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _apply_decay(self, arm: _ArmState) -> None:
        """Decay effective counts so recent outcomes weigh more."""
        now = datetime.now(timezone.utc)
        days_since = (now - arm.last_update).total_seconds() / 86_400.0
        if days_since <= 0:
            return

        gamma_factor = self.config.decay_factor ** days_since
        floor = self.config.min_effective_count

        arm.alpha = max(arm.alpha * gamma_factor, floor)
        arm.beta_param = max(arm.beta_param * gamma_factor, floor)
        arm.last_update = now

    def _build_selection(
        self,
        chosen: ArmId,
        reason: SelectionReason,
        sample_champ: float,
        sample_chall: float,
    ) -> ArmSelection:
        champ = self._arms[ArmId.CHAMPION]
        chall = self._arms[ArmId.CHALLENGER]
        return ArmSelection(
            selected=chosen,
            reason=reason,
            champion_sample=sample_champ,
            challenger_sample=sample_chall,
            champion_posterior=(champ.alpha, champ.beta_param),
            challenger_posterior=(chall.alpha, chall.beta_param),
        )
