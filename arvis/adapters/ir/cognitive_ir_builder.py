# arvis/adapters/ir/cognitive_ir_builder.py

from __future__ import annotations

from arvis.ir.cognitive_ir import CognitiveIR


class CognitiveIRBuilder:

    @staticmethod
    def from_context(ctx: object) -> CognitiveIR:
        """
        Build canonical IR from pipeline context.

        Pure projection:
        - no logic
        - no mutation
        - no side effects
        """

        return CognitiveIR(
            input=getattr(ctx, "ir_input", None),
            context=getattr(ctx, "ir_context", None),
            decision=getattr(ctx, "ir_decision", None),
            state=getattr(ctx, "ir_state", None),
            gate=getattr(ctx, "ir_gate", None),
            projection=getattr(ctx, "ir_projection", None),
            validity=getattr(ctx, "ir_validity", None),
            stability=getattr(ctx, "ir_stability", None),
            adaptive=getattr(ctx, "ir_adaptive", None),
        )