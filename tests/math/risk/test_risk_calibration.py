# tests/math/risk/test_risk_calibration.py

from arvis.math.risk.risk_calibration import (
    calibrate_risk,
    probabilistic_or,
    calibrated_or_fusion,
    DEFAULT_RISK_CALIBRATION,
)


def test_calibrate_risk_bounds():
    p = calibrate_risk(0.5, theta=0.5, k=4)

    assert 0 < p < 1


def test_probabilistic_or():
    result = probabilistic_or([0.2, 0.3])

    assert 0 <= result <= 1


def test_calibrated_or_fusion():
    sources = [
        ("mh", 0.5),
        ("wm", 0.6),
    ]

    r = calibrated_or_fusion(
        sources,
        calibration=DEFAULT_RISK_CALIBRATION,
    )

    assert 0 <= r <= 1
