# arvis/kernel/pipeline/stages/gate_stage.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from typing import cast
import logging

from arvis.math.lyapunov.lyapunov_gate import (
    LyapunovVerdict,
)
from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov
from arvis.math.switching.switching_params import switching_condition
from arvis.math.switching.switching_params import switching_lhs, kappa_eff
from arvis.math.stability.global_guard import GlobalStabilityGuard
from arvis.math.switching.global_stability_observer import GlobalStabilityObserver
from arvis.math.confidence.system_confidence import SystemConfidenceInputs, compute_system_confidence
from arvis.math.adaptive.adaptive_runtime_observer import AdaptiveRuntimeObserver
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.stability.validity_envelope import build_validity_envelope
from arvis.math.gate.gate_types import GateKernelInputs
from arvis.math.gate.gate_policy import apply_gate_policy
from arvis.math.gate.gate_adapter import ensure_lyapunov_state
from arvis.math.gate.gate_entry import run_gate_kernel
from arvis.math.gate.gate_fusion import run_fusion
from arvis.kernel.observability.gate_observer import GateObserver
from arvis.kernel.pipeline.gate_overrides import GateOverrides

@dataclass
class StabilityEnvelope:
    delta_w: Optional[float]
    global_safe: bool
    switching_safe: bool
    w_bound_ratio: Optional[float]
    hard_block: bool
    hard_reason: Optional[str]


def _record_verdict_transition(
    ctx: Any,
    stage: str,
    before: LyapunovVerdict,
    after: LyapunovVerdict,
    reason: str,
) -> None:
    trace = ctx.extra.setdefault("verdict_transition_trace", [])
    trace.append(
        {"stage": stage, "before": str(before), "after": str(after), "reason": reason}
    )
    ctx.extra["last_verdict_source"] = stage
    ctx.extra["last_verdict_reason"] = reason

