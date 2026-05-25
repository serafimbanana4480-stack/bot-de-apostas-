"""
CLV (Closing Line Value) objective functions for XGBoost custom training.

Provides:
1. clv_objective() — standalone CLV loss computation
2. clv_xgb_objective() — XGBoost custom objective with gradient & hessian
3. time_decay_weights() — exponential decay for historical samples
4. clv_roi_objective() — combined CLV + ROI loss

The key insight: optimizing log-loss produces well-calibrated probabilities,
but doesn't guarantee profitable bets. CLV loss directly penalizes predictions
that don't beat the closing line, which is the gold standard for edge detection.
"""
from datetime import datetime
from typing import Any, List, Tuple

import numpy as np


def clv_objective(
    y_pred: np.ndarray,
    opening_odds: np.ndarray,
    closing_odds: np.ndarray,
) -> np.ndarray:
    """
    Computes a loss penalty proportional to CLV under-performance.
    The loss is higher when predicted edge and realized CLV have opposite signs.
    """
    predicted_edge = y_pred - (1.0 / opening_odds)
    realized_clv = np.log(closing_odds) - np.log(opening_odds)
    loss = -predicted_edge * realized_clv
    return loss


def clv_xgb_objective(
    preds: np.ndarray,
    dtrain: Any,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    XGBoost custom objective function that maximizes CLV instead of log-loss.

    This replaces the default `reg:logistic` or `binary:logloss` objective.
    The gradient pushes predictions toward values that beat the closing line.

    Usage with XGBoost:
        import xgboost as xgb
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dtrain.set_float_info('opening_odds', opening_odds_train)
        dtrain.set_float_info('closing_odds', closing_odds_train)

        model = xgb.train(
            params={'tree_method': 'hist', 'max_depth': 4},
            dtrain=dtrain,
            num_boost_round=100,
            obj=clv_xgb_objective,
        )

    The opening/closing odds are passed via DMatrix float_info fields.
    """
    labels = dtrain.get_label()
    opening_odds = dtrain.get_float_info('opening_odds')
    closing_odds = dtrain.get_float_info('closing_odds')

    # Convert raw XGBoost output to probabilities via sigmoid
    preds_prob = 1.0 / (1.0 + np.exp(-preds))

    # Predicted edge: how much our probability exceeds implied probability
    implied_prob = 1.0 / opening_odds
    predicted_edge = preds_prob - implied_prob

    # Realized CLV: log ratio of closing to opening odds
    # Positive CLV = we beat the market (closing odds moved in our direction)
    realized_clv = np.log(closing_odds) - np.log(opening_odds)

    # Loss: we want predicted_edge and realized_clv to have the same sign
    # When they agree (both positive or both negative), loss is negative (good)
    # When they disagree, loss is positive (bad)
    loss = -predicted_edge * realized_clv

    # Gradient: d(loss)/d(preds) via chain rule through sigmoid
    # sigmoid derivative: preds_prob * (1 - preds_prob)
    sigmoid_deriv = preds_prob * (1.0 - preds_prob)
    grad = -realized_clv * sigmoid_deriv

    # Hessian: d²(loss)/d(preds)²
    hessian = np.abs(realized_clv) * sigmoid_deriv * (1.0 - 2.0 * preds_prob)
    # Ensure hessian is positive (required by XGBoost for Newton step)
    hessian = np.abs(hessian) + 1e-6

    return grad, hessian


def clv_roi_objective(
    preds: np.ndarray,
    dtrain: Any,
    commission_rate: float = 0.05,
    edge_threshold: float = 0.03,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Combined CLV + ROI objective for XGBoost.

    In addition to beating the closing line, this objective also penalizes
    predictions that would lead to unprofitable bets after commission.

    Args:
        preds: Raw XGBoost predictions
        dtrain: DMatrix with label, opening_odds, closing_odds in float_info
        commission_rate: Exchange commission rate (e.g., 0.05 for 5%)
        edge_threshold: Minimum edge to consider a bet (avoids noise on tiny edges)
    """
    labels = dtrain.get_label()
    opening_odds = dtrain.get_float_info('opening_odds')
    closing_odds = dtrain.get_float_info('closing_odds')

    preds_prob = 1.0 / (1.0 + np.exp(-preds))

    # True odds after commission
    profit_multiplier = opening_odds - 1.0
    net_profit_multiplier = profit_multiplier * (1.0 - commission_rate)
    true_odds = 1.0 + net_profit_multiplier

    # Expected ROI per bet
    expected_roi = (preds_prob * true_odds) - 1.0

    # CLV component
    realized_clv = np.log(closing_odds) - np.log(opening_odds)

    # Combined loss:
    # - CLV component: want predicted edge to align with realized CLV
    # - ROI component: want expected ROI to be positive when we bet
    predicted_edge = preds_prob - (1.0 / opening_odds)

    # Only penalize ROI when edge exceeds threshold (we would actually bet)
    bet_mask = (predicted_edge > edge_threshold).astype(float)

    clv_loss = -predicted_edge * realized_clv
    roi_loss = -expected_roi * bet_mask

    # Weight: 70% CLV, 30% ROI
    combined_loss = 0.7 * clv_loss + 0.3 * roi_loss

    # Gradient
    sigmoid_deriv = preds_prob * (1.0 - preds_prob)
    grad_clv = -realized_clv * sigmoid_deriv
    grad_roi = -(true_odds - 1.0 / opening_odds) * bet_mask * sigmoid_deriv
    grad = 0.7 * grad_clv + 0.3 * grad_roi

    # Hessian (positive definite)
    hessian = (np.abs(0.7 * realized_clv) + 0.3 * bet_mask) * sigmoid_deriv + 1e-6

    return grad, hessian


def time_decay_weights(
    event_timestamps: List[datetime],
    decay_lambda: float = 0.005,
) -> np.ndarray:
    """
    Applies exponential decay weight to historical samples.
    Weights samples closer to current local time higher.
    """
    now = datetime.now()
    weights = []

    for dt in event_timestamps:
        days_diff = (now - dt).days
        w = np.exp(-decay_lambda * max(0, days_diff))
        weights.append(w)

    return np.array(weights)


def asymmetric_clv_objective(
    preds: np.ndarray,
    dtrain: Any,
    commission_rate: float = 0.05,
    edge_threshold: float = 0.03,
    high_stake_penalty: float = 2.0,
    confidence_penalty: float = 1.5,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Asymmetric CLV loss — penalizes false positives (betting when we shouldn't)
    more than false negatives (not betting when we could).

    The penalty scales with:
    - Stake size: Higher-stake errors cost more capital
    - Confidence: High-confidence wrong predictions are especially costly

    This prevents wasting capital on high-risk false positives while
    maintaining sensitivity to genuine edge.

    Args:
        preds: Raw XGBoost predictions
        dtrain: DMatrix with label, opening_odds, closing_odds in float_info
        commission_rate: Exchange commission rate
        edge_threshold: Minimum edge to consider a bet
        high_stake_penalty: Multiplier for errors on high-edge bets (>=2x)
        confidence_penalty: Multiplier for errors when prediction > 0.7 or < 0.3
    """
    labels = dtrain.get_label()
    opening_odds = dtrain.get_float_info('opening_odds')
    closing_odds = dtrain.get_float_info('closing_odds')

    preds_prob = 1.0 / (1.0 + np.exp(-preds))
    implied_prob = 1.0 / opening_odds
    predicted_edge = preds_prob - implied_prob
    realized_clv = np.log(closing_odds) - np.log(opening_odds)

    # Base CLV loss
    base_loss = -predicted_edge * realized_clv

    # Asymmetric penalty: false positives (we bet, market moves against us)
    # predicted_edge > 0 but realized_clv < 0 → we bet and lost CLV
    false_positive = (predicted_edge > edge_threshold) & (realized_clv < 0)
    # false negative: predicted_edge < 0 but realized_clv > 0 → we didn't bet but should have
    false_negative = (predicted_edge < -edge_threshold) & (realized_clv > 0)

    # Scale penalty by confidence (how far from 0.5)
    confidence = np.abs(preds_prob - 0.5) * 2  # 0 at 0.5, 1 at 0 or 1
    confidence_weight = 1.0 + confidence_penalty * confidence

    # Scale penalty by edge magnitude (proxy for stake size via Kelly)
    edge_magnitude = np.abs(predicted_edge)
    stake_weight = 1.0 + (high_stake_penalty - 1.0) * np.clip(edge_magnitude / 0.1, 0, 1)

    # Apply asymmetric weights
    loss = base_loss.copy()
    loss[false_positive] *= confidence_weight[false_positive] * stake_weight[false_positive]
    loss[false_negative] *= 0.5  # Less penalty for missed opportunities

    # Gradient
    sigmoid_deriv = preds_prob * (1.0 - preds_prob)
    grad = -realized_clv * sigmoid_deriv

    # Apply asymmetry to gradient
    fp_grad_scale = np.ones_like(grad)
    fp_grad_scale[false_positive] = confidence_weight[false_positive] * stake_weight[false_positive]
    fp_grad_scale[false_negative] = 0.5
    grad = grad * fp_grad_scale

    # Hessian (positive definite)
    hessian = np.abs(realized_clv) * sigmoid_deriv * fp_grad_scale + 1e-6

    return grad, hessian


def parametric_loss_objective(
    preds: np.ndarray,
    dtrain: Any,
    alpha: float = 1.0,
    beta: float = 2.0,
    commission_rate: float = 0.05,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Parametric loss function: loss = α * (y_pred - y_true)² + β * max(0, y_true - y_pred) * stake_weight.

    The α parameter controls the base squared error weight.
    The β parameter controls the penalty for underestimating the probability
    (false negatives in betting — missing a winning bet).

    Both α and β can be optimized via cross-validation.

    Args:
        preds: Raw XGBoost predictions
        dtrain: DMatrix with label, opening_odds, closing_odds in float_info
        alpha: Weight for squared error component (default 1.0)
        beta: Weight for asymmetric penalty on underestimation (default 2.0)
        commission_rate: Exchange commission rate
    """
    labels = dtrain.get_label()
    opening_odds = dtrain.get_float_info('opening_odds') if dtrain.get_float_info('opening_odds') is not None else np.ones(len(labels)) * 2.0

    preds_prob = 1.0 / (1.0 + np.exp(-preds))

    # Component 1: Squared error (base calibration)
    sq_error = (preds_prob - labels) ** 2

    # Component 2: Asymmetric penalty for underestimation
    # When y_true=1 (home wins) and we predicted low prob → we missed a winning bet
    # Stake weight: proportional to edge (higher edge = higher missed profit)
    implied_prob = 1.0 / opening_odds
    edge = preds_prob - implied_prob
    stake_weight = np.clip(np.abs(edge) * 10, 0, 1)  # Normalized 0-1

    underestimation = np.maximum(0, labels - preds_prob) * stake_weight

    # Combined loss
    loss = alpha * sq_error + beta * underestimation

    # Gradient
    sigmoid_deriv = preds_prob * (1.0 - preds_prob)
    grad_sq = 2.0 * alpha * (preds_prob - labels) * sigmoid_deriv
    grad_under = -beta * stake_weight * sigmoid_deriv * (labels > preds_prob).astype(float)
    grad = grad_sq + grad_under

    # Hessian (positive definite)
    hess_sq = 2.0 * alpha * sigmoid_deriv * (1.0 - 2.0 * (preds_prob - labels) * (1.0 - 2.0 * preds_prob))
    hess_sq = np.abs(hess_sq) + 1e-6
    hess_under = beta * stake_weight * sigmoid_deriv + 1e-6
    hessian = hess_sq + hess_under

    return grad, hessian


# Type alias for dtrain parameter (avoids circular import)
from typing import Any
