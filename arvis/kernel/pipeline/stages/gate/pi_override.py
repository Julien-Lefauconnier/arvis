# arvis/kernel/pipeline/stages/gate/pi_override.py

from __future__ import annotations

from typing import Any

from arvis.errors.manager import ErrorManager
from arvis.kernel.gate.pi_gate import PiBasedGate
from arvis.kernel.pipeline.stages.gate.trace_helpers import record_verdict_transition
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def _resolve_pi_state(ctx: Any) -> Any:
    """
    Canonical Π-state resolver.

    The canonical Π artifact lives under:
        ctx.projection.structured_projection

    Mock/legacy compatibility still supports:
        ctx.projection.pi_state and ctx.pi_state
    """
    projection = getattr(ctx, "projection", None)

    if projection is not None:
        structured = getattr(projection, "structured_projection", None)
        if structured is not None:
            return structured
        pi_state = getattr(projection, "pi_state", None)
        if pi_state is not None:
            return pi_state

    return getattr(ctx, "pi_state", None)


def apply_pi_gate_override(ctx: Any, verdict: LyapunovVerdict) -> LyapunovVerdict:
    try:
        pi_state = _resolve_pi_state(ctx)

        if pi_state is not None:
            pi_gate = PiBasedGate()
            pi_result = pi_gate.evaluate(pi_state, bundle_id="kernel")

            ctx.extra["pi_gate_verdict"] = pi_result.verdict.value
            ctx.extra["pi_gate_risk"] = pi_result.risk_level

            if pi_result.verdict.value == "abstain":
                pi_verdict = LyapunovVerdict.ABSTAIN
            elif pi_result.verdict.value == "require_confirmation":
                pi_verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
            else:
                pi_verdict = LyapunovVerdict.ALLOW

            kernel_verdict = getattr(ctx, "kernel_result", None)
            if kernel_verdict is not None:
                kernel_verdict = getattr(kernel_verdict, "final_verdict", None)

            if pi_verdict != verdict:
                # ---- HARD SAFETY RULE ----
                # PI cannot relax a stricter verdict (especially ABSTAIN)
                if kernel_verdict == LyapunovVerdict.ABSTAIN:
                    applied = LyapunovVerdict.ABSTAIN
                elif pi_verdict == LyapunovVerdict.ABSTAIN:
                    applied = LyapunovVerdict.ABSTAIN
                elif (
                    pi_verdict == LyapunovVerdict.REQUIRE_CONFIRMATION
                    and verdict == LyapunovVerdict.ALLOW
                ):
                    applied = LyapunovVerdict.REQUIRE_CONFIRMATION
                else:
                    applied = verdict

                # Trace fidelity: only applied transitions are recorded,
                # a proposed-but-rejected relaxation is not a transition.
                if applied != verdict:
                    record_verdict_transition(
                        ctx,
                        stage="pi_gate_override",
                        before=verdict,
                        after=applied,
                        reason="pi_structured_decision",
                    )
                verdict = applied

    except Exception as exc:
        ErrorManager.capture_exception(
            ctx,
            exc,
            code="pi_gate_failure",
        )

    return verdict


__all__ = [
    "PiBasedGate",
    "apply_pi_gate_override",
    "_resolve_pi_state",
]
