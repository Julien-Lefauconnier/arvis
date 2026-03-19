# tests/math/signals/test_signals.py

import pytest

from arvis.math.signals import (
    RiskSignal,
    UncertaintySignal,
    DriftSignal,
    StabilitySignal,
    ConfidenceSignal,
    ForecastSignal,
    SymbolicDriftSignal,
    ConflictSignal,
)


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


def test_stability_signal_float():
    s = StabilitySignal(0.9)
    assert float(s) == 0.9


def test_confidence_signal_float():
    s = ConfidenceSignal(0.7)
    assert float(s) == 0.7


def test_forecast_signal_float():
    s = ForecastSignal(0.6)
    assert float(s) == 0.6


def test_symbolic_drift_signal_float():
    s = SymbolicDriftSignal(0.4)
    assert float(s) == 0.4


def test_conflict_signal_level():
    s = ConflictSignal(global_score=0.8, decisional=0.9)
    assert s.level() == 0.8


def test_conflict_signal_is_zero():
    s = ConflictSignal()
    assert s.is_zero() is True


def test_conflict_signal_is_max():
    s = ConflictSignal(global_score=1.0)
    assert s.is_max() is True


def test_conflict_signal_clamps_values():
    s = ConflictSignal(
        global_score=2.0,
        epistemic=-1.0,
        decisional=0.5,
        temporal=3.0,
        ethical=-3.0,
    )
    assert s.global_score == 1.0
    assert s.epistemic == 0.0
    assert s.decisional == 0.5
    assert s.temporal == 1.0
    assert s.ethical == 0.0