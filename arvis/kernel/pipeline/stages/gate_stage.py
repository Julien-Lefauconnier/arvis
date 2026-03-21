# arvis/kernel/pipeline/stages/gate_stage.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
import logging

from arvis.math.lyapunov.lyapunov_gate import (
    lyapunov_gate,
    LyapunovVerdict,
    LyapunovGateParams,
)
from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov
from arvis.math.switching.switching_params import switching_condition
from arvis.math.switching.switching_params import switching_lhs, kappa_eff
from arvis.math.control.eps_adaptive import CognitiveMode
from arvis.cognition.control.cognitive_control_snapshot import CognitiveControlSnapshot
from arvis.math.stability.global_guard import GlobalStabilityGuard
from arvis.math.switching.global_stability_observer import GlobalStabilityObserver
from arvis.math.decision.multiaxial_fusion import multiaxial_fusion, MultiaxialInputs
from arvis.math.confidence.system_confidence import SystemConfidenceInputs, compute_system_confidence
from arvis.math.control.confidence_control import apply_confidence_control, ConfidenceControlInputs

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

        HIGH_RISK_THRESHOLD = 0.8

        # Configurable thresholds
        delta_w_strict = getattr(pipeline, "delta_w_strict_threshold", 0.1)
        delta_w_monitor = getattr(pipeline, "delta_w_monitor_threshold", 0.2)
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
            if prev_slow is not None and cur_slow is not None:
                slow_delta = abs(cur_slow - prev_slow)
                if delta_w is not None and delta_w > 0 and slow_delta < 1e-3:
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
            observer = GlobalStabilityObserver()
            metrics = observer.update(ctx)
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
            ctx.extra["hard_block_log"] = {
                "reasons": hard_reason,
                "delta_w": delta_w,
                "w_ratio": w_ratio,
            }

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
        ctx.stability_certificate = {
            "local": delta_w is not None,
            "global": bool(global_safe),
            "switching": bool(switching_safe),
            "delta_negative": (delta_w is not None and delta_w <= 0),
        }

        # Add exponential stability condition to certificate
        ctx.stability_certificate["exponential"] = (
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

        ctx.system_confidence = system_confidence
        ctx.extra["system_confidence"] = system_confidence

        # -----------------------------------------
        # Switching theorem observability
        # -----------------------------------------
        try:
            if ctx.switching_runtime and ctx.switching_params:
                tau_d = float(ctx.switching_runtime.dwell_time())
                k_eff = float(kappa_eff(ctx.switching_params))
                lhs = float(switching_lhs(ctx.switching_runtime, ctx.switching_params))
                ctx.switching_metrics = {
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
                ctx.switching_metrics = {}
        except Exception:
            ctx.switching_metrics = {}

        # -----------------------------------------
        # PRE-VERDICT (local reasoning only)
        # -----------------------------------------
        pre_verdict = LyapunovVerdict.ABSTAIN
        # Local Lyapunov veto (strong instability detection)
        mode = getattr(pipeline, "theoretical_enforcement_mode", "monitor")

        if ctx.stable is False:
            pre_verdict = LyapunovVerdict.ABSTAIN

        elif float(ctx.collapse_risk) >= HIGH_RISK_THRESHOLD:
            pre_verdict = LyapunovVerdict.ABSTAIN

        elif ctx._cognitive_mode == CognitiveMode.CRITICAL:
            pre_verdict = LyapunovVerdict.ABSTAIN

        elif ctx.cur_lyap is None:
            pre_verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

        elif ctx.prev_lyap is None:
            print("[GATE] No prev_lyap → REQUIRE_CONFIRMATION")
            pre_verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

        else:
            previous = ctx.prev_lyap or ctx.cur_lyap

            params = LyapunovGateParams(
                eps_override=ctx._epsilon
            )

            pre_verdict = lyapunov_gate(
                previous=previous,
                current=ctx.cur_lyap,
                params=params,
                prev_slow=prev_slow,
                current_slow=cur_slow,
                prev_symbolic=prev_symbolic,
                current_symbolic=cur_symbolic,
            )
        # Local Lyapunov veto / warning must override AFTER baseline verdict selection
        if delta_w is not None:
            if mode == "strict" and delta_w > delta_w_strict:
                pre_verdict = LyapunovVerdict.ABSTAIN
            elif mode != "strict" and delta_w > delta_w_monitor:
                ctx.extra["delta_instability_warning"] = True
                if pre_verdict == LyapunovVerdict.ALLOW:
                    pre_verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

        # -----------------------------------------
        # Slow drift veto (strict mode only)
        # -----------------------------------------
        if (
            mode == "strict"
            and ctx.extra.get("slow_drift_warning")
            and pre_verdict != LyapunovVerdict.ABSTAIN
        ):
            if pre_verdict == LyapunovVerdict.ALLOW:
                pre_verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
            ctx.extra.setdefault("fusion_reasons", []).append("slow_drift_veto")

        # -----------------------------------------
        # MULTI-AXIAL FUSION (single decision point)
        # -----------------------------------------
        try:
            fusion = multiaxial_fusion(
                MultiaxialInputs(
                    fast_verdict=pre_verdict,
                    delta_w=delta_w,
                    switching_safe=switching_safe,
                    global_safe=bool(global_safe),
                    use_composite=getattr(ctx, "use_paper_composite_gate", False),
                    global_action=str(getattr(ctx, "global_stability_action", "ignore")),
                )
            )

            verdict = fusion.verdict
            ctx.extra["fusion_reasons"] = fusion.reasons

        except Exception:
            # fallback robuste
            verdict = pre_verdict or LyapunovVerdict.ABSTAIN
            ctx.extra["fusion_reasons"] = ["fusion_fallback"]
            ctx.extra["fusion_error"] = True
        
        ctx.extra.setdefault("confidence_flags", [])
        ctx.extra["fusion_trace"] = {
            "pre_verdict": str(pre_verdict),
            "delta_w": delta_w,
            "global_safe": bool(global_safe),
            "switching_safe": bool(switching_safe),
            "confidence_inputs": {
                "delta_w": confidence_inputs.delta_w,
                "global_safe": confidence_inputs.global_safe,
                "switching_safe": confidence_inputs.switching_safe,
                "has_history": confidence_inputs.has_history,
                "has_observability": confidence_inputs.has_observability,
                "collapse_risk": confidence_inputs.collapse_risk,
            },
            "system_confidence": float(system_confidence),
            "reasons": list(ctx.extra.get("fusion_reasons", [])),
        }

        # -----------------------------------------
        # 6. STRICT THEORETICAL MODE
        # -----------------------------------------
        mode = getattr(pipeline, "theoretical_enforcement_mode", "monitor")

        if mode == "strict" and envelope.hard_block:
            verdict = LyapunovVerdict.ABSTAIN
            ctx.extra.setdefault("fusion_reasons", []).append(
                f"strict_veto_{envelope.hard_reason}"
            )

        # -----------------------------------------
        # 7. POLICY LAYER
        # -----------------------------------------

        action = getattr(ctx, "global_stability_action", "ignore")

        # Policy override is intended for GLOBAL instability handling.
        if envelope.hard_block:
            if "global" in (envelope.hard_reason or ""):
                if action == "abstain":
                    verdict = LyapunovVerdict.ABSTAIN
                    ctx.extra.setdefault("fusion_reasons", []).append(
                        "global_instability_abstain"
                    )
                elif action == "confirm":
                    verdict = LyapunovVerdict.REQUIRE_CONFIRMATION
                    ctx.extra.setdefault("fusion_reasons", []).append(
                        "global_instability_confirm"
                    )
                else:
                    # ignore → no-op (no trace, no override)
                    pass
            else:
                ctx.extra.setdefault("fusion_reasons", []).append(
                    f"hard_block_policy_{action}_{envelope.hard_reason}"
                )
        
        # Final trace must reflect the actual final verdict after strict/policy layers
        ctx.extra["fusion_trace"]["final_verdict"] = str(verdict)
        
        ctx.gate_result = verdict

        base = ctx.control_snapshot
        ctx.extra.setdefault("confidence_flags", [])
        if base is None:
            ctx.gate_result = verdict
            return
        # -----------------------------------------
        # Confidence-driven control (pilotage)
        # -----------------------------------------
        control = apply_confidence_control(
            ConfidenceControlInputs(
                system_confidence=system_confidence,
                base_epsilon=base.epsilon,
                exploration=base.exploration,
            )
        )

        # -----------------------------------------
        # Lyapunov-informed control modulation
        # -----------------------------------------
        rec = ctx.extra.get("composite_gate_recommendation")

        # Immutable update (ConfidenceControlOutput is frozen)
        new_epsilon = control.epsilon
        new_exploration = control.exploration
        new_flags = list(control.flags)

        if rec == "strong_decrease":
            new_epsilon *= 0.8
            new_exploration *= 0.7
            new_flags.append("composite_strong_decrease")
        elif rec == "soft_decrease":
            new_epsilon *= 0.9
            new_flags.append("composite_soft_decrease")
        elif rec == "strong_increase":
            new_epsilon *= 1.1
            new_exploration *= 1.1
            new_flags.append("composite_strong_increase")

        control = type(control)(
            epsilon=new_epsilon,
            exploration=new_exploration,
            flags=new_flags,
        )

        ctx.extra["confidence_flags"] = list(control.flags)

        if "very_low_confidence" in control.flags:
            ctx.extra["low_confidence_escalation"] = True

        ctx.control_snapshot = CognitiveControlSnapshot(
            gate_mode=base.gate_mode,
            epsilon=control.epsilon,
            smoothed_risk=base.smoothed_risk,
            lyap_verdict=verdict,
            exploration=control.exploration,
            drift=base.drift,
            regime=base.regime,
            calibration=base.calibration,
            temporal_pressure=getattr(ctx, "temporal_pressure", None),
            temporal_modulation=getattr(ctx, "temporal_modulation", None),
        )

