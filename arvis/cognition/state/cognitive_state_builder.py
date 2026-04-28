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
from arvis.signals.signal_journal import SignalJournal


class CognitiveStateBuilder:
    """
    Canonical builder from pipeline context.
    """

    @staticmethod
    def from_context(ctx: "CognitivePipelineContext") -> CognitiveState:
        ir = StateIRAdapter.from_context(ctx)
        risk = ir.collapse_risk

        # -----------------------------------------
        # TIMELINE NORMALIZATION
        # -----------------------------------------
        timeline_obj = getattr(ctx, "timeline", None)
        timeline: SignalJournal

        if isinstance(timeline_obj, SignalJournal):
            timeline = timeline_obj
        else:
            timeline = SignalJournal()

        # -----------------------------------------
        # IR BRIDGE
        # -----------------------------------------
        ir_input = getattr(ctx, "ir_input", None)
        ir_context = getattr(ctx, "ir_context", None)
        ir_decision = getattr(ctx, "ir_decision", None)
        ir_state = getattr(ctx, "ir_state", None)
        ir_gate = getattr(ctx, "ir_gate", None)

        return CognitiveState(
            bundle_id=ir.bundle_id,
            decision=getattr(ctx, "action_decision", None),
            trace=getattr(ctx, "trace", None),
            timeline=timeline,
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
            #  IR ATTACHMENT
            # -----------------------------------------
            ir_input=ir_input,
            ir_context=ir_context,
            ir_decision=ir_decision,
            ir_state=ir_state,
            ir_gate=ir_gate,
            # -----------------------------------------
            # TOOL EXECUTION TRACE
            # -----------------------------------------
            tool_results=list(ctx.extra.get("tool_results", [])),
        )
