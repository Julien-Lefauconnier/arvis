# arvis/kernel/pipeline/stages/control_stage.py

from __future__ import annotations

from typing import Any
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.signals import UncertaintySignal
from arvis.math.control.eps_adaptive import CognitiveMode
from arvis.cognition.control.cognitive_control_snapshot import CognitiveControlSnapshot
from arvis.uncertainty.uncertainty_to_intent_mapper import map_uncertainty_to_intent


class ControlStage:

    def run(self, pipeline: Any, ctx: Any) -> None:

        # -----------------------------------------
        # 1. HYSTERESIS
        # -----------------------------------------
        gate_mode_raw = pipeline.hysteresis.update(
            user_id=ctx.user_id,
            risk=float(ctx.collapse_risk),
        )

        if isinstance(gate_mode_raw, CognitiveMode):
            cognitive_mode = gate_mode_raw
        else:
            cognitive_mode = CognitiveMode.NORMAL

        # -----------------------------------------
        # 2. UNCERTAINTY
        # -----------------------------------------
        ctx.uncertainty = UncertaintySignal(float(ctx.collapse_risk))

        try:
            ctx.uncertainty_intent = map_uncertainty_to_intent(ctx.uncertainty)
        except Exception:
            ctx.uncertainty_intent = None

        # -----------------------------------------
        # 3. EPSILON
        # -----------------------------------------
        epsilon = pipeline.epsilon_controller.compute(
            uncertainty=float(ctx.uncertainty),
            budget_used=0.5,
            delta_v=float(ctx.drift_score),
            collapse_risk=float(ctx.collapse_risk),
            latent_volatility=min(1.0, abs(float(ctx.drift_score))),
            mode=cognitive_mode,
        )

        # -----------------------------------------
        # 4. REGIME POLICY
        # -----------------------------------------
        regime_control = pipeline.regime_policy.compute(
            ctx.regime or "neutral"
        )

        # -----------------------------------------
        # 5. MODULATION
        # -----------------------------------------
        epsilon *= getattr(regime_control, "epsilon_multiplier", 1.0)
        epsilon *= getattr(ctx.temporal_modulation, "epsilon_multiplier", 1.0)

        # -----------------------------------------
        # 6. EXPLORATION
        # -----------------------------------------
        exploration_snapshot = pipeline.exploration.compute(
            regime=ctx.regime,
            collapse_risk=float(ctx.collapse_risk),
            drift_score=float(ctx.drift_score),
            stable=ctx.stable,
        )

        # -----------------------------------------
        # 7. SNAPSHOT
        # -----------------------------------------
        control_snapshot = CognitiveControlSnapshot(
            gate_mode=cognitive_mode,
            epsilon=float(epsilon),
            smoothed_risk=float(ctx.collapse_risk),
            lyap_verdict=LyapunovVerdict.ABSTAIN,
            exploration=exploration_snapshot,
            drift={
                "score": float(ctx.drift_score),
                "confidence": ctx.regime_confidence,
            },
            regime=regime_control,
            calibration=None,
        )

        ctx.control_snapshot = control_snapshot
        ctx._epsilon = epsilon  # used later by gate
        ctx._cognitive_mode = cognitive_mode