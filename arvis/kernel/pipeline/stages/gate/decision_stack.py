# arvis/kernel/pipeline/stages/gate/decision_stack.py

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any, cast

from arvis.kernel.pipeline.gate_overrides import GateOverrides
from arvis.kernel.pipeline.stages.gate.adaptive import (
    apply_final_adaptive_veto,
    apply_kappa_margin_layer,
    updated_pre_verdict,
)
from arvis.kernel.pipeline.stages.gate.enforcement import (
    apply_kappa_hard_block,
    apply_projection_enforcement,
)
from arvis.kernel.pipeline.stages.gate.memory_policy import apply_memory_policy
from arvis.kernel.pipeline.stages.gate.mid_traces import write_mid_traces
from arvis.kernel.pipeline.stages.gate.models import (
    CompositeMetrics,
    GateDecisionResult,
    StabilityAssessment,
)
from arvis.kernel.pipeline.stages.gate.pi_override import apply_pi_gate_override
from arvis.kernel.pipeline.stages.gate.stability import (
    apply_global_stability_policy,
    apply_validity_enforcement,
    build_validity_envelope,
)
from arvis.kernel.pipeline.stages.gate.trace_helpers import (
    record_verdict_transition,
    sync_confirmation_flags,
)
from arvis.math.gate.gate_adapter import ensure_lyapunov_state
from arvis.math.gate.gate_entry import run_gate_kernel
from arvis.math.gate.gate_fusion import run_fusion
from arvis.math.gate.gate_policy import apply_gate_policy
from arvis.math.gate.gate_types import GateKernelInputs
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def _get_gate_stage_hook(name: str) -> Callable[..., Any] | None:
    try:
        module = importlib.import_module("arvis.kernel.pipeline.stages.gate_stage")
        return getattr(module, name, None)
    except Exception:
        return None


