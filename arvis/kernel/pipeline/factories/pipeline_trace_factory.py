# arvis/kernel/pipeline/factories/pipeline_trace_factory.py

from __future__ import annotations

from datetime import UTC, datetime

from arvis.cognition.gate.cognitive_gate_result import (
    CognitiveGateResult,
)
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.context.scientific_accessors import (
    fast_dynamics,
    perturbation,
    quadratic_comparability,
    quadratic_lyap_snapshot,
    symbolic_state,
    theoretical_regime,
)
from arvis.kernel.trace.decision_trace import DecisionTrace


class PipelineTraceFactory:
    @staticmethod
    def build(
        ctx: CognitivePipelineContext,
        normalized_gate_result: CognitiveGateResult,
    ) -> DecisionTrace:
        return DecisionTrace(
            timestamp=datetime.now(UTC),
            user_id=ctx.user_id,
            gate_result=normalized_gate_result,
            confirmation_request=ctx.confirmation_request,
            confirmation_result=ctx.confirmation_result,
            action_decision=ctx.action_decision,
            executable_intent=ctx.executable_intent,
            conflict=ctx.extra.get("conflict"),
            predictive=ctx.predictive_snapshot,
            stability=ctx.global_stability,
            symbolic=symbolic_state(ctx),
            system_tension=ctx.observability.system_tension,
            quadratic_lyapunov=quadratic_lyap_snapshot(ctx),
            quadratic_comparability=quadratic_comparability(ctx),
            theoretical_regime=theoretical_regime(ctx),
            fast_dynamics=fast_dynamics(ctx),
            perturbation=perturbation(ctx),
            conversation=ctx.conversation_signal,
            governance=ctx.governance,
            pending_actions=ctx.pending_actions,
            events=ctx.events,
            coherence_policy=ctx.coherence_policy,
            memory_influence=getattr(
                ctx.decision_layer.decision_result,
                "memory_influence",
                None,
            ),
        )
