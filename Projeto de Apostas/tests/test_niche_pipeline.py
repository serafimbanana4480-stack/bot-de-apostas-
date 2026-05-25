import numpy as np
import pandas as pd
import pytest

from src.pipeline.niche_pipeline import (
    build_niche_features,
    filter_niche_markets,
    NicheMarketStrategy,
    FEATURES,
)


class TestBuildNicheFeatures:
    def test_creates_required_features(self):
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=10),
            "league": ["PL"] * 10,
            "home_team": [f"H{i}" for i in range(10)],
            "away_team": [f"A{i}" for i in range(10)],
            "home_goals": np.random.randint(0, 4, 10),
            "away_goals": np.random.randint(0, 4, 10),
            "actual_outcome": np.random.choice([1, 2, 3], 10),
            "b365_home": np.random.uniform(1.5, 3.0, 10),
            "pin_close_home": np.random.uniform(1.5, 3.0, 10),
            "avg_home": np.random.uniform(1.5, 3.5, 10),
        })

        result = build_niche_features(df)
        for feat in FEATURES:
            assert feat in result.columns, f"Feature {feat} não encontrada"

    def test_market_divergence_range(self):
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=5),
            "league": ["PL"] * 5,
            "home_team": [f"H{i}" for i in range(5)],
            "away_team": [f"A{i}" for i in range(5)],
            "home_goals": [1, 2, 1, 0, 3],
            "away_goals": [0, 1, 1, 2, 1],
            "actual_outcome": [1, 1, 3, 2, 1],
            "b365_home": [2.0, 2.5, 3.0, 1.8, 2.2],
            "pin_close_home": [2.0, 2.0, 3.0, 2.0, 2.0],
            "avg_home": [2.0, 2.2, 3.0, 1.9, 2.1],
        })

        result = build_niche_features(df)
        # Divergência deve ser >= 0
        assert (result["market_divergence"] >= 0).all()
        # Quando b365 == pin, divergência == 0
        assert result.loc[0, "market_divergence"] == pytest.approx(0.0, abs=1e-6)
        assert result.loc[2, "market_divergence"] == pytest.approx(0.0, abs=1e-6)


class TestFilterNicheMarkets:
    def test_filters_by_avg_home(self):
        df = pd.DataFrame({
            "avg_home": [1.5, 2.6, 3.0, 1.8],
            "b365_home": [1.5, 2.6, 3.0, 1.8],
            "pin_close_home": [1.5, 2.5, 2.8, 1.8],
        })
        result = filter_niche_markets(df)
        assert len(result) == 2
        assert (result["avg_home"] > 2.5).all()

    def test_filters_by_divergence(self):
        df = pd.DataFrame({
            "avg_home": [1.5, 1.6, 1.7],
            "b365_home": [1.5, 1.8, 2.0],
            "pin_close_home": [1.5, 1.5, 1.5],
        })
        result = filter_niche_markets(df)
        # A linha 1 tem divergência (1.8 - 1.5) / 1.5 = 0.20 > 0.10
        # A linha 2 tem divergência (2.0 - 1.5) / 1.5 = 0.33 > 0.10
        assert len(result) == 2
        assert result.iloc[-1]["b365_home"] == pytest.approx(2.0)


class TestNicheMarketStrategy:
    def test_fit_and_predict(self):
        np.random.seed(42)
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=100),
            "league": ["PL"] * 100,
            "home_team": np.random.choice(["A", "B", "C", "D"], 100),
            "away_team": np.random.choice(["A", "B", "C", "D"], 100),
            "home_goals": np.random.randint(0, 4, 100),
            "away_goals": np.random.randint(0, 4, 100),
            "actual_outcome": np.random.choice([1, 2, 3], 100),
            "b365_home": np.random.uniform(1.5, 4.0, 100),
            "pin_close_home": np.random.uniform(1.5, 4.0, 100),
            "avg_home": np.random.uniform(1.5, 5.0, 100),
            "avg_draw": np.random.uniform(3.0, 4.5, 100),
            "avg_away": np.random.uniform(1.5, 5.0, 100),
        })

        strategy = NicheMarketStrategy()
        strategy.fit(df)
        assert strategy.is_fitted

        preds = strategy.predict(df)
        assert "predicted_outcome" in preds.columns
        assert "prob_1" in preds.columns or "prob_2" in preds.columns

    def test_backtest_returns_metrics(self):
        np.random.seed(42)
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=200),
            "league": ["PL"] * 200,
            "home_team": np.random.choice(["A", "B", "C", "D", "E", "F"], 200),
            "away_team": np.random.choice(["A", "B", "C", "D", "E", "F"], 200),
            "home_goals": np.random.randint(0, 4, 200),
            "away_goals": np.random.randint(0, 4, 200),
            "actual_outcome": np.random.choice([1, 2, 3], 200),
            "b365_home": np.random.uniform(1.5, 4.0, 200),
            "pin_close_home": np.random.uniform(1.5, 4.0, 200),
            "avg_home": np.random.uniform(1.5, 6.0, 200),
            "avg_draw": np.random.uniform(3.0, 4.5, 200),
            "avg_away": np.random.uniform(1.5, 6.0, 200),
        })

        strategy = NicheMarketStrategy()
        metrics = strategy.backtest(df, stake_pct=0.01)

        assert "total_bets" in metrics
        assert "win_rate" in metrics
        assert "roi" in metrics
        assert "profit_units" in metrics
        assert "avg_odds" in metrics

        # Verificar que ROI é um número finito
        assert np.isfinite(metrics["roi"])

    def test_backtest_uses_only_niche_matches(self):
        """O backtest deve usar apenas jogos onde avg_home > 2.5."""
        np.random.seed(42)
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=500),
            "league": ["PL"] * 500,
            "home_team": np.random.choice(["A", "B", "C", "D", "E", "F"], 500),
            "away_team": np.random.choice(["A", "B", "C", "D", "E", "F"], 500),
            "home_goals": np.random.randint(0, 4, 500),
            "away_goals": np.random.randint(0, 4, 500),
            "actual_outcome": np.random.choice([1, 2, 3], 500),
            "b365_home": np.random.uniform(1.5, 4.0, 500),
            "pin_close_home": np.random.uniform(1.5, 4.0, 500),
            "avg_home": np.concatenate([
                np.random.uniform(1.1, 2.4, 300),
                np.random.uniform(2.6, 5.0, 200),
            ]),
            "avg_draw": np.random.uniform(3.0, 4.5, 500),
            "avg_away": np.random.uniform(1.5, 6.0, 500),
        })

        strategy = NicheMarketStrategy()
        metrics = strategy.backtest(df, stake_pct=0.01)

        # Se há jogos de nicho suficientes, total_bets deve ser > 0
        niche_count = (df["avg_home"] > 2.5).sum()
        if niche_count >= 50:
            assert metrics["total_bets"] > 0
        else:
            assert metrics["total_bets"] == 0
