# arvis/cognition/state/cognitive_state_builder.py

from __future__ import annotations

from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.cognition.state.cognitive_state import (
    CognitiveState,
    CognitiveStability,
    CognitiveRisk,
    CognitiveControl,
    CognitiveDynamics,
    CognitiveProjection,
)

from arvis.adapters.ir.state_adapter import StateIRAdapter


class CognitiveStateBuilder:
    """
    Canonical builder from pipeline context.
    """

    @staticmethod
    def from_context(ctx: "CognitivePipelineContext") -> CognitiveState:
        ir = StateIRAdapter.from_context(ctx)
        risk = ir.collapse_risk

        return CognitiveState(
            bundle_id=ir.bundle_id,

            stability=CognitiveStability(
                dv=ir.dv,
                regime=getattr(ir, "regime", None),
                stable=getattr(ir, "stable", None),
            ),

            risk=CognitiveRisk(
                mh_risk=risk.mh_risk,
                world_risk=risk.world_risk,
                forecast_risk=risk.forecast_risk,
                fused_risk=risk.fused_risk,
                smoothed_risk=risk.smoothed_risk,
                early_warning=ir.early_warning,
            ),

            control=CognitiveControl(
                epsilon=ir.epsilon,
            ),

            dynamics=CognitiveDynamics(
                system_tension=getattr(ir, "system_tension", None),
                drift=getattr(ir, "drift", None),
            ),

            projection=(
                CognitiveProjection(
                    valid=getattr(ir, "projection_valid", None),
                    margin=getattr(ir, "projection_margin", None),
                )
                if getattr(ir, "projection_valid", None) is not None
                else None
            ),

            world_prediction=ir.world_prediction,
            forecast=ir.forecast,

            irg=ir.irg,
            # -----------------------------------------
            # TOOL EXECUTION TRACE (NEW)
            # -----------------------------------------
            tool_results=list(ctx.extra.get("tool_results", [])),
        )