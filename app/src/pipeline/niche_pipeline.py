"""
Niche Market Pipeline — Estratégia para mercados ineficientes / lower leagues.

Foca em jogos onde avg_home > 2.5 ou existe divergência significativa
entre b365 e Pinnacle (>10%), indicando mercados menos eficientes.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

logger = logging.getLogger("niche_pipeline")


FEATURES = [
    "home_xg_diff_proxy",
    "away_xg_diff_proxy",
    "form_3_home",
    "h2h_goal_diff",
    "market_divergence",
]

TARGET = "actual_outcome"


def _team_rolling_mean(df: pd.DataFrame, team_col: str, val_col: str, window: int = 5) -> pd.Series:
    """Vectorized rolling mean per team."""
    return (
        df.groupby(team_col)[val_col]
        .transform(lambda s: s.shift(1).rolling(window=window, min_periods=1).mean())
    )


def _team_rolling_points(df: pd.DataFrame, team_col: str, is_home: bool, window: int = 3) -> pd.Series:
    """Vectorized rolling average points per team."""
    if is_home:
        points = np.where(df["home_goals"] > df["away_goals"], 3,
                          np.where(df["home_goals"] == df["away_goals"], 1, 0))
    else:
        points = np.where(df["away_goals"] > df["home_goals"], 3,
                          np.where(df["away_goals"] == df["home_goals"], 1, 0))

    s = pd.Series(points, index=df.index, name="_points")
    df = df.copy()
    df[s.name] = s
    return (
        df.groupby(team_col)[s.name]
        .transform(lambda x: x.shift(1).rolling(window=window, min_periods=1).mean())
    )


def build_niche_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constrói features proxy para mercados de nicho a partir de dados de golos.

    Como xG não está disponível, usamos proxies baseados em golos e divergência de mercado.
    """
    df = df.copy().sort_values(["league", "date"]).reset_index(drop=True)

    # Médias da liga (global por liga)
    league_avg_home_goals = df.groupby("league")["home_goals"].transform("mean")
    league_avg_away_goals = df.groupby("league")["away_goals"].transform("mean")
    league_avg_home_conceded = df.groupby("league")["away_goals"].transform("mean")
    league_avg_away_conceded = df.groupby("league")["home_goals"].transform("mean")

    # Rolling ratings por equipa (últimos 5 jogos) — vectorized
    home_attack = _team_rolling_mean(df, "home_team", "home_goals", window=5)
    home_defense = _team_rolling_mean(df, "home_team", "away_goals", window=5)
    away_attack = _team_rolling_mean(df, "away_team", "away_goals", window=5)
    away_defense = _team_rolling_mean(df, "away_team", "home_goals", window=5)

    # Normalizar pela média da liga
    df["home_attack_rating"] = home_attack / league_avg_home_goals.replace(0, np.nan)
    df["home_defense_rating"] = home_defense / league_avg_home_conceded.replace(0, np.nan)
    df["away_attack_rating"] = away_attack / league_avg_away_goals.replace(0, np.nan)
    df["away_defense_rating"] = away_defense / league_avg_away_conceded.replace(0, np.nan)

    # xG diff proxies
    df["home_xg_diff_proxy"] = df["home_attack_rating"].fillna(1.0) - df["away_defense_rating"].fillna(1.0)
    df["away_xg_diff_proxy"] = df["away_attack_rating"].fillna(1.0) - df["home_defense_rating"].fillna(1.0)

    # Forma dos últimos 3 jogos (pontos médios) — vectorized
    df["form_3_home"] = _team_rolling_points(df, "home_team", is_home=True, window=3).fillna(1.0)
    df["form_3_away"] = _team_rolling_points(df, "away_team", is_home=False, window=3).fillna(1.0)

    # H2H — diferença de golos média nos últimos 3 encontros diretos
    # Vectorized via groupby on sorted tuple of teams
    def _sorted_pair(h, a):
        return tuple(sorted([h, a]))

    df["_pair"] = df.apply(lambda r: _sorted_pair(r["home_team"], r["away_team"]), axis=1)

    # Goal diff from home perspective
    df["_gd"] = df["home_goals"] - df["away_goals"]

    # Rolling H2H mean per pair, shifted
    h2h_rolling = (
        df.groupby("_pair")["_gd"]
        .transform(lambda s: s.shift(1).rolling(window=3, min_periods=1).mean())
    )

    # If the current row has home/away reversed relative to the rolling mean,
    # we need to flip the sign when away team was home in past meetings.
    # Simplification: use the raw rolling mean (it averages both perspectives).
    # For a better approximation, compute per-direction H2H:
    df["_dir"] = df["home_team"] + "|" + df["away_team"]
    dir_rolling = (
        df.groupby("_dir")["_gd"]
        .transform(lambda s: s.shift(1).rolling(window=3, min_periods=1).mean())
    )

    df["h2h_goal_diff"] = dir_rolling.fillna(0.0)

    # Divergência de mercado
    pin_home = df["pin_close_home"].replace(0, np.nan)
    df["market_divergence"] = (df["b365_home"] - pin_home).abs() / pin_home
    df["market_divergence"] = df["market_divergence"].fillna(0.0)

    # Cleanup temp columns
    df = df.drop(columns=["_pair", "_gd", "_dir"], errors="ignore")

    return df


