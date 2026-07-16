# arvis/kernel/pipeline/stages/gate/stability.py

from __future__ import annotations

from typing import Any

from arvis.errors.manager import ErrorManager
from arvis.errors.pipeline import PipelineStageDegradedError
from arvis.kernel.pipeline.gate_overrides import GateOverrides
from arvis.kernel.pipeline.stages.gate.models import StabilityEnvelope
from arvis.kernel.pipeline.stages.gate.trace_helpers import (
    GLOBAL_STABILITY_PROVENANCE,
    record_verdict_transition,
    verdict_provenance,
)
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.lyapunov.verdict_order import max_strictness
from arvis.math.stability.global_guard import GlobalStabilityGuard
from arvis.math.stability.hard_block_policy import (
    HARD_BLOCK_TABLE_VERSION,
    resolve_hard_block,
)
from arvis.math.stability.validity_envelope import (
    build_validity_envelope as build_math_validity_envelope,
)
from arvis.math.switching.global_stability_observer import GlobalStabilityObserver

# Provenance labels whose ABSTAIN the confirm action may reinterpret:
# only an abstention produced by the global stability axis itself.
_RELAXABLE_ABSTAIN_PROVENANCE = frozenset({GLOBAL_STABILITY_PROVENANCE})


def apply_global_stability_policy(
    ctx: Any,
    verdict: LyapunovVerdict,
    global_safe: bool,
    stage_prefix: str = "global_policy",
) -> LyapunovVerdict:
    """Global stability policy, monotone (audit F-001, lot A2).

    Under global instability the configured action contributes a
    requirement composed through max_strictness: "confirm" hardens up
    to REQUIRE_CONFIRMATION, "abstain" hardens to ABSTAIN, "ignore"
    leaves the verdict untouched.

    The single sanctioned relaxation is provenance-checked: an incoming
    ABSTAIN produced by the global stability axis itself may be
    reinterpreted as REQUIRE_CONFIRMATION under action="confirm" (the
    traced product transition). An ABSTAIN of unknown or foreign
    provenance (projection, kappa, memory, adaptive, ...) is never
    relaxed; unknown provenance fails closed.
    """
    if ctx.extra.get("_hard_adaptive_veto", False):
        return verdict

    if global_safe:
        return verdict

    try:
        action = getattr(ctx, "global_stability_action", "confirm")
        reasons = ctx.extra.setdefault("fusion_reasons", [])

        if action != "ignore" and "global_instability_confirm" not in reasons:
            reasons.append("global_instability_confirm")

        if action == "confirm":
            if verdict == LyapunovVerdict.ABSTAIN:
                provenance = verdict_provenance(ctx, LyapunovVerdict.ABSTAIN)
                relaxable = provenance in _RELAXABLE_ABSTAIN_PROVENANCE and not (
                    ctx.extra.get("kappa_hard_block")
                )
                if relaxable:
                    record_verdict_transition(
                        ctx,
                        stage=f"{stage_prefix}_confirm",
                        before=verdict,
                        after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                        reason="global_instability_confirm",
                    )
                    return LyapunovVerdict.REQUIRE_CONFIRMATION
                record_verdict_transition(
                    ctx,
                    stage=f"{stage_prefix}_confirm_denied",
                    before=verdict,
                    after=verdict,
                    reason="abstain_provenance_not_global",
                )
                return verdict

            hardened = max_strictness(verdict, LyapunovVerdict.REQUIRE_CONFIRMATION)
            if hardened != verdict:
                record_verdict_transition(
                    ctx,
                    stage=f"{stage_prefix}_confirm",
                    before=verdict,
                    after=hardened,
                    reason="global_instability_confirm",
                )
            return hardened

        if action == "abstain":
            if "global_instability_abstain" not in reasons:
                reasons.append("global_instability_abstain")
            if verdict != LyapunovVerdict.ABSTAIN:
                record_verdict_transition(
                    ctx,
                    stage=f"{stage_prefix}_abstain",
                    before=verdict,
                    after=LyapunovVerdict.ABSTAIN,
                    reason="global_instability_abstain",
                )
            return LyapunovVerdict.ABSTAIN

    except Exception as exc:
        ErrorManager.attach(
            ctx,
            PipelineStageDegradedError(
                message=str(exc),
                details={
                    "component": "global_stability_policy",
                    "exception_type": type(exc).__name__,
                },
            ),
        )
        # F-002: a failing guarantee mechanism can never relax; an
        # exception inside the gate forces ABSTAIN (fail-closed).
        record_verdict_transition(
            ctx,
            stage=f"{stage_prefix}_fail_closed",
            before=verdict,
            after=LyapunovVerdict.ABSTAIN,
            reason="gate_exception",
        )
        return LyapunovVerdict.ABSTAIN

    return verdict


def compute_global_stability(ctx: Any, delta_w: float | None) -> bool:
    scientific = getattr(ctx, "scientific", None)

    if scientific is not None:
        history = list(scientific.composite.delta_w_history)
    else:
        history = list(getattr(ctx, "delta_w_history", []))
    if delta_w is not None:
        history.append(float(delta_w))
    if scientific is not None:
        scientific.composite.delta_w_history = history

    ctx.delta_w_history = history

    global_safe = True
    try:
        guard = GlobalStabilityGuard()
        global_safe = guard.check(history)
    except Exception as exc:
        # F-002: unknown stability is not safe (fail-closed).
        global_safe = False
        ErrorManager.attach(
            ctx,
            PipelineStageDegradedError(
                message=str(exc),
                details={
                    "component": "compute_global_stability",
                    "fallback": "global_safe=False (fail-closed)",
                    "exception_type": type(exc).__name__,
                },
            ),
        )

    ctx.global_stability_safe = global_safe
    return global_safe


