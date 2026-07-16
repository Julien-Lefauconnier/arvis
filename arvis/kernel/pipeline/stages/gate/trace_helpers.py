# arvis/kernel/pipeline/stages/gate/trace_helpers.py

from __future__ import annotations

from typing import Any

from arvis.errors.manager import ErrorManager
from arvis.errors.pipeline import PipelineStageDegradedError
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.lyapunov.verdict_order import is_relaxation, strictness

VERDICT_PROVENANCE_KEY = "verdict_provenance"

# Provenance labels for verdicts born in the assessment phase (kernel,
# fusion, recovery), attributed by seed_verdict_provenance before the
# enforcement gates run.
GLOBAL_STABILITY_PROVENANCE = "global_stability_fusion"
ASSESSMENT_PROVENANCE = "stability_assessment"

# Fusion reason marking an ABSTAIN produced by the global stability axis
# itself (multiaxial fusion wired with global_action="abstain").
_GLOBAL_ABSTAIN_MARKER = "global_stability_enforced:abstain"


def record_verdict_transition(
    ctx: Any,
    stage: str,
    before: LyapunovVerdict,
    after: LyapunovVerdict,
    reason: str,
) -> None:
    trace = ctx.extra.setdefault("verdict_transition_trace", [])
    if not isinstance(trace, list):
        ctx.extra["verdict_transition_trace"] = []
        trace = ctx.extra["verdict_transition_trace"]

    trace.append(
        {"stage": stage, "before": str(before), "after": str(after), "reason": reason}
    )
    if strictness(after) > strictness(before):
        ledger = ctx.extra.setdefault(VERDICT_PROVENANCE_KEY, {})
        if isinstance(ledger, dict):
            ledger[after.name] = stage
    ctx.extra["last_verdict_source"] = stage
    ctx.extra["last_verdict_reason"] = reason


def verdict_provenance(ctx: Any, verdict: LyapunovVerdict) -> str | None:
    """Stage that produced the current strictness level, if known.

    Consumers must treat a missing entry as unknown and fail closed
    (no relaxation).
    """
    extra = getattr(ctx, "extra", None)
    if not isinstance(extra, dict):
        return None
    ledger = extra.get(VERDICT_PROVENANCE_KEY)
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
    reasons = extra.get("fusion_reasons")
    reason_list = reasons if isinstance(reasons, list) else []
    if verdict == LyapunovVerdict.ABSTAIN and _GLOBAL_ABSTAIN_MARKER in reason_list:
        source = GLOBAL_STABILITY_PROVENANCE
    else:
        source = ASSESSMENT_PROVENANCE
    ledger = extra.setdefault(VERDICT_PROVENANCE_KEY, {})
    if isinstance(ledger, dict):
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
        conflict_signal = getattr(ctx, "conflict_signal", None)
        conflict_value = 0.0

        if conflict_signal is not None:
            conflict_value = float(getattr(conflict_signal, "global_score", 0.0))

        requires_confirmation = (
            verdict == LyapunovVerdict.REQUIRE_CONFIRMATION
            or verdict == LyapunovVerdict.ABSTAIN
            or conflict_value > 0.0
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

        runtime = getattr(ctx, "execution_state", None)
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
