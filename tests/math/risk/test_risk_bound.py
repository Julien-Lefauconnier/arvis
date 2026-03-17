# tests/math/risk/test_risk_bound.py

from arvis.math.risk.risk_bound import HoeffdingRiskBound


def test_hoeffding_bound_positive():

    bound = HoeffdingRiskBound()

    # simulate events
    for _ in range(50):
        snapshot = bound.push(False)

    assert snapshot.n == 50
    assert snapshot.violations == 0
    assert snapshot.p_hat == 0.0
    assert snapshot.p_ucb >= 0.0

def test_hoeffding_detects_risk():

    bound = HoeffdingRiskBound()

    for _ in range(20):
        snapshot = bound.push(True)

    assert snapshot.violations == 20
    assert snapshot.p_hat == 1.0
    assert snapshot.p_ucb <= 1.0