class GateDecisionStack:
    def run(
        self,
        pipeline: Any,
        ctx: Any,
        overrides: GateOverrides,
        composite: CompositeMetrics,
        assessment: StabilityAssessment,
        w_bound_tol: float,
    ) -> GateDecisionResult:
        stability_certificate = {
            "local": composite.delta_w is not None,
            "global": bool(assessment.global_safe),
            "switching": bool(assessment.switching_safe),
            "delta_negative": (
                composite.delta_w is not None and composite.delta_w <= 0
            ),
            "exponential": (
                assessment.w_ratio is None or assessment.w_ratio <= w_bound_tol
            ),
        }

        safe_prev_lyap = (
            ensure_lyapunov_state(ctx.prev_lyap) if ctx.prev_lyap is not None else None
        )
        safe_cur_lyap = (
            ensure_lyapunov_state(ctx.cur_lyap) if ctx.cur_lyap is not None else None
        )

        inputs = GateKernelInputs(
            prev_lyap=safe_prev_lyap,
            cur_lyap=safe_cur_lyap,
            slow_prev=composite.prev_slow,
            slow_cur=composite.cur_slow,
            symbolic_prev=composite.prev_symbolic,
            symbolic_cur=composite.cur_symbolic,
            collapse_risk=float(getattr(ctx, "collapse_risk", 0.0)),
            stable=ctx.stable,
            switching_safe=bool(assessment.switching_safe),
            global_safe=bool(assessment.global_safe),
            delta_w=composite.delta_w,
            w_prev=composite.w_prev,
            w_current=composite.w_current,
            adaptive_margin=(
                assessment.adaptive_metrics.margin
                if assessment.adaptive_metrics
                and assessment.adaptive_metrics.is_available
                else None
            ),
            adaptive_available=bool(
                assessment.adaptive_metrics and assessment.adaptive_metrics.is_available
            ),
            cognitive_mode=getattr(ctx, "_cognitive_mode", None),
            epsilon=float(getattr(ctx, "_epsilon", 1.0)),
        )

        hook = _get_gate_stage_hook("run_gate_kernel")
        kernel_fn = hook or run_gate_kernel
        kernel_result = kernel_fn(inputs)
        ctx.kernel_result = kernel_result
        recovery_detected = (
            assessment.recovery_detected or kernel_result.recovery_detected
        )
        if recovery_detected:
            ctx.extra["recovery_detected"] = True

        pre_verdict = kernel_result.pre_verdict
        if assessment.adaptive_metrics and assessment.adaptive_metrics.is_available:
            if assessment.adaptive_metrics.is_unstable:
                pre_verdict = LyapunovVerdict.ABSTAIN

        map_kernel_reasons(ctx, kernel_result, assessment.adaptive_metrics)
        apply_kappa_margin_layer(ctx, pre_verdict, assessment.adaptive_metrics)
        pre_verdict = updated_pre_verdict(ctx, pre_verdict, assessment.adaptive_metrics)

        if kernel_result.certificate:
            stability_certificate.update(kernel_result.certificate)
        ctx.stability_certificate = stability_certificate

        verdict = run_gate_fusion(
            ctx=ctx,
            pre_verdict=pre_verdict,
            kernel_result=kernel_result,
            delta_w=composite.delta_w,
            switching_safe=assessment.switching_safe,
            global_safe=assessment.global_safe,
            adaptive_metrics=assessment.adaptive_metrics,
        )

        verdict = apply_recovery_override(
            ctx=ctx,
            verdict=verdict,
            recovery_detected=recovery_detected,
            kernel_result=kernel_result,
            adaptive_metrics=assessment.adaptive_metrics,
        )

        hook = _get_gate_stage_hook("build_validity_envelope")
        validity_fn = hook or build_validity_envelope

        try:
            envelope = validity_fn(
                ctx=ctx,
                switching_safe=assessment.switching_safe,
                w_ratio=assessment.w_ratio,
                w_bound_tol=w_bound_tol,
                adaptive_metrics=assessment.adaptive_metrics,
            )

        except Exception:
            ctx.validity_envelope = None

        write_mid_traces(
            ctx=ctx,
            w_current=composite.w_current,
            delta_w=composite.delta_w,
            pre_verdict=pre_verdict,
            verdict=verdict,
        )

        before_policy = verdict
        hook = _get_gate_stage_hook("apply_gate_policy")
        policy_fn = hook or apply_gate_policy

        verdict = policy_fn(
            verdict=verdict,
            envelope=assessment.envelope,
            adaptive_metrics=assessment.adaptive_metrics,
            ctx=ctx,
            kernel_result=kernel_result,
        )
        # VALIDITY MUST OVERRIDE POLICY
        try:
            if envelope and not envelope.valid:
                ctx.extra.setdefault("fusion_reasons", []).append(
                    f"validity_{envelope.reason}"
                )

                if verdict == LyapunovVerdict.ALLOW:
                    record_verdict_transition(
                        ctx,
                        stage="validity_enforcement",
                        before=verdict,
                        after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                        reason="validity_constraint",
                    )
                    verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
        except Exception:
            pass

        if verdict != before_policy:
            record_verdict_transition(
                ctx,
                stage="apply_gate_policy",
                before=before_policy,
                after=verdict,
                reason="gate_policy_adjustment",
            )

        verdict = apply_validity_enforcement(ctx, verdict, overrides)
        verdict = apply_projection_enforcement(
            pipeline=pipeline,
            ctx=ctx,
            verdict=verdict,
            overrides=overrides,
            delta_w=composite.delta_w,
            global_safe=assessment.global_safe,
            switching_safe=assessment.switching_safe,
        )
        verdict = apply_kappa_hard_block(ctx, verdict)
        verdict = apply_final_adaptive_veto(ctx, verdict, assessment.adaptive_metrics)

        verdict = apply_global_stability_policy(
            ctx,
            verdict,
            assessment.global_safe,
        )

        verdict = apply_memory_policy(ctx, verdict)
        verdict = apply_pi_gate_override(ctx, verdict)
        sync_confirmation_flags(ctx, verdict)

        if "fusion_trace" in ctx.extra:
            ctx.extra["fusion_trace"]["final_verdict"] = str(verdict)

        reason_codes = tuple(
            str(code).strip()
            for code in dict.fromkeys(ctx.extra.get("fusion_reasons", []))
            if str(code).strip()
        )

        ctx.extra["final_reason_codes"] = reason_codes

        return GateDecisionResult(
            verdict=verdict,
            pre_verdict=pre_verdict,
            kernel_result=kernel_result,
            stability_certificate=stability_certificate,
        )


