# arvis/kernel/pipeline/stages/gate/trace_helpers.py

from __future__ import annotations

from typing import Any

from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


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
    ctx.extra["last_verdict_source"] = stage
    ctx.extra["last_verdict_reason"] = reason


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

        ctx.extra["_requires_confirmation"] = requires_confirmation
        ctx.extra["_needs_confirmation"] = requires_confirmation

    except Exception:
        pass
