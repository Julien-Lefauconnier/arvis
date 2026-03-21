# arvis/math/decision/multiaxial_fusion.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


@dataclass(frozen=True)
class MultiaxialInputs:
    fast_verdict: LyapunovVerdict
    delta_w: float | None
    switching_safe: bool
    global_safe: bool
    use_composite: bool = False
    global_action: str = "ignore"   # "ignore" | "confirm" | "abstain"


@dataclass(frozen=True)
class MultiaxialFusionResult:
    verdict: LyapunovVerdict
    reasons: list[str]


def _apply_composite(
    verdict: LyapunovVerdict,
    delta_w: float | None,
    use_composite: bool,
    reasons: list[str],
) -> LyapunovVerdict:
    if not use_composite or delta_w is None:
        return verdict

    if delta_w > 1e-6:
        reasons.append("composite_positive_delta_w")
        return LyapunovVerdict.REQUIRE_CONFIRMATION

    if delta_w < -1e-6 and verdict != LyapunovVerdict.ABSTAIN:
        reasons.append("composite_negative_delta_w")
        return LyapunovVerdict.ALLOW

    return verdict


def _apply_global_policy(
    verdict: LyapunovVerdict,
    global_safe: bool,
    global_action: str,
    reasons: list[str],
) -> LyapunovVerdict:
    if global_safe:
        return verdict

    if global_action == "confirm":
        reasons.append("global_instability_confirm")
        reasons.append("global_stability_enforced:confirm")
        return LyapunovVerdict.REQUIRE_CONFIRMATION

    if global_action == "abstain":
        reasons.append("global_instability_abstain")
        reasons.append("global_stability_enforced:abstain")
        return LyapunovVerdict.ABSTAIN

    return verdict


def _apply_switching_monitoring(
    verdict: LyapunovVerdict,
    switching_safe: bool,
    reasons: list[str],
) -> LyapunovVerdict:
    # Soft constraint only: observability, no override
    if not switching_safe:
        reasons.append("switching_unsafe_monitoring")
    return verdict


def multiaxial_fusion(inputs: MultiaxialInputs) -> MultiaxialFusionResult:
    reasons: list[str] = []
    verdict = inputs.fast_verdict

    verdict = _apply_composite(
        verdict=verdict,
        delta_w=inputs.delta_w,
        use_composite=inputs.use_composite,
        reasons=reasons,
    )

    verdict = _apply_global_policy(
        verdict=verdict,
        global_safe=inputs.global_safe,
        global_action=inputs.global_action,
        reasons=reasons,
    )

    verdict = _apply_switching_monitoring(
        verdict=verdict,
        switching_safe=inputs.switching_safe,
        reasons=reasons,
    )

    return MultiaxialFusionResult(
        verdict=verdict,
        reasons=reasons,
    )