def map_kernel_reasons(
    ctx: Any,
    kernel_result: Any,
    adaptive_metrics: Any,
) -> None:
    mapped_reasons = []
    for r in kernel_result.reasons:
        if r == "adaptive_instability":
            mapped_reasons.append("adaptive_instability_veto")
        elif r == "adaptive_warning":
            mapped_reasons.append("adaptive_margin_warning")
        elif r == "adaptive_hard_veto":
            mapped_reasons.append("adaptive_instability_veto")
        else:
            mapped_reasons.append(r)
    ctx.extra.setdefault("fusion_reasons", []).extend(mapped_reasons)

    if adaptive_metrics and adaptive_metrics.is_available:
        margin = adaptive_metrics.margin
        if margin is not None and -0.02 < margin <= 0:
            ctx.extra.setdefault("fusion_reasons", []).append("adaptive_margin_warning")


def run_gate_fusion(
    ctx: Any,
    pre_verdict: LyapunovVerdict,
    kernel_result: Any,
    delta_w: float | None,
    switching_safe: bool,
    global_safe: bool,
    adaptive_metrics: Any,
) -> LyapunovVerdict:
    try:
        hook = _get_gate_stage_hook("run_fusion")
        fusion_fn = hook or run_fusion

        fusion = fusion_fn(
            pre_verdict=pre_verdict,
            delta_w=delta_w,
            switching_safe=switching_safe,
            global_safe=bool(global_safe),
            ctx=ctx,
        )
        verdict: LyapunovVerdict = cast(LyapunovVerdict, fusion.verdict)
        if kernel_result.final_verdict == LyapunovVerdict.ABSTAIN:
            ctx.extra.setdefault("fusion_reasons", []).append("kernel_abstain_signal")
        if adaptive_metrics and adaptive_metrics.is_unstable:
            record_verdict_transition(
                ctx,
                stage="fusion_adaptive_hard_veto",
                before=verdict,
                after=LyapunovVerdict.ABSTAIN,
                reason="adaptive_metrics_unstable",
            )
            verdict = LyapunovVerdict.ABSTAIN
        existing = list(ctx.extra.get("fusion_reasons", []))
        ctx.extra["fusion_reasons"] = list(dict.fromkeys(existing + fusion.reasons))

        try:
            if delta_w is not None:
                soft_threshold = getattr(ctx, "delta_w_soft_threshold", -0.05)

                if soft_threshold < delta_w < 0:
                    if verdict == LyapunovVerdict.ALLOW:
                        record_verdict_transition(
                            ctx,
                            stage="local_soft_filter",
                            before=verdict,
                            after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                            reason="weak_stability",
                        )
                        verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
        except Exception:
            pass
        return verdict
    except Exception:
        verdict = pre_verdict or LyapunovVerdict.ABSTAIN
        existing = list(ctx.extra.get("fusion_reasons", []))
        ctx.extra["fusion_reasons"] = list(
            dict.fromkeys(existing + ["fusion_fallback"])
        )
        ctx.extra["fusion_error"] = True
        ctx.extra.setdefault("fusion_error", True)
        return verdict


def apply_recovery_override(
    ctx: Any,
    verdict: LyapunovVerdict,
    recovery_detected: bool,
    kernel_result: Any,
    adaptive_metrics: Any,
) -> LyapunovVerdict:
    if recovery_detected or kernel_result.recovery_detected:
        if verdict == LyapunovVerdict.ABSTAIN:
            validity = getattr(ctx, "validity_envelope", None)

            if (
                validity is not None
                and validity.valid
                and not (adaptive_metrics and adaptive_metrics.is_unstable)
            ):
                record_verdict_transition(
                    ctx,
                    stage="recovery_to_allow",
                    before=verdict,
                    after=LyapunovVerdict.ALLOW,
                    reason="stable_recovery",
                )
                return LyapunovVerdict.ALLOW

            record_verdict_transition(
                ctx,
                stage="recovery_to_confirmation",
                before=verdict,
                after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                reason="uncertain_recovery",
            )
            return LyapunovVerdict.REQUIRE_CONFIRMATION
    return verdict