def filter_niche_markets(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra jogos em mercados de nicho (ineficientes)."""
    mask = (df["avg_home"] > 2.5) | (
        (df["b365_home"] - df["pin_close_home"]).abs() / df["pin_close_home"].replace(0, np.nan) > 0.10
    )
    return df[mask].copy()


class NicheMarketStrategy:
    """
    Estratégia simplificada para mercados de nicho.

    Usa apenas 5 features proxy e um modelo Random Forest leve.
    """

    def __init__(self, model: Optional[Any] = None, min_prob: float = 0.35):
        self.model = model or RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_leaf=10,
            random_state=42,
            n_jobs=-1,
        )
        self.min_prob = min_prob
        self.is_fitted = False

    def fit(self, df: pd.DataFrame) -> "NicheMarketStrategy":
        """Treina o modelo em dados de mercados de nicho."""
        df = build_niche_features(df)
        df = filter_niche_markets(df)

        if df.empty:
            raise ValueError("Nenhum dado de mercado de nicho disponível para treino.")

        X = df[FEATURES].fillna(0.0)
        y = df[TARGET]

        self.model.fit(X, y)
        self.is_fitted = True
        self._feature_importance = dict(zip(FEATURES, self.model.feature_importances_))
        logger.info(f"Modelo treinado em {len(df)} jogos de nicho.")
        logger.info(f"Feature importances: {self._feature_importance}")
        return self

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Gera previsões com probabilidades para cada resultado."""
        if not self.is_fitted:
            raise RuntimeError("Modelo ainda não treinado. Chame fit() primeiro.")

        df = build_niche_features(df)
        X = df[FEATURES].fillna(0.0)

        probs = self.model.predict_proba(X)
        classes = self.model.classes_

        for i, cls in enumerate(classes):
            df[f"prob_{cls}"] = probs[:, i]

        df["predicted_outcome"] = (
            df[[f"prob_{c}" for c in classes]]
            .idxmax(axis=1)
            .str.replace("prob_", "")
        )

        return df

    def backtest(
        self,
        df: pd.DataFrame,
        odds_col_map: Optional[Dict[str, str]] = None,
        stake_pct: float = 0.01,
    ) -> Dict[str, Any]:
        """
        Corre backtest usando apenas mercados de nicho (avg_home > 2.5).

        Args:
            df: DataFrame com dados históricos completos.
            odds_col_map: Mapping de outcome -> coluna de odds. Default usa avg_*.
            stake_pct: Percentagem do bankroll a apostar por jogo (flat stake).
        """
        if odds_col_map is None:
            odds_col_map = {
                "1": "avg_home",
                "X": "avg_draw",
                "2": "avg_away",
            }

        df = build_niche_features(df)
        # Backtest apenas em mercados de nicho estritos (avg_home > 2.5)
        df_niche = df[df["avg_home"] > 2.5].copy()

        if df_niche.empty:
            return {
                "total_bets": 0,
                "win_rate": 0.0,
                "roi": 0.0,
                "profit_units": 0.0,
                "avg_odds": 0.0,
            }

        # Split temporal simples: treino nos primeiros 80%, teste nos últimos 20%
        split_idx = int(len(df_niche) * 0.8)
        df_train = df_niche.iloc[:split_idx]
        df_test = df_niche.iloc[split_idx:].copy()

        if len(df_train) < 50 or len(df_test) < 10:
            logger.warning("Dados insuficientes para backtest robusto.")
            return {
                "total_bets": 0,
                "win_rate": 0.0,
                "roi": 0.0,
                "profit_units": 0.0,
                "avg_odds": 0.0,
            }

        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_leaf=10,
            random_state=42,
            n_jobs=-1,
        )
        X_train = df_train[FEATURES].fillna(0.0)
        y_train = df_train[TARGET]
        self.model.fit(X_train, y_train)
        self.is_fitted = True

        df_test = df_test.copy()
        X_test = df_test[FEATURES].fillna(0.0)
        probs = self.model.predict_proba(X_test)
        classes = self.model.classes_

        for i, cls in enumerate(classes):
            df_test[f"prob_{cls}"] = probs[:, i]

        df_test["predicted_outcome"] = (
            df_test[[f"prob_{c}" for c in classes]]
            .idxmax(axis=1)
            .str.replace("prob_", "")
        )

        # Simular apostas — vectorized
        df_test["odds_col"] = df_test["predicted_outcome"].map(odds_col_map)
        df_test["odds"] = df_test.apply(
            lambda r: r.get(r["odds_col"]) if pd.notna(r["odds_col"]) else np.nan, axis=1
        )
        df_test = df_test.dropna(subset=["odds"])
        df_test = df_test[df_test["odds"] > 1.0]

        if df_test.empty:
            return {
                "total_bets": 0,
                "win_rate": 0.0,
                "roi": 0.0,
                "profit_units": 0.0,
                "avg_odds": 0.0,
            }

        df_test["stake"] = stake_pct
        df_test["won"] = df_test["predicted_outcome"] == df_test[TARGET]
        df_test["profit"] = np.where(
            df_test["won"],
            (df_test["odds"] - 1) * df_test["stake"],
            -df_test["stake"]
        )

        total_stake = df_test["stake"].sum()
        total_profit = df_test["profit"].sum()

        return {
            "total_bets": len(df_test),
            "win_rate": df_test["won"].mean(),
            "roi": total_profit / total_stake if total_stake > 0 else 0.0,
            "profit_units": total_profit,
            "avg_odds": df_test["odds"].mean(),
            "feature_importance": dict(zip(FEATURES, self.model.feature_importances_)),
        }