def compute_exponential_bound(ctx: Any) -> float | None:
    w_ratio = None
    try:
        scientific = getattr(ctx, "scientific", None)

        if scientific is not None:
            metrics = scientific.adaptive.global_stability_metrics
        else:
            metrics = getattr(ctx, "global_stability_metrics", None)
        if metrics is None:
            observer = GlobalStabilityObserver()
            metrics = observer.update(ctx)
            if scientific is not None:
                scientific.adaptive.global_stability_metrics = metrics

            ctx.global_stability_metrics = metrics

        if metrics is not None:
            w_ratio = getattr(metrics, "ratio", None)
            if w_ratio is not None:
                ctx.w_bound_ratio = float(w_ratio)
    except Exception as exc:
        ErrorManager.attach(
            ctx,
            PipelineStageDegradedError(
                message=str(exc),
                details={
                    "component": "global_stability_policy",
                    "exception_type": type(exc).__name__,
                },
            ),
        )
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

    # F-003: hard_block is resolved by the versioned severity table
    # instead of being hardcoded (unknown reasons fail closed).
    hard_block, hard_reason = resolve_hard_block(reasons)
    ctx.extra["hard_block_table_version"] = HARD_BLOCK_TABLE_VERSION

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
        scientific = getattr(ctx, "scientific", None)

        if scientific is not None:
            metrics = scientific.adaptive.global_stability_metrics
        else:
            metrics = getattr(ctx, "global_stability_metrics", None)
        kappa_safe = not bool(
            metrics is not None and getattr(metrics, "kappa_violation", False)
        )
        projection_ctx = getattr(ctx, "projection", None)

        if projection_ctx is not None:
            projection_certificate = getattr(
                projection_ctx,
                "certificate",
                None,
            )
        else:
            projection_certificate = getattr(
                ctx,
                "projection_certificate",
                None,
            )

        projection_available = projection_certificate is not None

        projection_domain_valid = bool(
            getattr(
                projection_certificate,
                "domain_valid",
                False,
            )
        )

        projection_safe = bool(
            getattr(
                projection_certificate,
                "is_projection_safe",
                True,
            )
        )

        projection_available = (
            projection_available and projection_domain_valid and projection_safe
        )
        exponential_safe = w_ratio is None or w_ratio <= w_bound_tol
        adaptive_band = ctx.extra.get("kappa_band")

        # -----------------------------------------------------
        # Switching safety envelope mode (audit F-004, lot A4).
        #
        # "soft" (default): switching stays observability only and
        # does not invalidate the mathematical validity envelope.
        # Any other value feeds the measured switching safety into
        # the envelope, so unknown modes fail closed into
        # enforcement.
        # -----------------------------------------------------

        switching_mode = getattr(ctx, "switching_envelope_mode", "soft")
        effective_switching_safe = (
            True if switching_mode == "soft" else bool(switching_safe)
        )

        validity_envelope = build_math_validity_envelope(
            projection_available=bool(projection_available),
            switching_safe=bool(effective_switching_safe),
            exponential_safe=bool(exponential_safe),
            kappa_safe=bool(kappa_safe),
            adaptive_available=bool(adaptive_metrics and adaptive_metrics.is_available),
            adaptive_band=adaptive_band,
        )
        if scientific is not None:
            scientific.adaptive.validity_envelope = validity_envelope

        ctx.validity_envelope = validity_envelope

        # -----------------------------------------------------
        # Soft switching observability
        # -----------------------------------------------------

        if not switching_safe:
            ctx.extra["switching_warning"] = True
            ctx.extra.setdefault("fusion_reasons", []).append("switching_soft_warning")

        ctx.extra["validity_envelope"] = validity_envelope.__dict__.copy()
    except Exception as exc:
        if scientific is not None:
            scientific.adaptive.validity_envelope = None

        ctx.validity_envelope = None

        ErrorManager.attach(
            ctx,
            PipelineStageDegradedError(
                message=str(exc),
                details={
                    "component": "build_validity_envelope",
                    "fallback": "validity_envelope=None",
                    "exception_type": type(exc).__name__,
                },
            ),
        )


def apply_validity_enforcement(
    ctx: Any,
    verdict: LyapunovVerdict,
    overrides: GateOverrides,
) -> LyapunovVerdict:
    try:
        scientific = getattr(ctx, "scientific", None)

        if scientific is not None:
            validity = scientific.adaptive.validity_envelope
        else:
            validity = getattr(ctx, "validity_envelope", None)
        requires_enforcement = bool(
            validity is not None
            and (
                getattr(validity, "hard_block", False)
                or not bool(getattr(validity, "valid", True))
            )
        )

        if validity is not None and requires_enforcement:
            reason_code = f"validity_{validity.reason}"

            fusion_reasons = ctx.extra.setdefault(
                "fusion_reasons",
                [],
            )

            if reason_code not in fusion_reasons:
                fusion_reasons.append(reason_code)

            if verdict == LyapunovVerdict.ALLOW:
                record_verdict_transition(
                    ctx,
                    stage="validity_envelope_enforcement",
                    before=verdict,
                    after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                    reason=reason_code,
                )
                verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
    except Exception as exc:
        ErrorManager.attach(
            ctx,
            PipelineStageDegradedError(
                message=str(exc),
                details={
                    "component": "global_stability_policy",
                    "exception_type": type(exc).__name__,
                },
            ),
        )
        # F-002: a failing guarantee mechanism can never relax; an
        # exception inside the gate forces ABSTAIN (fail-closed).
        record_verdict_transition(
            ctx,
            stage="validity_gate_fail_closed",
            before=verdict,
            after=LyapunovVerdict.ABSTAIN,
            reason="gate_exception",
        )
        return LyapunovVerdict.ABSTAIN
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
