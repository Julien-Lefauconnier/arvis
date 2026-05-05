# arvis/kernel/pipeline/stages/gate/observability.py

from __future__ import annotations

from typing import Any

from arvis.kernel.observability.gate_observer import GateObserver
from arvis.kernel.pipeline.stages.gate.models import (
    CompositeMetrics,
    GateDecisionResult,
    StabilityAssessment,
)


def finalize_observability(
    pipeline: Any,
    ctx: Any,
    composite: CompositeMetrics,
    assessment: StabilityAssessment,
    decision: GateDecisionResult,
) -> None:
    if pipeline is not None:
        gate_observer = getattr(pipeline, "gate_observer", None)
        if gate_observer is None:
            gate_observer = GateObserver()
            pipeline.gate_observer = gate_observer
    else:
        gate_observer = GateObserver()

    gate_observer.build(
        ctx,
        pre_verdict=decision.pre_verdict,
        final_verdict=decision.verdict,
        delta_w=composite.delta_w,
        w_prev=composite.w_prev,
        w_current=composite.w_current,
        adaptive_metrics=assessment.adaptive_metrics,
        switching_safe=assessment.switching_safe,
        global_safe=assessment.global_safe,
        envelope=assessment.envelope,
        confidence_inputs=assessment.confidence_inputs,
        system_confidence=assessment.system_confidence,
        switching_metrics=assessment.switching_metrics,
        stability_certificate=decision.stability_certificate,
        hard_block=assessment.envelope.hard_block,
        hard_reason=assessment.envelope.hard_reason,
        w_ratio=assessment.w_ratio,
        recovery_detected=assessment.recovery_detected,
        recovery_magnitude=abs(composite.delta_w)
        if (composite.delta_w is not None and assessment.recovery_detected)
        else None,
    )
