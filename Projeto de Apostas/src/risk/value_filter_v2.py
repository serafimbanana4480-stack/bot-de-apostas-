"""
ValueBetFilterV2 - Filtro profissional baseado em EDGE, não em probabilidade.

O erro fatal do V1 era min_probability=0.60, que eliminava quase todos os
value bets. Em betting profissional, o que importa é:
    edge = modelo_prob - implied_prob

Um value bet pode existir em QUALQUER probabilidade. Odds 5.0 com prob 25%
(implied 20%) tem 5% de edge e é lucrativo.

Referências:
- Walsh & Joshi (2024): calibration-driven ROI +34.69% vs accuracy-driven -35.17%
- Betfair / Pinnacle: closing odds como proxy de true probability
"""
import logging
from typing import Any, Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class ValueBetFilterV2:
    """
    Filtro de value bets profissional.

    Lógica:
    1. Calcular edge = model_prob - implied_prob
    2. Edge deve ser > threshold (ajustado por odds bin)
    3. CLV positivo como confirmação adicional
    4. Sem filtro de probabilidade mínima (eliminado)
    """

    def __init__(
        self,
        min_edge: float = 0.03,        # 3% edge mínimo (conservador)
        min_clv: float = 0.0,          # CLV mínimo (0 = sem filtro de CLV)
        max_odds: float = 10.0,        # Longshots até 10.0 (com edge suficiente)
        min_odds: float = 1.20,        # Evitar odds demasiado baixas
        edge_by_bin: Optional[Dict[str, float]] = None,
        max_edge_cap: float = 0.25,    # Edge > 25% é suspeito (palpable error)
        require_pinnacle: bool = False, # Não exigir Pinnacle (pode não estar disponível)
    ):
        self.min_edge = min_edge
        self.min_clv = min_clv
        self.max_odds = max_odds
        self.min_odds = min_odds
        self.max_edge_cap = max_edge_cap
        self.require_pinnacle = require_pinnacle

        # Edge thresholds por bin de odds
        # Quanto maiores as odds, maior o edge exigido (mais incerteza)
        self.edge_by_bin = edge_by_bin or {
            "favorite": 0.02,    # odds < 2.0
            "mid": 0.03,         # odds 2.0 - 3.5
            "longshot": 0.05,    # odds 3.5 - 7.0
            "extreme": 0.08,     # odds > 7.0
        }

    def _odds_bin(self, odds: float) -> str:
        if odds < 2.0:
            return "favorite"
        if odds < 3.5:
            return "mid"
        if odds < 7.0:
            return "longshot"
        return "extreme"

    def evaluate(self, opportunity: Dict[str, Any]) -> Tuple[bool, Optional[str], Dict[str, float]]:
        """
        Avalia uma oportunidade de aposta.

        Returns: (passed, reason, metrics)
        """
        match_id = opportunity.get("match_id", "unknown")
        event_name = opportunity.get("event_name", "unknown")

        # Extrair probabilidades e odds
        model_prob = opportunity.get("model_prob", 0.0)
        odds = opportunity.get("odds", 1.0)
        pinnacle_odds = opportunity.get("pinnacle_odds")
        clv = opportunity.get("clv_pct", 0.0)

        metrics = {
            "model_prob": model_prob,
            "odds": odds,
            "implied_prob": 0.0,
            "edge": 0.0,
            "expected_value": 0.0,
            "kelly_fraction": 0.0,
        }

        # 0. Validar inputs
        if odds <= 1.0 or model_prob <= 0 or model_prob >= 1:
            return False, "Invalid odds or probability", metrics

        # 1. Calcular implied probability e edge
        implied_prob = 1.0 / odds
        metrics["implied_prob"] = implied_prob

        edge = model_prob - implied_prob
        metrics["edge"] = edge

        # Expected value (%)
        ev = (model_prob * (odds - 1.0)) - (1.0 - model_prob)
        metrics["expected_value"] = ev

        # Kelly fraction (fractional)
        if odds > 1.0 and model_prob > 0:
            kelly = (model_prob * odds - 1.0) / (odds - 1.0)
            metrics["kelly_fraction"] = max(0.0, kelly)

        # 2. Edge cap (evita palpable errors)
        if edge > self.max_edge_cap:
            reason = f"Edge {edge:.1%} exceeds cap {self.max_edge_cap:.1%} — likely palpable error"
            logger.info(f"[{event_name}] Rejected: {reason}")
            return False, reason, metrics

        # 3. Edge mínimo por bin
        bin_key = self._odds_bin(odds)
        min_edge_for_bin = self.edge_by_bin.get(bin_key, self.min_edge)

        if edge < min_edge_for_bin:
            reason = f"Edge {edge:.2%} below bin threshold {min_edge_for_bin:.2%} ({bin_key})"
            logger.info(f"[{event_name}] Rejected: {reason}")
            return False, reason, metrics

        # 4. Odds range
        if odds > self.max_odds:
            reason = f"Odds {odds:.2f} above max {self.max_odds:.2f}"
            return False, reason, metrics
        if odds < self.min_odds:
            reason = f"Odds {odds:.2f} below min {self.min_odds:.2f}"
            return False, reason, metrics

        # 5. CLV check (opcional)
        if clv < self.min_clv:
            reason = f"CLV {clv:.2%} below threshold {self.min_clv:.2%}"
            logger.info(f"[{event_name}] Rejected: {reason}")
            return False, reason, metrics

        # 6. Pinnacle reference (opcional)
        if self.require_pinnacle and (pinnacle_odds is None or pinnacle_odds <= 1.0):
            reason = "No Pinnacle reference odds available"
            return False, reason, metrics

        # Se chegou aqui, é um value bet!
        logger.info(
            f"[{event_name}] VALUE BET — Edge: {edge:.2%}, EV: {ev:.2%}, "
            f"Kelly: {metrics['kelly_fraction']:.2%}, Bin: {bin_key}"
        )
        return True, None, metrics

    def kelly_stake(
        self,
        bankroll: float,
        model_prob: float,
        odds: float,
        fraction: float = 0.25,  # Quarter-Kelly (conservador)
    ) -> float:
        """Calcula stake usando Fractional Kelly Criterion."""
        if odds <= 1.0 or model_prob <= 0:
            return 0.0

        # Kelly full
        kelly_full = (model_prob * odds - 1.0) / (odds - 1.0)
        kelly_full = max(0.0, kelly_full)

        # Fractional Kelly
        stake_pct = kelly_full * fraction

        # Cap a 5% do bankroll por aposta
        stake_pct = min(stake_pct, 0.05)

        return bankroll * stake_pct
