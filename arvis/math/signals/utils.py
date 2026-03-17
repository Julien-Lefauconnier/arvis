# arvis/math/signals/utils.py

from __future__ import annotations

from typing import Union

from arvis.math.signals import RiskSignal, UncertaintySignal, DriftSignal


SignalLike = Union[
    float,
    RiskSignal,
    UncertaintySignal,
    DriftSignal,
]


def signal_value(x: SignalLike | None, default: float = 0.0) -> float:
    """
    Safe extraction of scalar value from signal or float.

    ZKCS-safe:
    - no inspection
    - no metadata leak
    """
    if x is None:
        return default

    if isinstance(x, (RiskSignal, UncertaintySignal, DriftSignal)):
        return float(x)

    return float(x)