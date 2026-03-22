# arvis/kernel/pipeline/stages/gate_stage.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
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

@dataclass
class StabilityEnvelope:
    delta_w: Optional[float]
    global_safe: bool
    switching_safe: bool
    w_bound_ratio: Optional[float]
    hard_block: bool
    hard_reason: Optional[str]

class GateStage:

    def run(self, pipeline: Any, ctx: Any) -> None:

        # -----------------------------------------
        # HARD SAFETY INIT (tests + pipeline guarantees)
        # -----------------------------------------
        if not hasattr(ctx, "delta_w_history"):
            ctx.delta_w_history = []

        if not hasattr(ctx, "extra"):
            ctx.extra = {}

        ctx.w_prev = getattr(ctx, "w_prev", None)
        ctx.w_current = getattr(ctx, "w_current", 0.0)
        ctx.delta_w = getattr(ctx, "delta_w", 0.0)

        ctx.stability_certificate = getattr(ctx, "stability_certificate", {
            "local": False,
            "global": True,
            "switching": True,
            "delta_negative": True,
            "exponential": True,
        })

        ctx.system_confidence = getattr(ctx, "system_confidence", 0.0)

        logger = logging.getLogger(__name__)
        if logger is None:
            class _DummyLogger:
                def warning(self, *args, **kwargs): pass
            logger = _DummyLogger()

        # Configurable thresholds
        w_bound_tol = getattr(pipeline, "w_bound_tolerance", 1.05)

        comp = CompositeLyapunov(lambda_mismatch=0.5, gamma_z=1.0)

        switching_safe = True

        # -----------------------------------------
        # 0. COMPOSITE LYAPUNOV 
        # -----------------------------------------
        delta_w, w_prev, w_current = None, None, None

        try:
            prev_slow = getattr(ctx, "slow_state_prev", None)
            cur_slow = getattr(ctx, "slow_state", None)
            prev_symbolic = getattr(ctx, "symbolic_state_prev", None)
            cur_symbolic = getattr(ctx, "symbolic_state", None)

            if ctx.cur_lyap is not None:
                w_current = comp.W(
                    fast=ctx.cur_lyap,
                    slow=cur_slow,
                    symbolic=cur_symbolic if cur_symbolic is not None else None,
                )
            else:
                # Observability fallback (pipeline-level, not mathematical)
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
            # -----------------------------------------
            # Observability fallback for delta_w
            # Ensures metric exposure even without causal pair
            # -----------------------------------------
            if delta_w is None:
                # No causal comparison possible → neutral variation
                delta_w = 0.0

        except Exception:
            delta_w = getattr(ctx, "delta_w", None)
        
        # Expose composite observability
        ctx.w_prev = w_prev
        ctx.w_current = w_current
        ctx.delta_w = delta_w

        # -----------------------------------------
        # ADAPTIVE STABILITY ESTIMATION 
        # -----------------------------------------
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
        
        # Test / fallback path:
        # if adaptive runtime estimation is unavailable, reuse any pre-injected
        # adaptive stability payload already present on the context.
        if adaptive_metrics is None:
            adaptive_metrics = getattr(ctx, "adaptive_snapshot", None)

        # -----------------------------------------
        # 1. Global stability tracking
        # -----------------------------------------
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

        # -----------------------------------------
        # Recovery detection (controlled, robust)
        # -----------------------------------------
        recovery_detected = False
        try:
            # Primary signal: composite Lyapunov decreases
            # Primary signal: composite Lyapunov decreases
            if delta_w is not None and delta_w < 0:
                recovery_detected = True

                # Fallback signal: direct Lyapunov decrease
            elif (
                ctx.prev_lyap is not None
                and ctx.cur_lyap is not None
                and float(ctx.cur_lyap) < float(ctx.prev_lyap)
            ):
                recovery_detected = True

            # Additional observability fallback
            elif (
                w_prev is not None
                and w_current is not None
                and float(w_current) < float(w_prev)
            ):
                recovery_detected = True
            
        except Exception:
            recovery_detected = False

        # ---------------------------------------------------------------
        # Composite recommendation (Lyapunov-informed control direction)
        # ---------------------------------------------------------------
        composite_recommendation = None
        try:
            if delta_w is not None and w_current is not None:
                denom = max(abs(w_current), 1e-6)
                raw_ratio = delta_w / denom
                # Numerical stabilization (bounded Lyapunov variation)
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

        ctx.extra["composite_gate_recommendation"] = composite_recommendation

        # -----------------------------------------
        # Slow dynamics drift detection
        # -----------------------------------------
        try:
            # -----------------------------------------
            # Fallback (no slow_state → tests path)
            # -----------------------------------------
            if prev_slow is None or cur_slow is None:
                hist = ctx.extra.setdefault("lyap_history", [])

                if ctx.cur_lyap is not None:
                    hist.append(float(ctx.cur_lyap))

                if len(hist) > 20:
                    hist.pop(0)

                if len(hist) >= 5:
                    # compute incremental differences
                    diffs = [
                        hist[i] - hist[i - 1]
                        for i in range(1, len(hist))
                    ]

                    small_increases = [
                        d for d in diffs if d > 0 and d < 0.01
                    ]
                    if len(small_increases) >= 4:
                        ctx.extra["slow_drift_warning"] = True

            # -----------------------------------------
            # Full slow drift detection
            # -----------------------------------------
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

        # -----------------------------------------
        # 2. SWITCHING CONDITION
        # -----------------------------------------
        try:
            if ctx.switching_runtime and ctx.switching_params:
                switching_safe = switching_condition(
                    ctx.switching_runtime,
                    ctx.switching_params,
                )
        except Exception:
            switching_safe = True

        ctx.switching_safe = switching_safe

        # -----------------------------------------
        # 3. EXPONENTIAL BOUND
        # -----------------------------------------
        w_ratio = None
        try:
            # Respect pre-injected metrics (tests / overrides)
            metrics = getattr(ctx, "global_stability_metrics", None)

            if metrics is None:
                observer = GlobalStabilityObserver()
                metrics = observer.update(ctx)

                # only write if we computed it
                ctx.global_stability_metrics = metrics

            # otherwise: keep injected metrics untouched

            if metrics is not None:
                w_ratio = getattr(metrics, "ratio", None)
                if w_ratio is not None:
                    ctx.w_bound_ratio = float(w_ratio)
        except Exception:
            pass

        # -----------------------------------------
        # 4. HARD CONSTRAINT EVALUATION
        # -----------------------------------------
        hard_block = False
        hard_reason = None

        # -----------------------------------------
        # Global stability enforcement (HARD)
        # -----------------------------------------
        reasons = []

        if not global_safe:
            reasons.append("global")

        if not switching_safe:
            reasons.append("switching")

        if w_ratio is not None and w_ratio > w_bound_tol:
            reasons.append("exponential_bound")

        hard_block = len(reasons) > 0
        hard_reason = "_".join(reasons) if reasons else None

        if hard_block:
            logger.warning(
                "[GATE][HARD_BLOCK] reasons=%s delta_w=%s w_ratio=%s",
                hard_reason,
                delta_w,
                w_ratio,
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

        # -----------------------------------------
        # 5. PRE-VERDICT (LOCAL)
        # -----------------------------------------

        # -----------------------------------------
        # Stability certificate
        # -----------------------------------------
        stability_certificate = {
            "local": delta_w is not None,
            "global": bool(global_safe),
            "switching": bool(switching_safe),
            "delta_negative": (delta_w is not None and delta_w <= 0),
        }

        # Add exponential stability condition to certificate
        stability_certificate["exponential"] = (
            w_ratio is None or w_ratio <= w_bound_tol
        )

        # -----------------------------------------
        # System confidence (purely mathematical)
        # -----------------------------------------
        confidence_inputs = SystemConfidenceInputs(
            delta_w=delta_w,
            global_safe=bool(global_safe),
            switching_safe=bool(switching_safe),
            has_history=ctx.prev_lyap is not None,
            has_observability=ctx.cur_lyap is not None,
            collapse_risk=float(getattr(ctx, "collapse_risk", 0.0) or 0.0),
         )

        system_confidence = compute_system_confidence(confidence_inputs)

        # Canonical projection: must always be available
        # even when observer is not instantiated (tests/pipeline=None).
        ctx.extra["system_confidence"] = system_confidence

        ctx.system_confidence = system_confidence

        # -----------------------------------------
        # Switching theorem observability
        # -----------------------------------------
        try:
            if ctx.switching_runtime and ctx.switching_params:
                tau_d = float(ctx.switching_runtime.dwell_time())
                k_eff = float(kappa_eff(ctx.switching_params))
                lhs = float(switching_lhs(ctx.switching_runtime, ctx.switching_params))
                switching_metrics = {
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
            else:
                switching_metrics = {}
        except Exception:
            switching_metrics = {}

        # -----------------------------------------
        # KERNEL GATE (math layer extraction)
        # -----------------------------------------
        # -----------------------------------------
        # SAFETY ADAPTER (pipeline → math boundary)
        # Ensures kernel receives strict LyapunovState
        # -----------------------------------------
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
            slow_prev=prev_slow,
            slow_cur=cur_slow,
            symbolic_prev=prev_symbolic,
            symbolic_cur=cur_symbolic,
            collapse_risk=float(getattr(ctx, "collapse_risk", 0.0)),
            stable=ctx.stable,
            switching_safe=bool(switching_safe),
            global_safe=bool(global_safe),
            delta_w=delta_w,
            w_prev=w_prev,
            w_current=w_current,
            adaptive_margin=(
                adaptive_metrics.margin
                if adaptive_metrics and adaptive_metrics.is_available
                else None
            ),
            adaptive_available=bool(
                adaptive_metrics and adaptive_metrics.is_available
            ),
            cognitive_mode=getattr(ctx, "_cognitive_mode", None),
            epsilon=float(getattr(ctx, "_epsilon", 1.0)),
        )

        kernel_result = run_gate_kernel(inputs)
        # merge recovery signals (kernel + observer)
        recovery_detected = recovery_detected or kernel_result.recovery_detected

        if recovery_detected:
            ctx.extra["recovery_detected"] = True

        pre_verdict = kernel_result.pre_verdict

        # -----------------------------------------
        # HARD adaptive veto invariant
        # -----------------------------------------
        if adaptive_metrics and adaptive_metrics.is_available:
            if adaptive_metrics.is_unstable:
                pre_verdict = LyapunovVerdict.ABSTAIN
        # -----------------------------------------
        # BACKWARD COMPATIBILITY (adaptive reasons)
        # -----------------------------------------
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
        # -----------------------------------------
        # BACKWARD COMPAT: marginal adaptive warning
        # -----------------------------------------
        if adaptive_metrics and adaptive_metrics.is_available:
            margin = adaptive_metrics.margin
            if margin is not None and -0.02 < margin <= 0:
                ctx.extra.setdefault("fusion_reasons", []).append(
                    "adaptive_margin_warning"
                )
        
        # -----------------------------------------
        # CONTINUOUS KAPPA MARGIN LAYER (M8)
        # -----------------------------------------
        try:
            kappa_band = None
            kappa_margin = None

            if adaptive_metrics is not None and adaptive_metrics.margin is not None:
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
                        pre_verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

                elif kappa_band == "warning":
                    if "kappa_margin_warning" not in reasons:
                        reasons.append("kappa_margin_warning")

        except Exception:
            pass
    
        if kernel_result.recovery_detected:
            ctx.extra["recovery_detected"] = True

        # sync certificate from math layer
        if kernel_result.certificate:
            stability_certificate.update(kernel_result.certificate)
        
        ctx.stability_certificate = stability_certificate

        # -----------------------------------------
        # MULTI-AXIAL FUSION (single decision point)
        # -----------------------------------------
        try:
            fusion = run_fusion(
                pre_verdict=pre_verdict,
                delta_w=delta_w,
                switching_safe=switching_safe,
                global_safe=bool(global_safe),
                ctx=ctx,
            )
            verdict = fusion.verdict
            # ensure kernel influence is preserved
            if kernel_result.final_verdict == LyapunovVerdict.ABSTAIN:
                verdict = LyapunovVerdict.ABSTAIN
            if adaptive_metrics and adaptive_metrics.is_unstable:
                verdict = LyapunovVerdict.ABSTAIN
            # Merge adaptive + fusion reasons (do NOT overwrite)
            existing = list(ctx.extra.get("fusion_reasons", []))
            ctx.extra["fusion_reasons"] = list(dict.fromkeys(existing + fusion.reasons))

        except Exception:
            # fallback robuste
            verdict = pre_verdict or LyapunovVerdict.ABSTAIN
            existing = list(ctx.extra.get("fusion_reasons", []))
            ctx.extra["fusion_reasons"] = list(
                dict.fromkeys(existing + ["fusion_fallback"])
            )
            ctx.extra["fusion_error"] = True
        
        # -----------------------------------------
        # FINAL recovery override (post-fusion)
        # -----------------------------------------
        if recovery_detected or kernel_result.recovery_detected:
            if verdict == LyapunovVerdict.ABSTAIN:
                 if not (adaptive_metrics and adaptive_metrics.is_unstable):
                     verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
                     ctx.extra.setdefault("fusion_reasons", []).append(
                         "recovery_post_fusion_override"
                     )
                
        # -----------------------------------------
        # VALIDITY ENVELOPE (M9)
        # -----------------------------------------
        try:
            metrics = getattr(ctx, "global_stability_metrics", None)
            kappa_safe = not bool(
                metrics is not None and getattr(metrics, "kappa_violation", False)
            )

            projection_available = (
                ctx.prev_lyap is not None or ctx.cur_lyap is not None
            )
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
        # -----------------------------------------
        # THEORETICAL TRACE (M6)
        # G(x,z,W,kappa,H) → v_t
        # -----------------------------------------
        try:
            metrics = getattr(ctx, "global_stability_metrics", None)

            ctx.extra["theoretical_trace"] = {
                "W": w_current,
                "delta_W": delta_w,
                "kappa_eff": (
                    float(getattr(metrics, "kappa_eff", 0.0))
                    if metrics is not None else None
                ),
                "history_len": len(ctx.delta_w_history),
                "pre_verdict": str(pre_verdict),
                "final_verdict": str(verdict),
            }
        except Exception:
            pass

        # -----------------------------------------
        # CLOSED-LOOP INVARIANT TRACE (M7)
        # W↑ ⇒ control↓ (negative feedback)
        # -----------------------------------------
        try:
            if delta_w is not None:
                ctx.extra["closed_loop_feedback"] = {
                    "energy_increase": bool(delta_w > 0),
                    "energy_decrease": bool(delta_w < 0),
                    "control_should_reduce": bool(delta_w > 0),
                }
        except Exception:
            pass

        # -----------------------------------------
        # ISS PERTURBATION DECOMPOSITION (M8)
        # w = w_proj + w_noise + w_switch + w_adv
        # -----------------------------------------
        try:
            ctx.extra["iss_perturbation"] = {
                "projection": float(getattr(ctx, "projection_disturbance", 0.0) or 0.0),
                "noise": float(getattr(ctx, "noise_disturbance", 0.0) or 0.0),
                "switch": float(getattr(ctx, "switching_disturbance", 0.0) or 0.0),
                "adversarial": float(getattr(ctx, "adversarial_disturbance", 0.0) or 0.0),
            }
        except Exception:
            pass

        # -----------------------------------------
        # VALIDITY ENVELOPE (M9) — enriched trace only
        # (no change to builder contract → safe)
        # -----------------------------------------
        try:
            if ctx.validity_envelope is not None:
                ctx.extra["validity_envelope_extended"] = {
                    **ctx.extra.get("validity_envelope", {}),
                    "projection_valid": bool(ctx.prev_lyap is not None or ctx.cur_lyap is not None),
                    "switching_constraints_valid": bool(switching_safe),
                    "perturbation_bounded": True,  # future hook (M10)
                }
        except Exception:
            pass

        verdict = apply_gate_policy(
            verdict=verdict,
            envelope=envelope,
            adaptive_metrics=adaptive_metrics,
            ctx=ctx,
            kernel_result=kernel_result,
        )

        # -----------------------------------------
        # VALIDITY ENVELOPE ENFORCEMENT (M9)
        # -----------------------------------------
        try:
            validity = getattr(ctx, "validity_envelope", None)
            if validity is not None and not validity.valid:
                ctx.extra.setdefault("fusion_reasons", []).append(f"validity_{validity.reason}")
                if verdict == LyapunovVerdict.ALLOW:
                    verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
        except Exception:
            pass

        # -----------------------------------------
        # HARD KAPPA INVARIANT ENFORCEMENT (FINAL)
        # Must dominate fusion / recovery / policy (M7/M8/M9)
        # -----------------------------------------
        try:
            metrics = getattr(ctx, "global_stability_metrics", None)
            if metrics is not None and getattr(metrics, "kappa_violation", False):
                reasons = ctx.extra.setdefault("fusion_reasons", [])
                if "kappa_violation" not in reasons:
                    reasons.append("kappa_violation")

                ctx.extra["kappa_hard_block"] = True
                ctx.extra["kappa_gap"] = getattr(metrics, "kappa_gap", None)

                verdict = LyapunovVerdict.ABSTAIN
        except Exception:
            pass

        # -----------------------------------------
        # Final math-aligned observability payloads
        # -----------------------------------------
        try:
            metrics = getattr(ctx, "global_stability_metrics", None)
            ctx.extra["theoretical_trace"] = {
                "W": w_current,
                "delta_W": delta_w,
                "kappa_eff": (
                    float(getattr(metrics, "kappa_eff", 0.0))
                    if metrics is not None else None
                ),
                "history_len": len(ctx.delta_w_history),
                "pre_verdict": str(pre_verdict),
                "final_verdict": str(verdict),
            }
        except Exception:
            pass

        # -----------------------------------------
        # OBSERVABILITY (extracted layer)
        # -----------------------------------------
        gate_observer = None
        if pipeline is not None:
            gate_observer = getattr(pipeline, "gate_observer", None)
            if gate_observer is None:
                gate_observer = GateObserver()
                pipeline.gate_observer = gate_observer

        if gate_observer is not None:
            gate_observer.build(
                ctx,
                pre_verdict=pre_verdict,
                final_verdict=verdict,
                delta_w=delta_w,
                w_prev=w_prev,
                w_current=w_current,
                adaptive_metrics=adaptive_metrics,
                switching_safe=switching_safe,
                global_safe=global_safe,
                envelope=envelope,
                confidence_inputs=confidence_inputs,
                system_confidence=system_confidence,
                switching_metrics=switching_metrics,
                stability_certificate=stability_certificate,
                hard_block=hard_block,
                hard_reason=hard_reason,
                w_ratio=w_ratio,
                recovery_detected=recovery_detected,
                recovery_magnitude=abs(delta_w) if (delta_w is not None and recovery_detected) else None,
            )
        else:
            ctx.extra.setdefault("confidence_flags", [])

        # -----------------------------------------
        # CLOSED-LOOP INVARIANT TRACE (M7)
        # W↑ ⇒ control↓ (negative feedback)
        # -----------------------------------------
        try:
            if delta_w is not None:
                ctx.extra["closed_loop_feedback"] = {
                    "energy_increase": bool(delta_w > 0),
                    "energy_decrease": bool(delta_w < 0),
                    "control_should_reduce": bool(delta_w > 0),
                }
        except Exception:
            pass

        # -----------------------------------------
        # ISS PERTURBATION DECOMPOSITION (M8)
        # -----------------------------------------
        try:
            ctx.extra["iss_perturbation"] = {
                "projection": float(getattr(ctx, "projection_disturbance", 0.0) or 0.0),
                "noise": float(getattr(ctx, "noise_disturbance", 0.0) or 0.0),
                "switch": float(getattr(ctx, "switching_disturbance", 0.0) or 0.0),
                "adversarial": float(getattr(ctx, "adversarial_disturbance", 0.0) or 0.0),
            }
        except Exception:
            pass

        # -----------------------------------------
        # VALIDITY ENVELOPE (M9) — enriched trace only
        # -----------------------------------------
        try:
            if ctx.validity_envelope is not None:
                ctx.extra["validity_envelope_extended"] = {
                    **ctx.extra.get("validity_envelope", {}),
                    "projection_valid": bool(ctx.prev_lyap is not None or ctx.cur_lyap is not None),
                    "switching_constraints_valid": bool(switching_safe),
                    "perturbation_bounded": True,
                }
        except Exception:
            pass

        # -----------------------------------------
        # HARD adaptive veto invariant (final)
        # -----------------------------------------
        if adaptive_metrics and adaptive_metrics.is_unstable:
            verdict = LyapunovVerdict.ABSTAIN

        if "fusion_trace" in ctx.extra:
            ctx.extra["fusion_trace"]["final_verdict"] = str(verdict)

        ctx.gate_result = verdict

        