# arvis/kernel/pipeline/factories/pipeline_trace_factory.py

from __future__ import annotations

from datetime import datetime, timezone

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.trace.decision_trace import DecisionTrace
from arvis.cognition.gate.cognitive_gate_result import (
    CognitiveGateResult,
)


class PipelineTraceFactory:

    @staticmethod
    def build(
        ctx: CognitivePipelineContext,
        normalized_gate_result: CognitiveGateResult,
    ) -> DecisionTrace:
        return DecisionTrace(
            timestamp=datetime.now(timezone.utc),
            user_id=ctx.user_id,
            gate_result=normalized_gate_result,
            confirmation_request=ctx.confirmation_request,
            confirmation_result=ctx.confirmation_result,
            action_decision=ctx.action_decision,
            executable_intent=ctx.executable_intent,
            conflict=ctx.extra.get("conflict"),
            predictive=ctx.predictive_snapshot,
            stability=ctx.global_stability,
            symbolic=ctx.symbolic_state,
            system_tension=ctx.system_tension,
            quadratic_lyapunov=ctx.quadratic_lyap_snapshot,
            quadratic_comparability=ctx.quadratic_comparability,
            theoretical_regime=ctx.theoretical_regime,
            fast_dynamics=ctx.fast_dynamics,
            perturbation=ctx.perturbation,
            conversation=ctx.conversation_signal,
            governance=ctx.governance,
            pending_actions=ctx.pending_actions,
            events=ctx.events,
            coherence_policy=ctx.coherence_policy,
            memory_influence=getattr(
                ctx.decision_result,
                "memory_influence",
                None,
            ),
        )