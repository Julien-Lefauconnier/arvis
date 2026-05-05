# arvis/kernel/pipeline/stages/gate/memory_policy.py

from __future__ import annotations

from typing import Any

from arvis.kernel.pipeline.stages.gate.trace_helpers import record_verdict_transition
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def apply_memory_policy(ctx: Any, verdict: LyapunovVerdict) -> LyapunovVerdict:
    try:
        bundle = getattr(ctx, "bundle", None)
        memory_features = getattr(bundle, "memory_features", {}) if bundle else {}

        memory_pressure = float(memory_features.get("memory_pressure", 0.0))
        has_constraints = bool(memory_features.get("has_constraints", False))

        reasons = ctx.extra.setdefault("fusion_reasons", [])

        if memory_pressure > 0.8:
            if "memory_pressure_hard" not in reasons:
                reasons.append("memory_pressure_hard")

            record_verdict_transition(
                ctx,
                stage="memory_hard_block",
                before=verdict,
                after=LyapunovVerdict.ABSTAIN,
                reason="memory_pressure_high",
            )
            return LyapunovVerdict.ABSTAIN

        if memory_pressure > 0.5:
            if verdict == LyapunovVerdict.ALLOW:
                if "memory_pressure_moderate" not in reasons:
                    reasons.append("memory_pressure_moderate")

                record_verdict_transition(
                    ctx,
                    stage="memory_soft_constraint",
                    before=verdict,
                    after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                    reason="memory_pressure_moderate",
                )
                verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

        if has_constraints:
            if verdict == LyapunovVerdict.ALLOW:
                if "memory_constraints" not in reasons:
                    reasons.append("memory_constraints")

                record_verdict_transition(
                    ctx,
                    stage="memory_constraints_enforcement",
                    before=verdict,
                    after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                    reason="memory_constraints",
                )
                verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

    except Exception:
        pass

    return verdict
