# arvis/kernel/pipeline/stages/gate/pi_override.py

from __future__ import annotations

from typing import Any

from arvis.kernel.gate.pi_gate import PiBasedGate
from arvis.kernel.pipeline.stages.gate.trace_helpers import record_verdict_transition
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def apply_pi_gate_override(ctx: Any, verdict: LyapunovVerdict) -> LyapunovVerdict:
    try:
        pi_state = getattr(ctx, "pi_state", None)

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
                record_verdict_transition(
                    ctx,
                    stage="pi_gate_override",
                    before=verdict,
                    after=pi_verdict,
                    reason="pi_structured_decision",
                )

                # ---- HARD SAFETY RULE ----
                # PI cannot relax a stricter verdict (especially ABSTAIN)
                if kernel_verdict == LyapunovVerdict.ABSTAIN:
                    return LyapunovVerdict.ABSTAIN

                # ---- Allowed overrides ----
                if pi_verdict == LyapunovVerdict.ABSTAIN:
                    verdict = LyapunovVerdict.ABSTAIN
                elif (
                    pi_verdict == LyapunovVerdict.REQUIRE_CONFIRMATION
                    and verdict == LyapunovVerdict.ALLOW
                ):
                    verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

    except Exception:
        ctx.extra.setdefault("errors", []).append("pi_gate_failure")

    return verdict


__all__ = [
    "PiBasedGate",
    "apply_pi_gate_override",
]
