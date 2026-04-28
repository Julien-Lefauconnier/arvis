# arvis/kernel/pipeline/stages/control_feedback_stage.py

from __future__ import annotations

from typing import Any

from arvis.cognition.control.cognitive_control_snapshot import CognitiveControlSnapshot
from arvis.math.control.confidence_control import (
    ConfidenceControlInputs,
    apply_confidence_control,
)


class ControlFeedbackStage:
    """
    Post-gate control adjustment.

    Responsibilities:
    - Apply confidence-based control
    - Apply Lyapunov-informed modulation
    - Update control_snapshot
    """

    def run(self, pipeline: Any, ctx: Any) -> None:
        gate_result = getattr(ctx, "gate_result", None)

        # Gate not executed yet → skip
        if gate_result is None:
            return

        base = getattr(ctx, "control_snapshot", None)
        if base is None:
            return

        system_confidence = float(getattr(ctx, "system_confidence", 0.0))
        rec = ctx.extra.get("composite_gate_recommendation")

        # -----------------------------------------
        # Confidence control
        # -----------------------------------------
        control = apply_confidence_control(
            ConfidenceControlInputs(
                system_confidence=system_confidence,
                base_epsilon=base.epsilon,
                exploration=base.exploration,
            )
        )

        new_epsilon = control.epsilon
        new_exploration = control.exploration
        new_flags = list(control.flags)

        # -----------------------------------------
        # Lyapunov feedback
        # -----------------------------------------
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

        # -----------------------------------------
        # Flags
        # -----------------------------------------
        ctx.extra["confidence_flags"] = list(new_flags)

        if "very_low_confidence" in new_flags:
            ctx.extra["low_confidence_escalation"] = True

        # -----------------------------------------
        # Snapshot update
        # -----------------------------------------
        ctx.control_snapshot = CognitiveControlSnapshot(
            gate_mode=base.gate_mode,
            epsilon=new_epsilon,
            smoothed_risk=base.smoothed_risk,
            lyap_verdict=gate_result,
            exploration=new_exploration,
            drift=base.drift,
            regime=base.regime,
            calibration=base.calibration,
            temporal_pressure=getattr(ctx, "temporal_pressure", None),
            temporal_modulation=getattr(ctx, "temporal_modulation", None),
        )
        ctx._effective_epsilon = float(new_epsilon)
