# arvis/adapters/ir/cognitive_ir_builder.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from arvis.ir.cognitive_ir import CognitiveIR


class CognitiveIRBuilder:
    @staticmethod
    def from_context(ctx: Any) -> CognitiveIR:
        """
        Build canonical IR from pipeline context.

        Pure projection:
        - no logic
        - no mutation
        - no side effects
        """

        tool_results: Optional[List[Dict[str, Any]]] = None

        extra = getattr(ctx, "extra", None)
        if isinstance(extra, dict):
            results = extra.get("tool_results", [])
            if results:
                tool_results = [
                    {
                        "tool_name": r.tool_name,
                        "success": r.success,
                        "output": r.output,
                        "error": r.error,
                        "latency_ms": getattr(r, "latency_ms", None),
                    }
                    for r in results
                ]

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
            tools=tool_results,
        )