def _apply_global_stability_policy(
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
            _record_verdict_transition(
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

def _sync_confirmation_flags(
    ctx: Any,
    verdict: LyapunovVerdict,
) -> None:
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

@dataclass
class CompositeMetrics:
    prev_slow: Any
    cur_slow: Any
    prev_symbolic: Any
    cur_symbolic: Any
    delta_w: Optional[float]
    w_prev: Optional[float]
    w_current: Optional[float]

@dataclass
class StabilityAssessment:
    global_safe: bool
    switching_safe: bool
    w_ratio: Optional[float]
    adaptive_metrics: Optional[AdaptiveSnapshot]
    recovery_detected: bool
    composite_recommendation: Optional[str]
    switching_metrics: dict[str, Any]
    envelope: StabilityEnvelope
    confidence_inputs: SystemConfidenceInputs
    system_confidence: float

class GateStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        overrides = self._resolve_overrides(ctx)
        self._initialize_context(ctx)
        w_bound_tol = getattr(pipeline, "w_bound_tolerance", 1.05)

        composite = self._compute_composite_metrics(ctx)
        self._expose_composite_metrics(ctx, composite)

        adaptive_metrics = self._compute_adaptive_metrics(
            pipeline=pipeline,
            ctx=ctx,
            w_prev=composite.w_prev,
            w_current=composite.w_current,
        )

        global_safe = self._compute_global_stability(ctx, composite.delta_w)
        recovery_detected = self._detect_recovery(
            ctx=ctx,
            delta_w=composite.delta_w,
            w_prev=composite.w_prev,
            w_current=composite.w_current,
        )
        composite_recommendation = self._compute_composite_recommendation(
            pipeline=pipeline,
            delta_w=composite.delta_w,
            w_current=composite.w_current,
        )
        ctx.extra["composite_gate_recommendation"] = composite_recommendation

        self._detect_slow_drift(
            ctx=ctx,
            prev_slow=composite.prev_slow,
            cur_slow=composite.cur_slow,
            delta_w=composite.delta_w,
        )

        switching_safe = self._compute_switching_safety(
            ctx=ctx,
            overrides=overrides,
        )

        w_ratio = self._compute_exponential_bound(ctx)
        envelope = self._build_stability_envelope(
            ctx=ctx,
            global_safe=global_safe,
            switching_safe=switching_safe,
            w_ratio=w_ratio,
            w_bound_tol=w_bound_tol,
            delta_w=composite.delta_w,
        )

        confidence_inputs, system_confidence = self._compute_system_confidence(
            ctx=ctx,
            delta_w=composite.delta_w,
            global_safe=global_safe,
            switching_safe=switching_safe,
        )
        switching_metrics = self._build_switching_metrics(ctx, switching_safe)

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

        verdict, pre_verdict, kernel_result, stability_certificate = self._run_decision_stack(
            pipeline=pipeline,
            ctx=ctx,
            overrides=overrides,
            composite=composite,
            assessment=assessment,
            w_bound_tol=w_bound_tol,
        )

        self._finalize_observability(
            pipeline=pipeline,
            ctx=ctx,
            composite=composite,
            assessment=assessment,
            pre_verdict=pre_verdict,
            verdict=verdict,
            stability_certificate=stability_certificate,
            kernel_result=kernel_result,
        )

        ctx.gate_result = verdict

    def _resolve_overrides(self, ctx: Any) -> GateOverrides:
        overrides = getattr(ctx, "gate_overrides", None)
        if overrides is not None:
            return cast(GateOverrides, overrides)

        extra = getattr(ctx, "extra", {})
        return GateOverrides(
            force_safe_projection=extra.get("force_safe_projection", False),
            force_safe_switching=extra.get("force_safe_switching", False),
        )

    def _initialize_context(self, ctx: Any) -> logging.Logger:
        if not hasattr(ctx, "delta_w_history"):
            ctx.delta_w_history = []

        if not hasattr(ctx, "extra"):
            ctx.extra = {}

        ctx.w_prev = getattr(ctx, "w_prev", None)
        ctx.w_current = getattr(ctx, "w_current", 0.0)
        ctx.delta_w = getattr(ctx, "delta_w", 0.0)

        ctx.stability_certificate = getattr(
            ctx,
            "stability_certificate",
            {
                "local": False,
                "global": True,
                "switching": True,
                "delta_negative": True,
                "exponential": True,
            },
        )

        ctx.system_confidence = getattr(ctx, "system_confidence", 0.0)
        return logging.getLogger(__name__)

    def _compute_composite_metrics(self, ctx: Any) -> CompositeMetrics:
        comp = CompositeLyapunov(lambda_mismatch=0.5, gamma_z=1.0)

        prev_slow = getattr(ctx, "slow_state_prev", None)
        cur_slow = getattr(ctx, "slow_state", None)
        prev_symbolic = getattr(ctx, "symbolic_state_prev", None)
        cur_symbolic = getattr(ctx, "symbolic_state", None)

        delta_w: Optional[float] = None
        w_prev: Optional[float] = None
        w_current: Optional[float] = None

        try:
            if ctx.cur_lyap is not None:
                w_current = comp.W(
                    fast=ctx.cur_lyap,
                    slow=cur_slow,
                    symbolic=cur_symbolic if cur_symbolic is not None else None,
                )
            else:
                w_current = 0.0

            if ctx.prev_lyap is not None:
                w_prev = comp.W(
                    fast=ctx.prev_lyap,
                    slow=prev_slow,
                    symbolic=prev_symbolic if prev_symbolic is not None else None,
                )

            if ctx.prev_lyap is not None and ctx.cur_lyap is not None:
                delta_w = comp.delta_W(
                    fast_prev=ctx.prev_lyap,
                    fast_next=ctx.cur_lyap,
                    slow_prev=prev_slow,
                    slow_next=cur_slow,
                    symbolic_prev=prev_symbolic if prev_symbolic is not None else None,
                    symbolic_next=cur_symbolic if cur_symbolic is not None else None,
                )

            if delta_w is None:
                delta_w = 0.0
        except Exception:
            delta_w = getattr(ctx, "delta_w", None)

        return CompositeMetrics(
            prev_slow=prev_slow,
            cur_slow=cur_slow,
            prev_symbolic=prev_symbolic,
            cur_symbolic=cur_symbolic,
            delta_w=delta_w,
            w_prev=w_prev,
            w_current=w_current,
        )

    def _expose_composite_metrics(self, ctx: Any, composite: CompositeMetrics) -> None:
        ctx.w_prev = composite.w_prev
        ctx.w_current = composite.w_current
        ctx.delta_w = composite.delta_w

    def _compute_adaptive_metrics(
        self,
        pipeline: Any,
        ctx: Any,
        w_prev: Optional[float],
        w_current: Optional[float],
    ) -> Optional[AdaptiveSnapshot]:
        adaptive_metrics: Optional[AdaptiveSnapshot] = None
        try:
            if (
                w_prev is not None
                and w_current is not None
                and ctx.switching_runtime
                and ctx.switching_params
            ):
                if not hasattr(pipeline, "adaptive_observer"):
                    pipeline.adaptive_observer = AdaptiveRuntimeObserver(
                        estimator=pipeline.adaptive_kappa_estimator
                    )

                tau_d = float(ctx.switching_runtime.dwell_time())
                J = float(ctx.switching_params.J)

                adaptive_metrics = pipeline.adaptive_observer.update(
                    W_prev=w_prev,
                    W_next=w_current,
                    J=J,
                    tau_d=tau_d,
                )
                ctx.adaptive_snapshot = adaptive_metrics
        except Exception:
            adaptive_metrics = None

        if adaptive_metrics is None:
            adaptive_metrics = getattr(ctx, "adaptive_snapshot", None)

        return adaptive_metrics

    def _compute_global_stability(self, ctx: Any, delta_w: Optional[float]) -> bool:
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

    def _detect_recovery(
        self,
        ctx: Any,
        delta_w: Optional[float],
        w_prev: Optional[float],
        w_current: Optional[float],
    ) -> bool:
        recovery_detected = False
        try:
            if delta_w is not None and delta_w < 0:
                recovery_detected = True
            elif (
                ctx.prev_lyap is not None
                and ctx.cur_lyap is not None
                and float(ctx.cur_lyap) < float(ctx.prev_lyap)
            ):
                recovery_detected = True
            elif (
                w_prev is not None
                and w_current is not None
                and float(w_current) < float(w_prev)
            ):
                recovery_detected = True
        except Exception:
            recovery_detected = False

        return recovery_detected

    def _compute_composite_recommendation(
        self,
        pipeline: Any,
        delta_w: Optional[float],
        w_current: Optional[float],
    ) -> Optional[str]:
        composite_recommendation = None
        try:
            if delta_w is not None and w_current is not None:
                denom = max(abs(w_current), 1e-6)
                raw_ratio = delta_w / denom
                ratio = max(min(raw_ratio, 1.0), -1.0)

                rec_soft = getattr(pipeline, "composite_rec_soft_threshold", 0.0)
                rec_strong = getattr(pipeline, "composite_rec_strong_threshold", 0.05)

                if ratio > rec_strong:
                    composite_recommendation = "strong_decrease"
                elif ratio > rec_soft:
                    composite_recommendation = "soft_decrease"
                elif ratio < -rec_strong:
                    composite_recommendation = "strong_increase"
                else:
                    composite_recommendation = "stable"
        except Exception:
            composite_recommendation = None
        return composite_recommendation

    def _detect_slow_drift(
        self,
        ctx: Any,
        prev_slow: Any,
        cur_slow: Any,
        delta_w: Optional[float],
    ) -> None:
        try:
            if prev_slow is None or cur_slow is None:
                hist = ctx.extra.setdefault("lyap_history", [])
                if ctx.cur_lyap is not None:
                    hist.append(float(ctx.cur_lyap))
                if len(hist) > 20:
                    hist.pop(0)
                if len(hist) >= 5:
                    diffs = [hist[i] - hist[i - 1] for i in range(1, len(hist))]
                    small_increases = [d for d in diffs if d > 0 and d < 0.01]
                    if len(small_increases) >= 4:
                        ctx.extra["slow_drift_warning"] = True
            else:
                slow_delta = abs(cur_slow - prev_slow)
                drift_history = ctx.extra.setdefault("slow_drift_history", [])
                drift_history.append(slow_delta)
                if len(drift_history) > 10:
                    drift_history.pop(0)
                avg_drift = sum(drift_history) / len(drift_history)
                if delta_w is not None and delta_w > 0 and avg_drift < 0.002:
                    ctx.extra["slow_drift_warning"] = True
        except Exception:
            pass

    def _compute_switching_safety(self, ctx: Any, overrides: GateOverrides) -> bool:
        switching_safe = True
        try:
            if not overrides.force_safe_switching:
                if ctx.switching_runtime and ctx.switching_params:
                    switching_safe = switching_condition(
                        ctx.switching_runtime,
                        ctx.switching_params,
                    )
        except Exception:
            switching_safe = True

        if overrides.force_safe_switching:
            switching_safe = True

        ctx.switching_safe = switching_safe
        return switching_safe

    def _compute_exponential_bound(self, ctx: Any) -> Optional[float]:
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

    def _build_stability_envelope(
        self,
        ctx: Any,
        global_safe: bool,
        switching_safe: bool,
        w_ratio: Optional[float],
        w_bound_tol: float,
        delta_w: Optional[float],
    ) -> StabilityEnvelope:
        reasons = []
        if not global_safe:
            reasons.append("global")
        if not switching_safe:
            reasons.append("switching")
        if w_ratio is not None and w_ratio > w_bound_tol:
            reasons.append("exponential_bound")

        # -----------------------------------------
        # HARD BLOCK POLICY
        # -----------------------------------------
        # IMPORTANT:
        # - global instability MUST NOT hard block
        # - switching instability MUST NOT hard block here
        #   (handled later in dedicated veto layers if needed)
        # -----------------------------------------
        hard_block = False

        hard_reason = "_".join(reasons) if reasons else None

        if hard_block:
            ctx.extra.setdefault("warnings", []).append({
                "type": "hard_block",
                "reason": hard_reason,
            })

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

    def _compute_system_confidence(
        self,
        ctx: Any,
        delta_w: Optional[float],
        global_safe: bool,
        switching_safe: bool,
    ) -> tuple[SystemConfidenceInputs, float]:
        confidence_inputs = SystemConfidenceInputs(
            delta_w=delta_w,
            global_safe=bool(global_safe),
            switching_safe=bool(switching_safe),
            has_history=ctx.prev_lyap is not None,
            has_observability=ctx.cur_lyap is not None,
            collapse_risk=float(getattr(ctx, "collapse_risk", 0.0) or 0.0),
        )
        system_confidence = compute_system_confidence(confidence_inputs)
        ctx.extra["system_confidence"] = system_confidence
        ctx.system_confidence = system_confidence
        return confidence_inputs, system_confidence

    def _build_switching_metrics(self, ctx: Any, switching_safe: bool) -> dict[str, Any]:
        try:
            if ctx.switching_runtime and ctx.switching_params:
                tau_d = float(ctx.switching_runtime.dwell_time())
                k_eff = float(kappa_eff(ctx.switching_params))
                lhs = float(switching_lhs(ctx.switching_runtime, ctx.switching_params))
                return {
                    "tau_d": tau_d,
                    "kappa_eff": k_eff,
                    "lhs": lhs,
                    "safe": bool(switching_safe),
                    "J": float(ctx.switching_params.J),
                    "eta": float(ctx.switching_params.eta),
                    "alpha": float(ctx.switching_params.alpha),
                    "gamma_z": float(ctx.switching_params.gamma_z),
                    "L_T": float(ctx.switching_params.L_T),
                }
        except Exception:
            pass
        return {}

    def _run_decision_stack(
        self,
        pipeline: Any,
        ctx: Any,
        overrides: GateOverrides,
        composite: CompositeMetrics,
        assessment: StabilityAssessment,
        w_bound_tol: float,
    ) -> tuple[LyapunovVerdict, LyapunovVerdict, Any, dict[str, Any]]:
        stability_certificate = {
            "local": composite.delta_w is not None,
            "global": bool(assessment.global_safe),
            "switching": bool(assessment.switching_safe),
            "delta_negative": (composite.delta_w is not None and composite.delta_w <= 0),
            "exponential": (assessment.w_ratio is None or assessment.w_ratio <= w_bound_tol),
        }

        safe_prev_lyap = (
            ensure_lyapunov_state(ctx.prev_lyap)
            if ctx.prev_lyap is not None else None
        )
        safe_cur_lyap = (
            ensure_lyapunov_state(ctx.cur_lyap)
            if ctx.cur_lyap is not None else None
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
                if assessment.adaptive_metrics and assessment.adaptive_metrics.is_available
                else None
            ),
            adaptive_available=bool(
                assessment.adaptive_metrics and assessment.adaptive_metrics.is_available
            ),
            cognitive_mode=getattr(ctx, "_cognitive_mode", None),
            epsilon=float(getattr(ctx, "_epsilon", 1.0)),
        )

        kernel_result = run_gate_kernel(inputs)
        recovery_detected = assessment.recovery_detected or kernel_result.recovery_detected
        if recovery_detected:
            ctx.extra["recovery_detected"] = True

        pre_verdict = kernel_result.pre_verdict
        if assessment.adaptive_metrics and assessment.adaptive_metrics.is_available:
            if assessment.adaptive_metrics.is_unstable:
                pre_verdict = LyapunovVerdict.ABSTAIN

        self._map_kernel_reasons(ctx, kernel_result, assessment.adaptive_metrics)
        self._apply_kappa_margin_layer(ctx, pre_verdict, assessment.adaptive_metrics)
        pre_verdict = self._updated_pre_verdict(ctx, pre_verdict, assessment.adaptive_metrics)

        if kernel_result.certificate:
            stability_certificate.update(kernel_result.certificate)
        ctx.stability_certificate = stability_certificate

        verdict = self._run_fusion(
            ctx=ctx,
            pre_verdict=pre_verdict,
            kernel_result=kernel_result,
            delta_w=composite.delta_w,
            switching_safe=assessment.switching_safe,
            global_safe=assessment.global_safe,
            adaptive_metrics=assessment.adaptive_metrics,
        )

        verdict = self._apply_recovery_override(
            ctx=ctx,
            verdict=verdict,
            recovery_detected=recovery_detected,
            kernel_result=kernel_result,
            adaptive_metrics=assessment.adaptive_metrics,
        )

        self._build_validity_envelope(
            ctx=ctx,
            switching_safe=assessment.switching_safe,
            w_ratio=assessment.w_ratio,
            w_bound_tol=w_bound_tol,
            adaptive_metrics=assessment.adaptive_metrics,
        )

        self._write_mid_traces(
            ctx=ctx,
            w_current=composite.w_current,
            delta_w=composite.delta_w,
            pre_verdict=pre_verdict,
            verdict=verdict,
        )

        before_policy = verdict
        verdict = apply_gate_policy(
            verdict=verdict,
            envelope=assessment.envelope,
            adaptive_metrics=assessment.adaptive_metrics,
            ctx=ctx,
            kernel_result=kernel_result,
        )
        if verdict != before_policy:
            _record_verdict_transition(
                ctx,
                stage="apply_gate_policy",
                before=before_policy,
                after=verdict,
                reason="gate_policy_adjustment",
            )

        verdict = self._apply_validity_enforcement(ctx, verdict, overrides)
        verdict = self._apply_projection_enforcement(
            pipeline=pipeline,
            ctx=ctx,
            verdict=verdict,
            overrides=overrides,
            delta_w=composite.delta_w,
            global_safe=assessment.global_safe,
            switching_safe=assessment.switching_safe,
        )
        verdict = self._apply_kappa_hard_block(ctx, verdict)
        verdict = self._apply_final_adaptive_veto(ctx, verdict, assessment.adaptive_metrics)

        verdict = _apply_global_stability_policy(
            ctx,
            verdict,
            assessment.global_safe,
        )

        _sync_confirmation_flags(ctx, verdict)

        if "fusion_trace" in ctx.extra:
            ctx.extra["fusion_trace"]["final_verdict"] = str(verdict)

        return verdict, pre_verdict, kernel_result, stability_certificate

    def _map_kernel_reasons(
        self,
        ctx: Any,
        kernel_result: Any,
        adaptive_metrics: Optional[AdaptiveSnapshot],
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

    def _apply_kappa_margin_layer(
        self,
        ctx: Any,
        pre_verdict: LyapunovVerdict,
        adaptive_metrics: Optional[AdaptiveSnapshot],
    ) -> None:
        try:
            if adaptive_metrics is None or adaptive_metrics.margin is None:
                return

            kappa_margin = float(adaptive_metrics.margin)
            ctx.extra["kappa_margin"] = kappa_margin

            if kappa_margin > 0.0:
                kappa_band = "hard"
            elif kappa_margin > -0.02:
                kappa_band = "critical"
            elif kappa_margin > -0.05:
                kappa_band = "warning"
            else:
                kappa_band = "stable"

            ctx.extra["kappa_band"] = kappa_band
            reasons = ctx.extra.setdefault("fusion_reasons", [])

            if kappa_band == "critical":
                if "kappa_margin_critical" not in reasons:
                    reasons.append("kappa_margin_critical")
                if pre_verdict == LyapunovVerdict.ALLOW:
                    ctx.extra["_kappa_margin_forced_confirmation"] = True
            elif kappa_band == "warning":
                if "kappa_margin_warning" not in reasons:
                    reasons.append("kappa_margin_warning")
        except Exception:
            pass

    def _updated_pre_verdict(
        self,
        ctx: Any,
        pre_verdict: LyapunovVerdict,
        adaptive_metrics: Optional[AdaptiveSnapshot],
    ) -> LyapunovVerdict:
        if ctx.extra.pop("_kappa_margin_forced_confirmation", False):
            return LyapunovVerdict.REQUIRE_CONFIRMATION
        if adaptive_metrics and adaptive_metrics.is_available and adaptive_metrics.is_unstable:
            return LyapunovVerdict.ABSTAIN
        return pre_verdict

    def _run_fusion(
        self,
        ctx: Any,
        pre_verdict: LyapunovVerdict,
        kernel_result: Any,
        delta_w: Optional[float],
        switching_safe: bool,
        global_safe: bool,
        adaptive_metrics: Optional[AdaptiveSnapshot],
    ) -> LyapunovVerdict:
        try:
            fusion = run_fusion(
                pre_verdict=pre_verdict,
                delta_w=delta_w,
                switching_safe=switching_safe,
                global_safe=bool(global_safe),
                ctx=ctx,
            )
            verdict = cast(LyapunovVerdict, fusion.verdict)
            if kernel_result.final_verdict == LyapunovVerdict.ABSTAIN:
                ctx.extra.setdefault("fusion_reasons", []).append("kernel_abstain_signal")
            if adaptive_metrics and adaptive_metrics.is_unstable:
                _record_verdict_transition(
                    ctx,
                    stage="fusion_adaptive_hard_veto",
                    before=verdict,
                    after=LyapunovVerdict.ABSTAIN,
                    reason="adaptive_metrics_unstable",
                )
                verdict = LyapunovVerdict.ABSTAIN
            existing = list(ctx.extra.get("fusion_reasons", []))
            ctx.extra["fusion_reasons"] = list(dict.fromkeys(existing + fusion.reasons))
            return verdict
        except Exception:
            verdict = pre_verdict or LyapunovVerdict.ABSTAIN
            existing = list(ctx.extra.get("fusion_reasons", []))
            ctx.extra["fusion_reasons"] = list(dict.fromkeys(existing + ["fusion_fallback"]))
            ctx.extra["fusion_error"] = True
            return verdict

    def _apply_recovery_override(
        self,
        ctx: Any,
        verdict: LyapunovVerdict,
        recovery_detected: bool,
        kernel_result: Any,
        adaptive_metrics: Optional[AdaptiveSnapshot],
    ) -> LyapunovVerdict:
        if recovery_detected or kernel_result.recovery_detected:
            if verdict == LyapunovVerdict.ABSTAIN:
                if not (adaptive_metrics and adaptive_metrics.is_unstable):
                    _record_verdict_transition(
                        ctx,
                        stage="recovery_post_fusion_override",
                        before=verdict,
                        after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                        reason="recovery_detected",
                    )
                    verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
                    ctx.extra.setdefault("fusion_reasons", []).append(
                        "recovery_post_fusion_override"
                    )
        return verdict

    def _build_validity_envelope(
        self,
        ctx: Any,
        switching_safe: bool,
        w_ratio: Optional[float],
        w_bound_tol: float,
        adaptive_metrics: Optional[AdaptiveSnapshot],
    ) -> None:
        try:
            metrics = getattr(ctx, "global_stability_metrics", None)
            kappa_safe = not bool(
                metrics is not None and getattr(metrics, "kappa_violation", False)
            )
            projection_available = (ctx.prev_lyap is not None or ctx.cur_lyap is not None)
            exponential_safe = (w_ratio is None or w_ratio <= w_bound_tol)
            adaptive_band = ctx.extra.get("kappa_band")

            validity_envelope = build_validity_envelope(
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

    def _write_mid_traces(
        self,
        ctx: Any,
        w_current: Optional[float],
        delta_w: Optional[float],
        pre_verdict: LyapunovVerdict,
        verdict: LyapunovVerdict,
    ) -> None:
        try:
            if delta_w is not None:
                ctx.extra["closed_loop_feedback"] = {
                    "energy_increase": bool(delta_w > 0),
                    "energy_decrease": bool(delta_w < 0),
                    "control_should_reduce": bool(delta_w > 0),
                }
        except Exception:
            pass

        try:
            ctx.extra["iss_perturbation"] = {
                "projection": float(getattr(ctx, "projection_disturbance", 0.0) or 0.0),
                "noise": float(getattr(ctx, "noise_disturbance", 0.0) or 0.0),
                "switch": float(getattr(ctx, "switching_disturbance", 0.0) or 0.0),
                "adversarial": float(getattr(ctx, "adversarial_disturbance", 0.0) or 0.0),
            }
        except Exception:
            pass

        try:
            if ctx.validity_envelope is not None:
                ctx.extra["validity_envelope_extended"] = {
                    **ctx.extra.get("validity_envelope", {}),
                    "projection_valid": bool(ctx.prev_lyap is not None or ctx.cur_lyap is not None),
                    "switching_constraints_valid": bool(getattr(ctx, "switching_safe", False)),
                    "perturbation_bounded": True,
                }
        except Exception:
            pass

    def _apply_validity_enforcement(
        self,
        ctx: Any,
        verdict: LyapunovVerdict,
        overrides: GateOverrides,
    ) -> LyapunovVerdict:
        try:
            validity = getattr(ctx, "validity_envelope", None)
            if overrides.disable_validity_envelope:
                validity = None
            if validity is not None and not validity.valid:
                ctx.extra.setdefault("fusion_reasons", []).append(f"validity_{validity.reason}")
                if verdict == LyapunovVerdict.ALLOW:
                    _record_verdict_transition(
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

    def _apply_projection_enforcement(
        self,
        pipeline: Any,
        ctx: Any,
        verdict: LyapunovVerdict,
        overrides: GateOverrides,
        delta_w: Optional[float],
        global_safe: bool,
        switching_safe: bool,
    ) -> LyapunovVerdict:
        try:
            # -----------------------------------------
            # Projection inputs (Π_impl + Π_cert)
            # -----------------------------------------
            projection_cert = getattr(ctx, "projection_certificate", None)
            projection_view = getattr(ctx, "projection_view", None)
            projected_state = getattr(ctx, "projected_state", None)

            if projection_cert is not None:
                domain_valid = bool(getattr(projection_cert, "domain_valid", False))
                margin = getattr(projection_cert, "margin_to_boundary", None)
                is_safe = bool(getattr(projection_cert, "is_projection_safe", False))
                lyapunov_compatible = bool(
                    getattr(projection_cert, "lyapunov_compatibility_ok", True)
                )
            else:
                domain_valid = None
                margin = None
                is_safe = None
                lyapunov_compatible = None

            # -----------------------------------------
            # Backward compatibility (legacy projection)
            # -----------------------------------------
            if projection_view is not None and isinstance(projection_view, dict):
                # ensure legacy key exists
                if "system_tension" not in projection_view:
                    try:
                        if projected_state is not None:
                            projection_view["system_tension"] = float(
                                projected_state.primary_tension()
                            )
                    except Exception:
                        projection_view["system_tension"] = 0.0

            projection_boundary_threshold = float(
                getattr(pipeline, "projection_boundary_threshold", 0.1)
            )

            if projection_cert is None:
                return verdict

            projection_reasons = ctx.extra.setdefault("fusion_reasons", [])
            ctx.extra["projection_domain_valid"] = bool(domain_valid)
            ctx.extra["projection_margin"] = margin
            ctx.extra["projection_safe"] = bool(is_safe)
            ctx.extra["projection_lyapunov_compatible"] = bool(lyapunov_compatible)

            # -----------------------------------------
            # HARD BLOCK: invalid domain
            # -----------------------------------------

            if (
                domain_valid is False
                and not overrides.force_safe_projection
                and not overrides.disable_projection_hard_block
            ):
                if "projection_invalid" not in projection_reasons:
                    projection_reasons.append("projection_invalid")
                _record_verdict_transition(
                    ctx,
                    stage="projection_hard_block",
                    before=verdict,
                    after=LyapunovVerdict.ABSTAIN,
                    reason="projection_invalid",
                )
                ctx.extra["projection_hard_block"] = True
                return LyapunovVerdict.ABSTAIN
            
            # -----------------------------------------
            # SOFT BLOCK: Lyapunov incompatibility
            # -----------------------------------------
            if (
                lyapunov_compatible is False
                and not overrides.force_safe_projection
            ):
                if "projection_lyapunov_incompatible" not in projection_reasons:
                    projection_reasons.append("projection_lyapunov_incompatible")

                if verdict == LyapunovVerdict.ALLOW:
                    _record_verdict_transition(
                        ctx,
                        stage="projection_lyapunov_enforcement",
                        before=verdict,
                        after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                        reason="projection_lyapunov_incompatible",
                    )
                    verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
            
            # -----------------------------------------
            # SOFT BLOCK: boundary proximity
            # -----------------------------------------

            if (
                not overrides.force_safe_projection
                and margin is not None
                and margin >= 0.0
                and margin < projection_boundary_threshold
            ):
                if "projection_boundary" not in projection_reasons:
                    projection_reasons.append("projection_boundary")
                _record_verdict_transition(
                    ctx,
                    stage="projection_boundary_enforcement",
                    before=verdict,
                    after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                    reason="projection_boundary",
                )
                if verdict == LyapunovVerdict.ALLOW:
                    verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

            # -----------------------------------------
            # COUPLING (: projection must NOT override global policy
            # -----------------------------------------
            projection_unstable_coupling = (
                (not is_safe)
                and (
                    (delta_w is not None and delta_w > 0.0)
                    or (not bool(global_safe))
                    or (not bool(switching_safe))
                )
            )

            if projection_unstable_coupling and not overrides.force_safe_projection:
                if "projection_unsafe" not in projection_reasons:
                    projection_reasons.append("projection_unsafe")

                # projection can DOWNGRADE but NOT HARD BLOCK
                if verdict == LyapunovVerdict.ALLOW:
                    _record_verdict_transition(
                        ctx,
                        stage="projection_unstable_coupling_soft",
                        before=verdict,
                        after=LyapunovVerdict.REQUIRE_CONFIRMATION,
                        reason="projection_unsafe",
                    )
                    verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

            # -----------------------------------------
            # OPTIONAL FUTURE: projection-aware signals
            # (safe noop for now)
            # -----------------------------------------
            try:
                if projected_state is not None:
                    # Example future hook
                    coherence = projected_state.state_signals.get("coherence_score")
                    if coherence is not None and coherence < 0.1:
                        ctx.extra.setdefault("fusion_reasons", []).append("low_coherence_signal")
            except Exception:
                pass

        except Exception:
            ctx.extra.setdefault("errors", []).append("projection_gate_adjustment_failure")
        return verdict

    def _apply_kappa_hard_block(
        self,
        ctx: Any,
        verdict: LyapunovVerdict,
    ) -> LyapunovVerdict:
        try:
            metrics = getattr(ctx, "global_stability_metrics", None)
            if metrics is not None and getattr(metrics, "kappa_violation", False):
                reasons = ctx.extra.setdefault("fusion_reasons", [])
                if "kappa_violation" not in reasons:
                    reasons.append("kappa_violation")
                _record_verdict_transition(
                    ctx,
                    stage="kappa_hard_block",
                    before=verdict,
                    after=LyapunovVerdict.ABSTAIN,
                    reason="kappa_violation",
                )
                ctx.extra["kappa_hard_block"] = True
                ctx.extra["kappa_gap"] = getattr(metrics, "kappa_gap", None)
                verdict = LyapunovVerdict.ABSTAIN
        except Exception:
            pass
        return verdict

    def _apply_final_adaptive_veto(
        self,
        ctx: Any,
        verdict: LyapunovVerdict,
        adaptive_metrics: Optional[AdaptiveSnapshot],
    ) -> LyapunovVerdict:
        if adaptive_metrics and adaptive_metrics.is_unstable:
            _record_verdict_transition(
                ctx,
                stage="final_adaptive_hard_veto",
                before=verdict,
                after=LyapunovVerdict.ABSTAIN,
                reason="adaptive_metrics_unstable",
            )
            verdict = LyapunovVerdict.ABSTAIN
        return verdict

    def _finalize_observability(
        self,
        pipeline: Any,
        ctx: Any,
        composite: CompositeMetrics,
        assessment: StabilityAssessment,
        pre_verdict: LyapunovVerdict,
        verdict: LyapunovVerdict,
        stability_certificate: dict[str, Any],
        kernel_result: Any,
    ) -> None:
        if pipeline is not None:
            gate_observer = getattr(pipeline, "gate_observer", None)
            if gate_observer is None:
                gate_observer = GateObserver()
                pipeline.gate_observer = gate_observer
        else:
            gate_observer = GateObserver()

        gate_observer.build(
            ctx,
            pre_verdict=pre_verdict,
            final_verdict=verdict,
            delta_w=composite.delta_w,
            w_prev=composite.w_prev,
            w_current=composite.w_current,
            adaptive_metrics=assessment.adaptive_metrics,
            switching_safe=assessment.switching_safe,
            global_safe=assessment.global_safe,
            envelope=assessment.envelope,
            confidence_inputs=assessment.confidence_inputs,
            system_confidence=assessment.system_confidence,
            switching_metrics=assessment.switching_metrics,
            stability_certificate=stability_certificate,
            hard_block=assessment.envelope.hard_block,
            hard_reason=assessment.envelope.hard_reason,
            w_ratio=assessment.w_ratio,
            recovery_detected=assessment.recovery_detected,
            recovery_magnitude=abs(composite.delta_w)
            if (composite.delta_w is not None and assessment.recovery_detected)
            else None,
        )
