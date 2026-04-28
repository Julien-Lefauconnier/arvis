# tests/math/signals/test_coercion_full.py


from arvis.math.signals.coercion import (
    to_float,
    to_risk,
    to_uncertainty,
    to_drift,
    to_stability,
    to_confidence,
    to_forecast,
    to_symbolic_drift,
)

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


# ============================================================
# to_float
# ============================================================


def test_to_float_none():
    assert to_float(None) == 0.0


def test_to_float_basic_number():
    assert to_float(0.5) == 0.5
    assert to_float(1) == 1.0


def test_to_float_string_number():
    assert to_float("0.3") == 0.3


def test_to_float_invalid_returns_default():
    class Bad:
        pass

    assert to_float(Bad(), default=0.42) == 0.42


def test_to_float_signal_conversion():
    s = RiskSignal(0.7)
    assert to_float(s) == float(s)


def test_to_float_conflict_signal():
    s = ConflictSignal.from_scalar(0.6)
    assert to_float(s) == float(s)


# ============================================================
# Passthrough behavior
# ============================================================


def test_to_risk_passthrough():
    s = RiskSignal(0.2)
    assert to_risk(s) is s


def test_to_uncertainty_passthrough():
    s = UncertaintySignal(0.3)
    assert to_uncertainty(s) is s


def test_to_drift_passthrough():
    s = DriftSignal(0.4)
    assert to_drift(s) is s


def test_to_stability_passthrough():
    s = StabilitySignal(0.5)
    assert to_stability(s) is s


def test_to_confidence_passthrough():
    s = ConfidenceSignal(0.6)
    assert to_confidence(s) is s


def test_to_forecast_passthrough():
    s = ForecastSignal(0.7)
    assert to_forecast(s) is s


def test_to_symbolic_drift_passthrough():
    s = SymbolicDriftSignal(0.8)
    assert to_symbolic_drift(s) is s


# ============================================================
# Conversion behavior
# ============================================================


def test_to_risk_from_float():
    s = to_risk(0.2)
    assert isinstance(s, RiskSignal)
    assert float(s) == 0.2


def test_to_uncertainty_from_float():
    s = to_uncertainty(0.3)
    assert isinstance(s, UncertaintySignal)
    assert float(s) == 0.3


def test_to_drift_from_float():
    s = to_drift(0.4)
    assert isinstance(s, DriftSignal)
    assert float(s) == 0.4


def test_to_stability_from_float():
    s = to_stability(0.5)
    assert isinstance(s, StabilitySignal)
    assert float(s) == 0.5


def test_to_confidence_from_float():
    s = to_confidence(0.6)
    assert isinstance(s, ConfidenceSignal)
    assert float(s) == 0.6


def test_to_forecast_from_float():
    s = to_forecast(0.7)
    assert isinstance(s, ForecastSignal)
    assert float(s) == 0.7


def test_to_symbolic_drift_from_float():
    s = to_symbolic_drift(0.8)
    assert isinstance(s, SymbolicDriftSignal)
    assert float(s) == 0.8


# ============================================================
# Default fallback
# ============================================================


def test_to_risk_invalid_uses_default():
    s = to_risk("invalid", default=0.9)
    assert float(s) == 0.9


def test_to_uncertainty_none_default():
    s = to_uncertainty(None, default=0.1)
    assert float(s) == 0.1


# ============================================================
# Edge: exception safety
# ============================================================


def test_to_float_exception_safety():
    class Exploding:
        def __float__(self):
            raise RuntimeError()

    assert to_float(Exploding(), default=0.33) == 0.33
