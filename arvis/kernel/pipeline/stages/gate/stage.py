# arvis/kernel/pipeline/stages/gate/stage.py

from __future__ import annotations

from typing import Any

from arvis.kernel.pipeline.stages.gate.adaptive import compute_adaptive_metrics
from arvis.kernel.pipeline.stages.gate.composite import (
    compute_composite_metrics,
    compute_composite_recommendation,
    detect_recovery,
    detect_slow_drift,
    expose_composite_metrics,
)
from arvis.kernel.pipeline.stages.gate.confidence import compute_gate_system_confidence
from arvis.kernel.pipeline.stages.gate.context import (
    initialize_context,
    resolve_overrides,
)
from arvis.kernel.pipeline.stages.gate.decision_stack import GateDecisionStack
from arvis.kernel.pipeline.stages.gate.memory_policy import apply_memory_policy
from arvis.kernel.pipeline.stages.gate.models import StabilityAssessment
from arvis.kernel.pipeline.stages.gate.observability import finalize_observability
from arvis.kernel.pipeline.stages.gate.stability import (
    build_stability_envelope,
    compute_exponential_bound,
    compute_global_stability,
)
from arvis.kernel.pipeline.stages.gate.switching import (
    build_switching_metrics,
    compute_switching_safety,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


class GateStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        overrides = resolve_overrides(ctx)
        initialize_context(ctx)
        w_bound_tol = getattr(pipeline, "w_bound_tolerance", 1.05)

        composite = compute_composite_metrics(ctx)
        expose_composite_metrics(ctx, composite)

        adaptive_metrics = compute_adaptive_metrics(
            pipeline=pipeline,
            ctx=ctx,
            w_prev=composite.w_prev,
            w_current=composite.w_current,
        )

        global_safe = compute_global_stability(ctx, composite.delta_w)
        recovery_detected = detect_recovery(
            ctx=ctx,
            delta_w=composite.delta_w,
            w_prev=composite.w_prev,
            w_current=composite.w_current,
        )
        composite_recommendation = compute_composite_recommendation(
            pipeline=pipeline,
            delta_w=composite.delta_w,
            w_current=composite.w_current,
        )
        ctx.extra["composite_gate_recommendation"] = composite_recommendation

        detect_slow_drift(
            ctx=ctx,
            prev_slow=composite.prev_slow,
            cur_slow=composite.cur_slow,
            delta_w=composite.delta_w,
        )

        switching_safe = compute_switching_safety(
            ctx=ctx,
            overrides=overrides,
        )

        w_ratio = compute_exponential_bound(ctx)
        envelope = build_stability_envelope(
            ctx=ctx,
            global_safe=global_safe,
            switching_safe=switching_safe,
            w_ratio=w_ratio,
            w_bound_tol=w_bound_tol,
            delta_w=composite.delta_w,
        )

        confidence_inputs, system_confidence = compute_gate_system_confidence(
            ctx=ctx,
            delta_w=composite.delta_w,
            global_safe=global_safe,
            switching_safe=switching_safe,
        )
        switching_metrics = build_switching_metrics(ctx, switching_safe)

        assessment = StabilityAssessment(
            global_safe=global_safe,
            switching_safe=switching_safe,
            w_ratio=w_ratio,
            adaptive_metrics=adaptive_metrics,
            recovery_detected=recovery_detected,
            composite_recommendation=composite_recommendation,
            switching_metrics=switching_metrics,
            envelope=envelope,
            confidence_inputs=confidence_inputs,
            system_confidence=system_confidence,
        )

        decision = GateDecisionStack().run(
            pipeline=pipeline,
            ctx=ctx,
            overrides=overrides,
            composite=composite,
            assessment=assessment,
            w_bound_tol=w_bound_tol,
        )

        finalize_observability(
            pipeline=pipeline,
            ctx=ctx,
            composite=composite,
            assessment=assessment,
            decision=decision,
        )

        ctx.gate_result = decision.verdict

    # ---- legacy API compat (clean version) ----
    def _apply_memory_policy(
        self,
        ctx: Any,
        verdict: LyapunovVerdict,
    ) -> LyapunovVerdict:
        return apply_memory_policy(ctx, verdict)
