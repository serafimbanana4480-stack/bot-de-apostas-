import pytest
from src.risk.kelly import calculate_kelly_fraction, calculate_fractional_kelly
from src.engine.edge import calculate_clv, calculate_edge

def test_kelly_positive_edge():
    # 60% probability at 2.0 odds
    # Expected edge = 0.6 * 2.0 - 1 = 0.2 (20% edge)
    # b = 2.0 - 1 = 1
    # p = 0.6
    # q = 0.4
    # Kelly = (1 * 0.6 - 0.4) / 1 = 0.2
    
    kf = calculate_kelly_fraction(0.6, 2.0)
    assert kf == pytest.approx(0.2)
    
    fk = calculate_fractional_kelly(0.6, 2.0, 0.25)
    assert fk == pytest.approx(0.05)

def test_kelly_negative_edge():
    # 40% probability at 2.0 odds -> negative edge
    kf = calculate_kelly_fraction(0.4, 2.0)
    assert kf == 0.0

def test_calculate_clv():
    # Opening 2.0, closing 1.8 -> we got good value
    # CLV = (2.0 / 1.8) - 1 = 0.111 -> 11.1%
    clv = calculate_clv(2.0, 1.8)
    assert clv == pytest.approx(11.111, rel=1e-3)
    
    # Opening 2.0, closing 2.2 -> bad value
    clv_bad = calculate_clv(2.0, 2.2)
    assert clv_bad == pytest.approx(-9.09, rel=1e-2)

def test_calculate_edge():
    edge = calculate_edge(0.55, 2.0)
    # 0.55 * 2.0 = 1.1 -> 10% edge
    assert edge == pytest.approx(10.0)
