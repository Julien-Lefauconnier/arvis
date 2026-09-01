# arvis/kernel/pipeline/stages/gate/observability.py

from __future__ import annotations

from typing import Any

from arvis.kernel.observability.gate_observer import (
    GateObservation,
    GateObserver,
)
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
        GateObservation.from_gate_results(composite, assessment, decision),
    )
