# tests/math/signals/test_signals.py

import pytest

from arvis.math.signals import RiskSignal, UncertaintySignal, DriftSignal


# ---------------------------------------------------------
# RiskSignal
# ---------------------------------------------------------

def test_risk_signal_clamps():
    assert RiskSignal(2.0).value == 1.0
    assert RiskSignal(-1.0).value == 0.0


def test_risk_signal_float_conversion():
    r = RiskSignal(0.3)
    assert float(r) == pytest.approx(0.3)


# ---------------------------------------------------------
# UncertaintySignal
# ---------------------------------------------------------

def test_uncertainty_signal_clamps():
    assert UncertaintySignal(2.0).value == 1.0
    assert UncertaintySignal(-1.0).value == 0.0


def test_uncertainty_signal_float():
    u = UncertaintySignal(0.7)
    assert float(u) == pytest.approx(0.7)


# ---------------------------------------------------------
# DriftSignal
# ---------------------------------------------------------

def test_drift_signal_clamps_and_abs():
    assert DriftSignal(2.0).value == 1.0
    assert DriftSignal(-0.5).value == 0.5


def test_drift_signal_float():
    d = DriftSignal(0.2)
    assert float(d) == pytest.approx(0.2)


# ---------------------------------------------------------
# Immutability
# ---------------------------------------------------------

def test_signals_are_immutable():
    r = RiskSignal(0.5)

    with pytest.raises(Exception):
        r.value = 0.1