# arvis/kernel/pipeline/stages/control_stage.py

from __future__ import annotations

from typing import Any

from arvis.cognition.control.cognitive_control_snapshot import CognitiveControlSnapshot
from arvis.kernel.pipeline.context.scientific_accessors import (
    adaptive_snapshot as get_adaptive_snapshot,
)
from arvis.kernel.pipeline.context.scientific_accessors import (
    collapse_risk as get_collapse_risk,
)
from arvis.kernel.pipeline.context.scientific_accessors import (
    drift_score as get_drift_score,
)
from arvis.kernel.pipeline.context.scientific_accessors import (
    regime as get_regime,
)
from arvis.kernel.pipeline.context.scientific_accessors import (
    stable as get_stable,
)
from arvis.math.adaptive.adaptive_control_policy import AdaptiveControlPolicy
from arvis.math.control.eps_adaptive import CognitiveMode
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.signals import UncertaintySignal
from arvis.uncertainty.uncertainty_to_intent_mapper import map_uncertainty_to_intent


class ControlStage:
    def __init__(self) -> None:
        # Lazy adaptive control (safe: no dependency on pipeline init)
        self._adaptive_policy = AdaptiveControlPolicy()

    def run(self, pipeline: Any, ctx: Any) -> None:
        # -----------------------------------------
        # 1. HYSTERESIS
        # -----------------------------------------
        gate_mode_raw = pipeline.hysteresis.update(
            user_id=ctx.user_id,
            risk=float(get_collapse_risk(ctx)),
        )

        if isinstance(gate_mode_raw, CognitiveMode):
            cognitive_mode = gate_mode_raw
        else:
            cognitive_mode = CognitiveMode.NORMAL

        # -----------------------------------------
        # 2. UNCERTAINTY
        # -----------------------------------------
        ctx.scientific.core.uncertainty = UncertaintySignal(
            float(get_collapse_risk(ctx))
        )

        try:
            ctx.scientific.core.uncertainty_intent = map_uncertainty_to_intent(
                ctx.scientific.core.uncertainty
            )
        except (AttributeError, TypeError, ValueError, OverflowError):
            ctx.scientific.core.uncertainty_intent = None

        # -----------------------------------------
        # 3. TEMPORAL
        # -----------------------------------------
        if getattr(ctx, "timeline", None):
            ctx.temporal_pressure = 1.0
            ctx.temporal_modulation = type("Tmp", (), {"epsilon_multiplier": 1.2})()
        else:
            ctx.temporal_pressure = 0.0
            ctx.temporal_modulation = type("Tmp", (), {"epsilon_multiplier": 1.0})()

        # -----------------------------------------
        # 4. EPSILON
        # -----------------------------------------
        epsilon = pipeline.epsilon_controller.compute(
            uncertainty=float(ctx.scientific.core.uncertainty),
            budget_used=0.5,
            delta_v=float(get_drift_score(ctx)),
            collapse_risk=float(get_collapse_risk(ctx)),
            latent_volatility=min(
                1.0,
                abs(float(get_drift_score(ctx))),
            ),
            mode=cognitive_mode,
        )

        # -----------------------------------------
        # 5. REGIME POLICY
        # -----------------------------------------
        regime_control = pipeline.regime_policy.compute(get_regime(ctx) or "neutral")

        # -----------------------------------------
        # 6. MODULATION
        # -----------------------------------------
        epsilon *= getattr(regime_control, "epsilon_multiplier", 1.0)
        epsilon *= getattr(ctx.temporal_modulation, "epsilon_multiplier", 1.0)

        if getattr(ctx, "timeline", None):
            ctx.temporal_pressure = 1.0
            ctx.temporal_modulation = type("Tmp", (), {"epsilon_multiplier": 1.2})()
        else:
            ctx.temporal_pressure = 0.0
            ctx.temporal_modulation = type("Tmp", (), {"epsilon_multiplier": 1.0})()

        # -----------------------------------------
        # 6.5 MEMORY-AWARE MODULATION (OS layer)
        # -----------------------------------------
        try:
            decision_layer = getattr(ctx, "decision_layer", None)
            decision_layer = getattr(ctx, "decision_layer", None)
            bundle = getattr(decision_layer, "bundle", None)
            memory_features = getattr(bundle, "memory_features", {}) if bundle else {}

            memory_pressure = float(memory_features.get("memory_pressure", 0.0))
            has_constraints = bool(memory_features.get("has_constraints", False))

            # ---------------------------------
            # pressure → reduce exploration
            # ---------------------------------
            if memory_pressure > 0.7:
                epsilon *= 0.5
                ctx.memory_mode = "constrained"

            elif memory_pressure > 0.3:
                epsilon *= 0.8
                ctx.memory_mode = "moderate"

            else:
                ctx.memory_mode = "free"

            # ---------------------------------
            # constraints → enforce safety bias
            # ---------------------------------
            if has_constraints:
                epsilon *= 0.7
                ctx.memory_constraints_active = True
            else:
                ctx.memory_constraints_active = False

        except (AttributeError, TypeError, ValueError, OverflowError):
            ctx.memory_mode = None
            ctx.memory_constraints_active = False

        # -----------------------------------------
        # 7. EXPLORATION
        # -----------------------------------------
        exploration_snapshot = pipeline.exploration.compute(
            regime=get_regime(ctx),
            collapse_risk=float(get_collapse_risk(ctx)),
            drift_score=float(get_drift_score(ctx)),
            stable=get_stable(ctx),
        )

        # -----------------------------------------
        # 8. ADAPTIVE CONTROL
        # -----------------------------------------
        adaptive_snapshot = get_adaptive_snapshot(ctx)

        if adaptive_snapshot and adaptive_snapshot.is_available:
            try:
                ctrl = self._adaptive_policy.compute(
                    kappa_eff=adaptive_snapshot.kappa_eff,
                    margin=adaptive_snapshot.margin,
                    regime=adaptive_snapshot.regime,
                )

                # --- Apply safe multiplicative modulation ---
                epsilon *= ctrl.exploration_scale

                # -----------------------------------------
                # Continuous kappa margin regulation (M8)
                # -----------------------------------------
                margin = adaptive_snapshot.margin
                if margin is not None:
                    if margin > 0.0:
                        epsilon *= 0.25
                        ctx.kappa_band = "hard"
                    elif margin > -0.02:
                        epsilon *= 0.5
                        ctx.kappa_band = "critical"
                    elif margin > -0.05:
                        epsilon *= 0.8
                        ctx.kappa_band = "warning"
                    else:
                        ctx.kappa_band = "stable"
                # -----------------------------------------
                # HARD SAFETY: unstable regime clamp
                # -----------------------------------------
                if adaptive_snapshot.is_unstable:
                    epsilon *= 0.5  # conservative fallback

                # Optional: enrich context for downstream stages
                ctx.adaptive_control = ctrl

            except Exception:  # arvis-broad: fail-soft control stage
                ctx.adaptive_control = None
        else:
            ctx.adaptive_control = None

        confidence = getattr(ctx, "regime_confidence", None)

        if confidence is None:
            confidence = 0.0  # safe fallback

        # -----------------------------------------
        # 9. SNAPSHOT
        # -----------------------------------------
        control_snapshot = CognitiveControlSnapshot(
            gate_mode=cognitive_mode,
            epsilon=float(epsilon),
            smoothed_risk=float(get_collapse_risk(ctx)),
            lyap_verdict=LyapunovVerdict.ABSTAIN,
            exploration=exploration_snapshot,
            drift={
                "score": float(get_drift_score(ctx)),
                "confidence": float(confidence),
            },
            regime=regime_control,
            calibration=None,
            temporal_pressure=ctx.temporal_pressure,
            temporal_modulation=ctx.temporal_modulation,
        )

        ctx.control_snapshot = control_snapshot
        ctx._epsilon = epsilon  # used later by gate
        ctx._effective_epsilon = float(epsilon)
        ctx._cognitive_mode = cognitive_mode
