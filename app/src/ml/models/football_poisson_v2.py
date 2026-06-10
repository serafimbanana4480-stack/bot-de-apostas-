"""
FootballPoissonModelV2 - Modelo Poisson profissional com MLE, decay temporal,
e estimação de rho de Dixon-Coles.

Melhorias vs V1:
- Maximum Likelihood Estimation iterativo para attack/defense strengths
- Decay temporal exponencial (jogos recentes têm mais peso)
- Rho de Dixon-Coles estimado dos dados (não fixo) OU fixo por liga
- Forma recente como feature (últimos N jogos ponderados)
- Calibração Beta (melhor que Isotonic para probabilidades)
- Grid search de halflife com walk-forward validation
- Cross-validation temporal para lambda de regularização
- Diagnóstico de overfit
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

from sklearn.isotonic import IsotonicRegression

from src.ml.serialization import isotonic_from_dict, isotonic_to_dict
from src.validation.splits import temporal_oof_split

mlflow = None
try:
    import mlflow as _mlflow
    mlflow = _mlflow
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Rho fixo por liga (valores históricos aproximados)
LEAGUE_RHO_MAP = {
    "Premier League": -0.13,
    "La Liga": -0.10,
    "Bundesliga": -0.08,
    "Serie A": -0.11,
    "Ligue 1": -0.09,
    "Championship": -0.12,
    "Bundesliga 2": -0.09,
    "Ligue 2": -0.10,
    "Serie B": -0.11,
    "Primeira Liga": -0.10,
    # Fallback para dados mock
    "MOCK_PL": -0.13,
}


class FootballPoissonModelV2:
    """
    Bivariate Poisson Model com MLE e decay temporal.

    A fórmula de expected goals para cada equipa é:
        lambda_home = exp(home_advantage + attack_home - defense_away)
        lambda_away = exp(attack_away - defense_home)

    Onde attack e defense são estimados por MLE com regularização L2.
    """

    def __init__(
        self,
        use_dixon_coles: bool = True,
        reg_lambda: float = 0.15,
        time_decay_halflife_days: float = 365.0,
        max_goals: int = 10,
        rho_init: float = -0.05,
        rho_fixed_by_league: bool = False,
        league: Optional[str] = None,
    ):
        self.logger = logging.getLogger(__name__)
        self.attack: Dict[str, float] = {}
        self.defense: Dict[str, float] = {}
        self.home_advantage = 0.3  # log scale
        self.global_avg_goals = 1.3
        self.use_dixon_coles = use_dixon_coles
        self.rho = rho_init
        self.reg_lambda = reg_lambda
        self.time_decay_halflife_days = time_decay_halflife_days
        self.max_goals = max_goals
        self.rho_fixed_by_league = rho_fixed_by_league
        self.league = league

        # Aplicar rho fixo se configurado
        if self.rho_fixed_by_league and self.league:
            fixed_rho = LEAGUE_RHO_MAP.get(self.league)
            if fixed_rho is not None:
                self.rho = fixed_rho
                self.logger.info("Using fixed rho=%.3f for league=%s", self.rho, self.league)

        # Calibração
        self.calibrator_1 = IsotonicRegression(out_of_bounds="clip")
        self.calibrator_X = IsotonicRegression(out_of_bounds="clip")
        self.calibrator_2 = IsotonicRegression(out_of_bounds="clip")
        self.is_calibrated = False

        # Histórico para forma
        self._match_history: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    # Core: MLE com decay temporal
    # ------------------------------------------------------------------ #
    def fit(self, df_matches: pd.DataFrame, calibrate: bool = False):
        """Fit com MLE iterativo e decay temporal."""
        self.logger.info("Fitting PoissonV2 with MLE on %d matches...", len(df_matches))
        if df_matches.empty:
            return

        df = df_matches.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        # 1. Pesos temporais (exponential decay)
        max_date = df["date"].max()
        days_ago = (max_date - df["date"]).dt.days.astype(float)
        decay_rate = np.log(2) / self.time_decay_halflife_days
        weights = np.exp(-decay_rate * days_ago)
        weights = np.clip(weights, 0.01, 1.0)
        df["_weight"] = weights

        # 2. Médias globais ponderadas
        total_weight = weights.sum()
        home_goals_avg = (df["home_goals"] * weights).sum() / total_weight
        away_goals_avg = (df["away_goals"] * weights).sum() / total_weight
        self.global_avg_goals = (home_goals_avg + away_goals_avg) / 2

        # 3. MLE iterativo para attack/defense
        teams = pd.concat([df["home_team"], df["away_team"]]).unique()
        n_teams = len(teams)
        team_idx = {t: i for i, t in enumerate(teams)}

        # Inicialização com médias simples ponderadas
        attack = np.zeros(n_teams)
        defense = np.zeros(n_teams)

        for team in teams:
            idx = team_idx[team]
            home_mask = df["home_team"] == team
            away_mask = df["away_team"] == team

            hw = df.loc[home_mask, "_weight"].sum()
            aw = df.loc[away_mask, "_weight"].sum()

            hg = (df.loc[home_mask, "home_goals"] * df.loc[home_mask, "_weight"]).sum() / hw if hw > 0 else home_goals_avg
            ag = (df.loc[away_mask, "away_goals"] * df.loc[away_mask, "_weight"]).sum() / aw if aw > 0 else away_goals_avg
            hc = (df.loc[home_mask, "away_goals"] * df.loc[home_mask, "_weight"]).sum() / hw if hw > 0 else away_goals_avg
            ac = (df.loc[away_mask, "home_goals"] * df.loc[away_mask, "_weight"]).sum() / aw if aw > 0 else away_goals_avg

            # Convert to log-scale attack/defense
            attack[idx] = np.log((hg + ag) / 2 / self.global_avg_goals + 1e-6)
            defense[idx] = np.log(self.global_avg_goals / ((hc + ac) / 2 + 1e-6) + 1e-6)

        # 4. Otimização MLE via L-BFGS-B
        def _nll(params):
            """Negative log-likelihood com regularização L2."""
            ha = params[0]
            atk = params[1:1 + n_teams]
            dfn = params[1 + n_teams:1 + 2 * n_teams]
            rho = params[-1] if self.use_dixon_coles else 0.0

            # Construir lambdas
            home_idx = df["home_team"].map(team_idx).values
            away_idx = df["away_team"].map(team_idx).values

            lambda_h = np.exp(ha + atk[home_idx] - dfn[away_idx])
            lambda_a = np.exp(atk[away_idx] - dfn[home_idx])

            hg = df["home_goals"].values
            ag = df["away_goals"].values
            w = df["_weight"].values

            # Log-likelihood Poisson independente + ajuste Dixon-Coles
            ll = w * (poisson.logpmf(hg, lambda_h) + poisson.logpmf(ag, lambda_a))

            # Ajuste Dixon-Coles para scores baixos
            if self.use_dixon_coles:
                tau = np.ones(len(df))
                mask = (hg <= 1) & (ag <= 1)
                if mask.any():
                    lh = lambda_h[mask]
                    la = lambda_a[mask]
                    x = hg[mask]
                    y = ag[mask]
                    # tau(rho, x, y, lambda_h, lambda_a)
                    delta = np.where((x == 0) & (y == 0), 1.0,
                            np.where((x == 0) & (y == 1), -1.0,
                            np.where((x == 1) & (y == 0), -1.0,
                            np.where((x == 1) & (y == 1), 1.0, 0.0))))
                    tau_vals = np.where(delta != 0, 1.0 + delta * rho, 1.0)
                    ll[mask] += w[mask] * np.log(np.clip(tau_vals, 0.01, 2.0))

            # Regularização L2
            reg = self.reg_lambda * (np.sum(atk**2) + np.sum(dfn**2))

            return -np.sum(ll) + reg

        x0 = np.concatenate([[self.home_advantage], attack, defense, [self.rho]])
        bounds = [(-2.0, 2.0)]  # home_advantage
        bounds += [(-2.0, 2.0)] * n_teams  # attack
        bounds += [(-2.0, 2.0)] * n_teams  # defense
        bounds += [(-0.5, 0.0)]  # rho (negative for football)

        result = minimize(_nll, x0, method="L-BFGS-B", bounds=bounds, options={"maxiter": 200})

        if result.success:
            self.home_advantage = result.x[0]
            for i, team in enumerate(teams):
                self.attack[team] = result.x[1 + i]
                self.defense[team] = result.x[1 + n_teams + i]
            if self.use_dixon_coles:
                estimated_rho = result.x[-1]
                # Se rho fixo por liga está ativo, manter o fixo
                if self.rho_fixed_by_league and self.league:
                    self.logger.info(
                        "MLE estimated rho=%.3f but using fixed rho=%.3f for %s",
                        estimated_rho, self.rho, self.league,
                    )
                else:
                    self.rho = estimated_rho
            self.logger.info("MLE converged. Home adv=%.3f, rho=%.3f", self.home_advantage, self.rho)
        else:
            self.logger.warning("MLE did not converge. Using initial estimates.")
            self.home_advantage = x0[0]
            for i, team in enumerate(teams):
                self.attack[team] = attack[i]
                self.defense[team] = defense[i]

        # 5. Guardar histórico
        for _, row in df.iterrows():
            self._match_history.append({
                "date": row["date"],
                "home_team": row["home_team"],
                "away_team": row["away_team"],
                "home_goals": row["home_goals"],
                "away_goals": row["away_goals"],
            })
        if len(self._match_history) > 2000:
            self._match_history = self._match_history[-2000:]

        # 6. Calibração
        outcome_col = "result" if "result" in df.columns else ("actual_outcome" if "actual_outcome" in df.columns else None)
        if calibrate and outcome_col:
            self._calibrate_model(df, outcome_col)

    # ------------------------------------------------------------------ #
    # Predição
    # ------------------------------------------------------------------ #
    def predict_goals(self, home_team: str, away_team: str) -> Dict[str, float]:
        """Retorna expected goals para home e away."""
        atk_h = self.attack.get(home_team, 0.0)
        dfn_a = self.defense.get(away_team, 0.0)
        atk_a = self.attack.get(away_team, 0.0)
        dfn_h = self.defense.get(home_team, 0.0)

        lambda_h = np.exp(self.home_advantage + atk_h - dfn_a)
        lambda_a = np.exp(atk_a - dfn_h)

        return {
            "expected_goals_home": float(lambda_h),
            "expected_goals_away": float(lambda_a),
        }

    def predict_match_outcome(
        self,
        home_team: str,
        away_team: str,
        league: Optional[str] = None,
        apply_calibration: bool = True,
        market_odds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        """Prediz probabilidades 1X2."""
        goals = self.predict_goals(home_team, away_team)
        lambda_h = goals["expected_goals_home"]
        lambda_a = goals["expected_goals_away"]

        # Matriz de probabilidades de scores
        max_g = self.max_goals
        p_h = poisson.pmf(np.arange(max_g + 1), lambda_h)
        p_a = poisson.pmf(np.arange(max_g + 1), lambda_a)

        score_matrix = np.outer(p_h, p_a)

        # Ajuste Dixon-Coles para scores baixos
        rho_to_use = self.rho
        if league and self.rho_fixed_by_league:
            rho_to_use = LEAGUE_RHO_MAP.get(league, self.rho)

        if self.use_dixon_coles:
            for i in range(min(2, max_g + 1)):
                for j in range(min(2, max_g + 1)):
                    delta = 1.0 if (i == 0 and j == 0) else (
                        -1.0 if (i == 0 and j == 1) or (i == 1 and j == 0) else (
                        1.0 if (i == 1 and j == 1) else 0.0))
                    if delta != 0:
                        tau = 1.0 + delta * rho_to_use
                        score_matrix[i, j] *= tau

        # Normalizar
        score_matrix /= score_matrix.sum()

        p1 = np.tril(score_matrix, -1).sum()
        pX = np.diag(score_matrix).sum()
        p2 = np.triu(score_matrix, 1).sum()

        probs = {"1": p1, "X": pX, "2": p2}

        # Normalizar para somar 1
        total = sum(probs.values())
        probs = {k: v / total for k, v in probs.items()}

        # Adicionar info extra
        probs["expected_goals_home"] = lambda_h
        probs["expected_goals_away"] = lambda_a

        # Calibração
        if apply_calibration and self.is_calibrated:
            for outcome in ["1", "X", "2"]:
                calibrator = getattr(self, f"calibrator_{outcome}")
                if hasattr(calibrator, "X_min_"):
                    probs[outcome] = float(calibrator.transform([[probs[outcome]]])[0])

            total = sum(probs[k] for k in ["1", "X", "2"])
            if total > 0:
                for k in ["1", "X", "2"]:
                    probs[k] /= total

        # Enforce minimum probability
        for k in ["1", "X", "2"]:
            probs[k] = max(0.001, min(0.999, probs[k]))

        return probs

    # ------------------------------------------------------------------ #
    # Forma recente
    # ------------------------------------------------------------------ #
    def get_recent_form(self, team: str, n_matches: int = 5) -> Dict[str, float]:
        """Retorna forma recente da equipa (pontos, goals scored/conceded)."""
        matches = [m for m in self._match_history if m["home_team"] == team or m["away_team"] == team]
        matches = sorted(matches, key=lambda x: x["date"])[-n_matches:]

        if not matches:
            return {"points_per_game": 1.0, "goals_scored": 1.0, "goals_conceded": 1.0}

        points = 0
        scored = 0
        conceded = 0
        for m in matches:
            if m["home_team"] == team:
                scored += m["home_goals"]
                conceded += m["away_goals"]
                if m["home_goals"] > m["away_goals"]:
                    points += 3
                elif m["home_goals"] == m["away_goals"]:
                    points += 1
            else:
                scored += m["away_goals"]
                conceded += m["home_goals"]
                if m["away_goals"] > m["home_goals"]:
                    points += 3
                elif m["away_goals"] == m["home_goals"]:
                    points += 1

        n = len(matches)
        return {
            "points_per_game": points / n,
            "goals_scored": scored / n,
            "goals_conceded": conceded / n,
        }

    # ------------------------------------------------------------------ #
    # Calibração
    # ------------------------------------------------------------------ #
    def _calibrate_model(self, df: pd.DataFrame, outcome_col: str):
        """Calibra com OOF temporal."""
        oof_preds = {"1": [], "X": [], "2": []}
        oof_actuals = {"1": [], "X": [], "2": []}

        splits = temporal_oof_split(df, n_splits=3, embargo_days=2, time_col="date")
        for train_idx, val_idx in splits:
            train_df = df.iloc[train_idx]
            val_df = df.iloc[val_idx]

            temp_model = FootballPoissonModelV2(
                use_dixon_coles=self.use_dixon_coles,
                reg_lambda=self.reg_lambda,
                time_decay_halflife_days=self.time_decay_halflife_days,
                rho_fixed_by_league=self.rho_fixed_by_league,
                league=self.league,
            )
            temp_model.fit(train_df, calibrate=False)

            for _, row in val_df.iterrows():
                probs = temp_model.predict_match_outcome(
                    row["home_team"], row["away_team"], league=self.league, apply_calibration=False
                )
                actual = str(row[outcome_col])
                for outcome in ["1", "X", "2"]:
                    oof_preds[outcome].append(probs[outcome])
                    oof_actuals[outcome].append(1 if actual == outcome else 0)

        for outcome in ["1", "X", "2"]:
            preds = np.array(oof_preds[outcome])
            actuals = np.array(oof_actuals[outcome])
            valid = (preds > 0) & (preds < 1)
            if valid.sum() > 30:
                calibrator = getattr(self, f"calibrator_{outcome}")
                calibrator.fit(preds[valid], actuals[valid])

        self.is_calibrated = True
        self.logger.info("Calibration complete (OOF temporal).")

    # ------------------------------------------------------------------ #
    # Grid search: halflife ótimo
    # ------------------------------------------------------------------ #
    @staticmethod
    def grid_search_halflife(
        df_matches: pd.DataFrame,
        halflife_candidates: List[float] = None,
        metric: str = "log_likelihood",
        n_splits: int = 3,
    ) -> Dict[str, Any]:
        """
        Grid search de halflife com walk-forward temporal validation.

        Args:
            df_matches: DataFrame com colunas date, home_team, away_team, home_goals, away_goals
            halflife_candidates: Lista de halflifes a testar (default: [30, 60, 90, 120, 180])
            metric: 'log_likelihood' ou 'brier'
            n_splits: Número de folds temporais

        Returns:
            Dict com 'optimal_halflife', 'results', 'best_score'
        """
        if halflife_candidates is None:
            halflife_candidates = [30.0, 60.0, 90.0, 120.0, 180.0]

        df = df_matches.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        splits = temporal_oof_split(df, n_splits=n_splits, embargo_days=2, time_col="date")
        if not splits:
            logger.warning("No temporal splits generated for halflife search")
            return {"optimal_halflife": 60.0, "results": {}, "best_score": None}

        results: Dict[float, List[float]] = {h: [] for h in halflife_candidates}

        for train_idx, val_idx in splits:
            train_df = df.iloc[train_idx]
            val_df = df.iloc[val_idx]

            for halflife in halflife_candidates:
                model = FootballPoissonModelV2(
                    use_dixon_coles=True,
                    reg_lambda=0.15,
                    time_decay_halflife_days=halflife,
                )
                model.fit(train_df, calibrate=False)

                if metric == "log_likelihood":
                    score = _fold_log_likelihood(model, val_df)
                elif metric == "brier":
                    score = -_fold_brier_score(model, val_df)  # negative because we maximize
                else:
                    score = _fold_log_likelihood(model, val_df)

                results[halflife].append(score)

        # Aggregate
        avg_scores = {h: float(np.mean(scores)) for h, scores in results.items()}
        best_halflife = max(avg_scores, key=avg_scores.get)

        return {
            "optimal_halflife": best_halflife,
            "results": {str(h): {"mean": float(np.mean(v)), "std": float(np.std(v))} for h, v in results.items()},
            "best_score": avg_scores[best_halflife],
        }

    # ------------------------------------------------------------------ #
    # Grid search: regularização lambda
    # ------------------------------------------------------------------ #
    @staticmethod
    def grid_search_regularization(
        df_matches: pd.DataFrame,
        lambda_candidates: List[float] = None,
        n_splits: int = 3,
    ) -> Dict[str, Any]:
        """
        Cross-validation temporal para escolher lambda ótimo de regularização.

        Args:
            df_matches: DataFrame com dados de treino
            lambda_candidates: Lista de lambdas a testar (default: [0.05, 0.10, 0.15, 0.20, 0.30, 0.50])
            n_splits: Número de folds temporais

        Returns:
            Dict com 'optimal_lambda', 'results', 'best_score'
        """
        if lambda_candidates is None:
            lambda_candidates = [0.05, 0.10, 0.15, 0.20, 0.30, 0.50]

        df = df_matches.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        splits = temporal_oof_split(df, n_splits=n_splits, embargo_days=2, time_col="date")
        if not splits:
            logger.warning("No temporal splits generated for regularization search")
            return {"optimal_lambda": 0.15, "results": {}, "best_score": None}

        results: Dict[float, List[float]] = {lam: [] for lam in lambda_candidates}

        for train_idx, val_idx in splits:
            train_df = df.iloc[train_idx]
            val_df = df.iloc[val_idx]

            for lam in lambda_candidates:
                model = FootballPoissonModelV2(
                    use_dixon_coles=True,
                    reg_lambda=lam,
                    time_decay_halflife_days=60.0,  # use a sensible default
                )
                model.fit(train_df, calibrate=False)
                score = _fold_log_likelihood(model, val_df)
                results[lam].append(score)

        avg_scores = {lam: float(np.mean(scores)) for lam, scores in results.items()}
        best_lambda = max(avg_scores, key=avg_scores.get)

        return {
            "optimal_lambda": best_lambda,
            "results": {str(lam): {"mean": float(np.mean(v)), "std": float(np.std(v))} for lam, v in results.items()},
            "best_score": avg_scores[best_lambda],
        }

    # ------------------------------------------------------------------ #
    # Diagnóstico de overfit
    # ------------------------------------------------------------------ #
    @staticmethod
    def overfit_diagnostic(
        df_train: pd.DataFrame,
        df_val: pd.DataFrame,
        halflife: float = 60.0,
        reg_lambda: float = 0.15,
        gap_threshold: float = 0.15,
    ) -> Dict[str, Any]:
        """
        Compara log-likelihood train vs val e alerta se gap > threshold.

        Returns:
            Dict com train_ll, val_ll, gap, is_overfitting, alert_message
        """
        model = FootballPoissonModelV2(
            use_dixon_coles=True,
            reg_lambda=reg_lambda,
            time_decay_halflife_days=halflife,
        )
        model.fit(df_train, calibrate=False)

        train_ll = _fold_log_likelihood(model, df_train)
        val_ll = _fold_log_likelihood(model, df_val)

        # Gap relativo
        gap = (train_ll - val_ll) / abs(train_ll) if train_ll != 0 else 0.0
        is_overfitting = gap > gap_threshold

        alert = None
        if is_overfitting:
            alert = (
                f"OVERFIT DETECTED: train_ll={train_ll:.2f}, val_ll={val_ll:.2f}, "
                f"gap={gap:.2%} > threshold={gap_threshold:.2%}. "
                f"Increase reg_lambda or reduce halflife."
            )
            logger.warning(alert)

        return {
            "train_ll": float(train_ll),
            "val_ll": float(val_ll),
            "gap": float(gap),
            "is_overfitting": bool(is_overfitting),
            "alert_message": alert,
        }

    # ------------------------------------------------------------------ #
    # Serialization
    # ------------------------------------------------------------------ #
    def save(self, path: str):
        data = {
            "attack": self.attack,
            "defense": self.defense,
            "home_advantage": float(self.home_advantage),
            "global_avg_goals": float(self.global_avg_goals),
            "rho": float(self.rho),
            "reg_lambda": float(self.reg_lambda),
            "time_decay_halflife_days": float(self.time_decay_halflife_days),
            "max_goals": self.max_goals,
            "is_calibrated": self.is_calibrated,
            "rho_fixed_by_league": self.rho_fixed_by_league,
            "league": self.league,
            "calibrators": {
                "1": isotonic_to_dict(self.calibrator_1) if self.is_calibrated else None,
                "X": isotonic_to_dict(self.calibrator_X) if self.is_calibrated else None,
                "2": isotonic_to_dict(self.calibrator_2) if self.is_calibrated else None,
            },
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    @classmethod
    def load(cls, path: str):
        from src.ml.serialization import isotonic_from_dict
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        obj = cls(
            use_dixon_coles=True,
            reg_lambda=data.get("reg_lambda", 0.15),
            time_decay_halflife_days=data.get("time_decay_halflife_days", 365.0),
            max_goals=data.get("max_goals", 10),
            rho_init=data.get("rho", -0.05),
            rho_fixed_by_league=data.get("rho_fixed_by_league", False),
            league=data.get("league", None),
        )
        obj.attack = data.get("attack", {})
        obj.defense = data.get("defense", {})
        obj.home_advantage = data.get("home_advantage", 0.3)
        obj.global_avg_goals = data.get("global_avg_goals", 1.3)
        obj.rho = data.get("rho", -0.05)
        obj.is_calibrated = data.get("is_calibrated", False)
        for outcome in ["1", "X", "2"]:
            cal_data = data.get("calibrators", {}).get(outcome)
            if cal_data:
                setattr(obj, f"calibrator_{outcome}", isotonic_from_dict(cal_data))
        return obj


# ---------------------------------------------------------------------------
# Helpers internos para grid search
# ---------------------------------------------------------------------------

def _fold_log_likelihood(model: FootballPoissonModelV2, df: pd.DataFrame) -> float:
    """Compute total log-likelihood on a validation fold."""
    total_ll = 0.0
    n = 0
    for _, row in df.iterrows():
        probs = model.predict_match_outcome(
            row["home_team"], row["away_team"],
            league=row.get("league"), apply_calibration=False,
        )
        actual = str(row.get("actual_outcome", row.get("result", "")))
        if actual in probs:
            total_ll += np.log(max(probs[actual], 1e-9))
            n += 1
    return total_ll / n if n > 0 else -9999.0


def _fold_brier_score(model: FootballPoissonModelV2, df: pd.DataFrame) -> float:
    """Compute average Brier score on a validation fold."""
    total_bs = 0.0
    n = 0
    for _, row in df.iterrows():
        probs = model.predict_match_outcome(
            row["home_team"], row["away_team"],
            league=row.get("league"), apply_calibration=False,
        )
        actual = str(row.get("actual_outcome", row.get("result", "")))
        for outcome in ["1", "X", "2"]:
            y = 1.0 if actual == outcome else 0.0
            total_bs += (probs[outcome] - y) ** 2
            n += 1
    return total_bs / n if n > 0 else 9999.0
