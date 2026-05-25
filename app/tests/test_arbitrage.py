import pytest
import numpy as np
import pandas as pd

from scripts.run_arbitrage import (
    implied_probability,
    calculate_arbitrage_stakes,
    run_arbitrage_detection,
)


class TestImpliedProbability:
    def test_basic_odds(self):
        assert implied_probability(2.0) == pytest.approx(0.5)
        assert implied_probability(4.0) == pytest.approx(0.25)

    def test_invalid_odds(self):
        assert implied_probability(1.0) == 1.0
        assert implied_probability(0.5) == 1.0
        assert implied_probability(None) == 1.0


class TestArbitrageMath:
    def test_guaranteed_profit_when_implied_lt_100(self):
        """
        Se a soma das probabilidades implícitas < 100%,
        o lucro é garantido independentemente do resultado.
        """
        odds_home = 2.20
        odds_draw = 3.40
        odds_away = 4.50

        bankroll = 1000.0
        result = calculate_arbitrage_stakes(odds_home, odds_draw, odds_away, bankroll)

        assert result is not None
        assert result["total_implied"] < 1.0
        assert result["profit_pct"] > 0.0

        # Verificar payout igual em todos os resultados
        payout_home = result["stake_home"] * odds_home
        payout_draw = result["stake_draw"] * odds_draw
        payout_away = result["stake_away"] * odds_away

        assert payout_home == pytest.approx(payout_draw, rel=1e-3)
        assert payout_draw == pytest.approx(payout_away, rel=1e-3)

    def test_stakes_sum_to_bankroll(self):
        """A soma das stakes deve ser igual ao bankroll."""
        odds_home = 2.50
        odds_draw = 3.50
        odds_away = 4.50
        bankroll = 500.0

        result = calculate_arbitrage_stakes(odds_home, odds_draw, odds_away, bankroll)
        assert result is not None
        assert result["stake_total"] == pytest.approx(bankroll, rel=1e-3)
        assert result["stake_home"] + result["stake_draw"] + result["stake_away"] == pytest.approx(
            bankroll, rel=1e-3
        )

    def test_no_arbitrage_when_implied_gte_100(self):
        """Se a soma das probabilidades implícitas >= 100%, não há arbitragem."""
        odds_home = 1.50
        odds_draw = 3.50
        odds_away = 4.50

        result = calculate_arbitrage_stakes(odds_home, odds_draw, odds_away, bankroll=100.0)
        assert result is None

    def test_profit_calculation(self):
        """O lucro deve ser igual ao payout menos o bankroll."""
        odds_home = 2.50
        odds_draw = 3.20
        odds_away = 3.80
        bankroll = 1000.0

        result = calculate_arbitrage_stakes(odds_home, odds_draw, odds_away, bankroll)
        assert result is not None
        assert result["profit"] == pytest.approx(result["payout"] - bankroll, rel=1e-3)
        assert result["profit_pct"] == pytest.approx((result["payout"] / bankroll - 1.0) * 100, rel=1e-3)


class TestArbitrageDetection:
    def test_detects_arbitrage_opportunity(self):
        """Deve detetar uma arbitragem óbvia entre bookmakers diferentes."""
        df = pd.DataFrame({
            "match_id": ["m1"],
            "date": ["2024-01-01"],
            "home_team": ["Team A"],
            "away_team": ["Team B"],
            "league": ["Test League"],
            "b365_home": [2.10],
            "b365_draw": [3.20],
            "b365_away": [4.00],
            "pin_close_home": [1.80],
            "pin_close_draw": [3.60],
            "pin_close_away": [5.00],
            "max_home": [2.20],
            "max_draw": [3.50],
            "max_away": [4.50],
        })

        opportunities = run_arbitrage_detection(df, bankroll=1000.0, min_profit_pct=0.5)
        assert not opportunities.empty
        # A melhor combinação deve usar max_home, pinnacle_draw, pinnacle_away
        row = opportunities.iloc[0]
        assert row["home_bookmaker"] == "max"
        assert row["draw_bookmaker"] == "pinnacle"
        assert row["away_bookmaker"] == "pinnacle"

    def test_no_arbitrage_on_identical_odds(self):
        """Se todos os bookmakers tiverem odds idênticas com overround, não há arbitragem."""
        df = pd.DataFrame({
            "match_id": ["m1"],
            "date": ["2024-01-01"],
            "home_team": ["Team A"],
            "away_team": ["Team B"],
            "league": ["Test League"],
            "b365_home": [1.90],
            "b365_draw": [3.40],
            "b365_away": [4.20],
            "pin_close_home": [1.90],
            "pin_close_draw": [3.40],
            "pin_close_away": [4.20],
            "max_home": [1.90],
            "max_draw": [3.40],
            "max_away": [4.20],
        })

        opportunities = run_arbitrage_detection(df, bankroll=1000.0, min_profit_pct=0.5)
        assert opportunities.empty

    def test_respects_min_profit_filter(self):
        """Deve respeitar o filtro de lucro mínimo."""
        df = pd.DataFrame({
            "match_id": ["m1"],
            "date": ["2024-01-01"],
            "home_team": ["Team A"],
            "away_team": ["Team B"],
            "league": ["Test League"],
            "b365_home": [2.50],
            "b365_draw": [3.50],
            "b365_away": [3.00],
            "pin_close_home": [2.50],
            "pin_close_draw": [3.50],
            "pin_close_away": [3.00],
            "max_home": [2.50],
            "max_draw": [3.50],
            "max_away": [3.00],
        })

        # Com min_profit muito alto, não deve encontrar nada (ou pouco)
        opportunities = run_arbitrage_detection(df, bankroll=1000.0, min_profit_pct=50.0)
        assert opportunities.empty
