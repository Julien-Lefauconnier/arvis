# arvis/math/decision/multiaxial_fusion.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


@dataclass(frozen=True)
class MultiaxialInputs:
    """Inputs of the assessment-phase fusion.

    Pruned (audit G3, decision D1, 2026-08): the ``use_composite`` and
    ``global_action`` knobs and their branches were exercised only by
    unit tests: production never wired them, so the composite axis
    could never fire and the global axis always took its neutral path.
    One of those dead branches even relaxed REQUIRE_CONFIRMATION to
    ALLOW, in contradiction with the verdict-strictness order. Global
    stability enforcement lives in the policy layer
    (``apply_gate_policy`` and the gate stage's global-stability
    policy), not here.
    """

    fast_verdict: LyapunovVerdict
    switching_safe: bool


@dataclass(frozen=True)
class MultiaxialFusionResult:
    verdict: LyapunovVerdict
    reasons: list[str]


def multiaxial_fusion(inputs: MultiaxialInputs) -> MultiaxialFusionResult:
    """Observation-only fusion of the assessment axes.

    The verdict passes through unchanged: every enforcement decision
    (global stability policy, strict veto, recovery relaxation) belongs
    to the policy layer, where it is traced and provenance-checked.
    This function only records what the non-decisive axes observed
    (today: an unsafe switching regime).
    """
    reasons: list[str] = []

    if not inputs.switching_safe:
        reasons.append("switching_unsafe_monitoring")

    return MultiaxialFusionResult(
        verdict=inputs.fast_verdict,
        reasons=reasons,
    )
