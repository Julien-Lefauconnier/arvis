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
        base_exploration_scalar = _exploration_scalar(base.exploration)
        control = apply_confidence_control(
            ConfidenceControlInputs(
                system_confidence=system_confidence,
                base_epsilon=base.epsilon,
                exploration=base_exploration_scalar,
            )
        )

        new_epsilon = control.epsilon
        new_exploration = _restore_exploration_shape(
            base.exploration,
            control.exploration,
        )
        new_flags = list(getattr(control, "flags", []))

        # -----------------------------------------
        # Lyapunov feedback
        # -----------------------------------------
        if rec == "strong_decrease":
            new_epsilon *= 0.8
            new_exploration = _scale_exploration(new_exploration, 0.7)
            new_flags.append("composite_strong_decrease")

        elif rec == "soft_decrease":
            new_epsilon *= 0.9
            new_flags.append("composite_soft_decrease")

        elif rec == "strong_increase":
            new_epsilon *= 1.1
            new_exploration = _scale_exploration(new_exploration, 1.1)
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


def _exploration_scalar(value: Any) -> float:
    """
    Extract scalar exploration value for math/control layer.
    """

    if isinstance(value, (int, float)):
        return float(value)

    if hasattr(value, "exploration_factor"):
        try:
            return float(value.exploration_factor)
        except (AttributeError, TypeError, ValueError, OverflowError):
            return 1.0

    return 1.0


def _restore_exploration_shape(original: Any, scalar: float) -> Any:
    """
    Preserve snapshot shape when the input exploration was structured.
    """

    if hasattr(original, "exploration_factor"):
        return _scale_exploration(original, scalar / _exploration_scalar(original))

    return float(scalar)


def _scale_exploration(value: Any, factor: float) -> Any:
    """
    Safely scales exploration structures.

    Supports:
    - float exploration
    - dataclass snapshots exposing exploration_factor
    """

    if isinstance(value, (int, float)):
        return float(value) * factor

    if hasattr(value, "exploration_factor"):
        try:
            from dataclasses import replace

            return replace(
                value,
                exploration_factor=float(value.exploration_factor) * factor,
            )
        except (AttributeError, TypeError, ValueError, OverflowError):
            return value

    return value
