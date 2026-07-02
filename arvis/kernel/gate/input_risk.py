# arvis/kernel/gate/input_risk.py
"""
Governed policy for an explicit input risk scalar.

When a caller provides a direct top-level risk assertion in the cognitive input
(``{"risk": 0.9}``), that is a first-class risk statement and is gated by a
small, governed three-band policy. This is intentionally separate from the
trajectory-based Lyapunov machinery: a static risk scalar has no trajectory, so
it is graded by thresholds rather than by energy dynamics.

Only a numeric *top-level* ``risk`` key qualifies. Nested ``numeric_signals``
(used by other layers and by compliance scenarios) are deliberately NOT read
here, so this policy never interferes with structured/observational inputs.
"""

from __future__ import annotations

from typing import Any

from arvis.math.core.normalization import clamp01

# Governed thresholds (documented, tunable).
#   risk < CONFIRM            -> ALLOW
#   CONFIRM <= risk < ABSTAIN -> REQUIRE_CONFIRMATION
#   risk >= ABSTAIN           -> ABSTAIN
INPUT_RISK_CONFIRM_THRESHOLD: float = 0.4
INPUT_RISK_ABSTAIN_THRESHOLD: float = 0.8


def read_input_risk(cognitive_input: Any) -> float | None:
    """Return an explicit top-level risk scalar in [0, 1], or None.

    Accepts only a numeric top-level ``risk`` key. Booleans are rejected
    (``bool`` is an ``int`` subclass). Nested signals are not consulted.
    """
    if not isinstance(cognitive_input, dict):
        return None

    value = cognitive_input.get("risk")

    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return clamp01(float(value))

    return None


def resolve_input_risk_verdict(risk: float) -> str:
    """Map an input risk scalar to a governed verdict string.

    Returns one of: ``"allow"``, ``"require_confirmation"``, ``"abstain"``.
    """
    if risk >= INPUT_RISK_ABSTAIN_THRESHOLD:
        return "abstain"
    if risk >= INPUT_RISK_CONFIRM_THRESHOLD:
        return "require_confirmation"
    return "allow"
