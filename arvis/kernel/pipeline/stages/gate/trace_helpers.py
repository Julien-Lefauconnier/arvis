# arvis/kernel/pipeline/stages/gate/trace_helpers.py

from __future__ import annotations

from typing import Any

from arvis.cognition.conflict.conflict_confirmation import (
    requires_conflict_confirmation,
)
from arvis.errors.manager import ErrorManager
from arvis.errors.pipeline import PipelineStageDegradedError
from arvis.kernel.pipeline.context.journal_context import (
    fusion_reasons_of,
    verdict_provenance_of,
    verdict_transition_trace_of,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.lyapunov.verdict_order import is_relaxation, strictness

VERDICT_PROVENANCE_KEY = "verdict_provenance"

# Provenance labels for verdicts born in the assessment phase (kernel,
# fusion, recovery), attributed by seed_verdict_provenance before the
# enforcement gates run.
GLOBAL_STABILITY_PROVENANCE = "global_stability_fusion"
ASSESSMENT_PROVENANCE = "stability_assessment"

# Fusion reason that used to mark an ABSTAIN produced by the global
# stability axis of the multiaxial fusion. That axis was pruned (audit
# G3 / D1, 2026-08): the fusion is observation-only and no production
# code emits this marker anymore. The constant stays so that traces and
# provenance checks keep recognizing it in recorded histories.
_GLOBAL_ABSTAIN_MARKER = "global_stability_enforced:abstain"


def record_verdict_transition(
    ctx: Any,
    stage: str,
    before: LyapunovVerdict,
    after: LyapunovVerdict,
    reason: str,
) -> None:
    trace = verdict_transition_trace_of(ctx)

    trace.append(
        {"stage": stage, "before": str(before), "after": str(after), "reason": reason}
    )
    if strictness(after) > strictness(before):
        ledger = verdict_provenance_of(ctx)
        ledger[after.name] = stage
    ctx.extra["last_verdict_source"] = stage
    ctx.extra["last_verdict_reason"] = reason


def verdict_provenance(ctx: Any, verdict: LyapunovVerdict) -> str | None:
    """Stage that produced the current strictness level, if known.

    Consumers must treat a missing entry as unknown and fail closed
    (no relaxation).
    """
    ledger = verdict_provenance_of(ctx)
    if not isinstance(ledger, dict):
        return None
    value = ledger.get(verdict.name)
    return value if isinstance(value, str) else None


def seed_verdict_provenance(ctx: Any, verdict: LyapunovVerdict) -> None:
    """Attribute the assessment-phase verdict before enforcement runs.

    A verdict reaching the enforcement phase without a traced hardening
    was produced by the stability assessment (kernel, fusion, recovery).
    An ABSTAIN carrying the fusion marker of the global stability axis
    is attributed to that axis; anything else to the assessment at
    large. Traced hardenings are more precise and are never overwritten.
    """
    extra = getattr(ctx, "extra", None)
    if not isinstance(extra, dict):
        return
    if verdict_provenance(ctx, verdict) is not None:
        return
    reasons = fusion_reasons_of(ctx)
    reason_list = reasons if isinstance(reasons, list) else []
    if verdict == LyapunovVerdict.ABSTAIN and _GLOBAL_ABSTAIN_MARKER in reason_list:
        source = GLOBAL_STABILITY_PROVENANCE
    else:
        source = ASSESSMENT_PROVENANCE
    ledger = verdict_provenance_of(ctx)
    ledger[verdict.name] = source


def enforce_monotone(
    ctx: Any,
    stage: str,
    before: LyapunovVerdict,
    after: LyapunovVerdict,
) -> LyapunovVerdict:
    """Monotone guard around an enforcement gate (audit F-001).

    A relaxation attempt is blocked, traced, and the stricter verdict
    is kept. Hardenings and no-ops pass through unchanged.
    """
    if is_relaxation(before, after):
        record_verdict_transition(
            ctx,
            stage=f"{stage}_relaxation_blocked",
            before=before,
            after=before,
            reason=f"blocked_relaxation_to_{after.name}",
        )
        return before
    return after


def sync_confirmation_flags(ctx: Any, verdict: LyapunovVerdict) -> None:
    try:
        # Campaign OBS (decision DS4a): the historical read here was
        # getattr(ctx, "conflict_signal", None), an attribute nothing
        # ever writes (0.0 on every run). The flag now consumes the
        # real declared channel through the SAME canonical threshold
        # function the confirmation stage applies, so the gate-time
        # exports agree with the confirmation decision instead of
        # ignoring conflict. Direction is hardening-only: pressure can
        # raise the flag, never lower it (F-001).
        conflict_pressure = getattr(ctx, "conflict_pressure", None)
        conflict_value = (
            float(conflict_pressure) if conflict_pressure is not None else 0.0
        )

        requires_confirmation = (
            verdict == LyapunovVerdict.REQUIRE_CONFIRMATION
            or verdict == LyapunovVerdict.ABSTAIN
            or requires_conflict_confirmation(conflict_value)
        )

        # -------------------------------------------------
        # Legacy trace compatibility only.
        # Runtime authority lives in execution_state.
        #
        # DO NOT write mutable runtime authority into
        # private ctx flags from trace helpers.
        # -------------------------------------------------
        ctx.extra["requires_confirmation"] = requires_confirmation
        ctx.extra["needs_confirmation"] = requires_confirmation

        runtime = ctx.execution.execution_state
        if runtime is not None:
            runtime.needs_confirmation = requires_confirmation

    except Exception as exc:
        ErrorManager.attach(
            ctx,
            PipelineStageDegradedError(
                message=str(exc),
                details={
                    "component": "sync_confirmation_flags",
                    "exception_type": type(exc).__name__,
                },
            ),
        )
