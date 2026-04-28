# arvis/math/__init__.py
"""
Mathematical primitives for stability-aware cognition.

This module exposes the public mathematical API of ARVIS.
"""

# Lyapunov dynamics
from .lyapunov.lyapunov import (
    LyapunovState,
    LyapunovWeights,
    lyapunov_value,
    lyapunov_delta,
)

# Core utilities
from .core.normalization import (
    clamp,
    clamp01,
    normalize_weights,
)

from .core.change_budget import ChangeBudget

# Risk estimation
from .risk.risk_bound import (
    HoeffdingRiskBound,
    RiskBoundSnapshot,
)

__all__ = [
    "LyapunovState",
    "LyapunovWeights",
    "lyapunov_value",
    "lyapunov_delta",
    "clamp",
    "clamp01",
    "normalize_weights",
    "HoeffdingRiskBound",
    "RiskBoundSnapshot",
    "ChangeBudget",
]
