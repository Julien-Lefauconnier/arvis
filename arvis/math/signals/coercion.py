# arvis/math/signals/coercion.py

from __future__ import annotations

from typing import Any

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
# Core coercion
# ============================================================


def to_float(value: Any, default: float = 0.0) -> float:
    """
    Safe float coercion.

    ZKCS-safe:
    - no metadata inspection
    - no branching on hidden state
    """
    try:
        if value is None:
            return float(default)

        if isinstance(
            value,
            (
                RiskSignal,
                UncertaintySignal,
                DriftSignal,
                StabilitySignal,
                ConfidenceSignal,
                ForecastSignal,
                SymbolicDriftSignal,
                ConflictSignal,
            ),
        ):
            return float(value)

        return float(value)
    except Exception:
        return float(default)


# ============================================================
# Signal constructors
# ============================================================


def to_risk(value: Any, default: float = 0.0) -> RiskSignal:
    if isinstance(value, RiskSignal):
        return value
    return RiskSignal(to_float(value, default))

def to_uncertainty(value: Any, default: float = 0.0) -> UncertaintySignal:
    if isinstance(value, UncertaintySignal):
        return value
    return UncertaintySignal(to_float(value, default))


def to_drift(value: Any, default: float = 0.0) -> DriftSignal:
    if isinstance(value, DriftSignal):
        return value
    return DriftSignal(to_float(value, default))

def to_stability(value: Any, default: float = 0.0) -> StabilitySignal:
    if isinstance(value, StabilitySignal):
        return value
    return StabilitySignal(to_float(value, default))


def to_confidence(value: Any, default: float = 0.0) -> ConfidenceSignal:
    if isinstance(value, ConfidenceSignal):
        return value
    return ConfidenceSignal(to_float(value, default))


def to_forecast(value: Any, default: float = 0.0) -> ForecastSignal:
    if isinstance(value, ForecastSignal):
        return value
    return ForecastSignal(to_float(value, default))


def to_symbolic_drift(value: Any, default: float = 0.0) -> SymbolicDriftSignal:
    if isinstance(value, SymbolicDriftSignal):
        return value
    return SymbolicDriftSignal(to_float(value, default))