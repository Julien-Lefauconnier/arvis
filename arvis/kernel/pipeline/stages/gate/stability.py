# arvis/kernel/pipeline/stages/gate/stability.py

from __future__ import annotations

from typing import Any

from arvis.kernel.pipeline.gate_overrides import GateOverrides
from arvis.kernel.pipeline.stages.gate.models import StabilityEnvelope
from arvis.kernel.pipeline.stages.gate.trace_helpers import record_verdict_transition
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.stability.global_guard import GlobalStabilityGuard
from arvis.math.stability.validity_envelope import (
    build_validity_envelope as build_math_validity_envelope,
)
from arvis.math.switching.global_stability_observer import GlobalStabilityObserver


def apply_global_stability_policy(
    ctx: Any,
    verdict: LyapunovVerdict,
    global_safe: bool,
    stage_prefix: str = "global_policy",
) -> LyapunovVerdict:
    if global_safe:
        return verdict

    try:
        action = getattr(ctx, "global_stability_action", "confirm")
        reasons = ctx.extra.setdefault("fusion_reasons", [])

        if action != "ignore" and "global_instability_confirm" not in reasons:
            reasons.append("global_instability_confirm")

        if action == "confirm" and verdict == LyapunovVerdict.ABSTAIN:
            record_verdict_transition(
                ctx,
                stage=f"{stage_prefix}_confirm",
                before=verdict,
                after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                reason="global_instability_confirm",
            )
            return LyapunovVerdict.REQUIRE_CONFIRMATION

        if action == "abstain":
            if "global_instability_abstain" not in reasons:
                reasons.append("global_instability_abstain")
            return LyapunovVerdict.ABSTAIN

    except Exception:
        pass

    return verdict


def compute_global_stability(ctx: Any, delta_w: float | None) -> bool:
    history = list(getattr(ctx, "delta_w_history", []))
    if delta_w is not None:
        history.append(float(delta_w))
    ctx.delta_w_history = history

    global_safe = True
    try:
        guard = GlobalStabilityGuard()
        global_safe = guard.check(ctx.delta_w_history)
    except Exception:
        global_safe = True

    ctx.global_stability_safe = global_safe
    return global_safe


def compute_exponential_bound(ctx: Any) -> float | None:
    w_ratio = None
    try:
        metrics = getattr(ctx, "global_stability_metrics", None)
        if metrics is None:
            observer = GlobalStabilityObserver()
            metrics = observer.update(ctx)
            ctx.global_stability_metrics = metrics

        if metrics is not None:
            w_ratio = getattr(metrics, "ratio", None)
            if w_ratio is not None:
                ctx.w_bound_ratio = float(w_ratio)
    except Exception:
        pass
    return w_ratio


def build_stability_envelope(
    ctx: Any,
    global_safe: bool,
    switching_safe: bool,
    w_ratio: float | None,
    w_bound_tol: float,
    delta_w: float | None,
) -> StabilityEnvelope:
    reasons = []
    if not global_safe:
        reasons.append("global")
    if not switching_safe:
        reasons.append("switching")
    if w_ratio is not None and w_ratio > w_bound_tol:
        reasons.append("exponential_bound")

    hard_block = False
    hard_reason = "_".join(reasons) if reasons else None

    if hard_block:
        ctx.extra.setdefault("warnings", []).append(
            {
                "type": "hard_block",
                "reason": hard_reason,
            }
        )

    envelope = StabilityEnvelope(
        delta_w=delta_w,
        global_safe=global_safe,
        switching_safe=switching_safe,
        w_bound_ratio=w_ratio,
        hard_block=hard_block,
        hard_reason=hard_reason,
    )

    if not envelope.global_safe:
        ctx.extra["global_instability"] = True
        ctx.extra["global_instability_warning"] = True
    if not envelope.switching_safe:
        ctx.extra["switching_warning"] = True
        ctx.extra["switching_violation"] = True
    if envelope.w_bound_ratio is not None and envelope.w_bound_ratio > w_bound_tol:
        ctx.extra["exponential_bound_warning"] = True

    return envelope


def build_validity_envelope(
    ctx: Any,
    switching_safe: bool,
    w_ratio: float | None,
    w_bound_tol: float,
    adaptive_metrics: AdaptiveSnapshot | None,
) -> None:
    try:
        metrics = getattr(ctx, "global_stability_metrics", None)
        kappa_safe = not bool(
            metrics is not None and getattr(metrics, "kappa_violation", False)
        )
        projection_available = ctx.prev_lyap is not None or ctx.cur_lyap is not None
        exponential_safe = w_ratio is None or w_ratio <= w_bound_tol
        adaptive_band = ctx.extra.get("kappa_band")

        validity_envelope = build_math_validity_envelope(
            projection_available=bool(projection_available),
            switching_safe=bool(switching_safe),
            exponential_safe=bool(exponential_safe),
            kappa_safe=bool(kappa_safe),
            adaptive_available=bool(adaptive_metrics and adaptive_metrics.is_available),
            adaptive_band=adaptive_band,
        )
        ctx.validity_envelope = validity_envelope
        ctx.extra["validity_envelope"] = validity_envelope.__dict__.copy()
    except Exception:
        ctx.validity_envelope = None


def apply_validity_enforcement(
    ctx: Any,
    verdict: LyapunovVerdict,
    overrides: GateOverrides,
) -> LyapunovVerdict:
    try:
        validity = getattr(ctx, "validity_envelope", None)
        if overrides.disable_validity_envelope:
            validity = None
        if validity is not None and not validity.valid:
            ctx.extra.setdefault("fusion_reasons", []).append(
                f"validity_{validity.reason}"
            )
            if verdict == LyapunovVerdict.ALLOW:
                record_verdict_transition(
                    ctx,
                    stage="validity_envelope_enforcement",
                    before=verdict,
                    after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                    reason=f"validity_{validity.reason}",
                )
                verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
    except Exception:
        pass
    return verdict


__all__ = [
    "GlobalStabilityGuard",
    "build_validity_envelope",
    "apply_validity_enforcement",
    "apply_global_stability_policy",
    "compute_global_stability",
    "compute_exponential_bound",
    "build_stability_envelope",
]
