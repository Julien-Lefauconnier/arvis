# tests/fixtures/builders/context_builder.py

from __future__ import annotations

from typing import Any

from arvis.ir.decision import CognitiveDecisionIR
from arvis.ir.gate import CognitiveGateIR, CognitiveGateVerdictIR
from arvis.ir.state import CognitiveRiskIR, CognitiveStateIR
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.math.signals import DriftSignal, RiskSignal, UncertaintySignal


def build_test_context(
    *,
    user_id: str = "test_user",
    cognitive_input: Any | None = None,
    system_tension: float = 0.4,
    drift_score: float = 0.1,
    uncertainty: float = 0.2,
    collapse_risk: float = 0.3,
    regime: str | None = "stable",
    switching_safe: bool | None = True,
    delta_w: float | None = 0.05,
) -> CognitivePipelineContext:
    ctx = CognitivePipelineContext(
        user_id=user_id,
        cognitive_input=cognitive_input,
    )

    ctx.scientific.core.drift_score = DriftSignal(drift_score)
    ctx.scientific.core.uncertainty = UncertaintySignal(uncertainty)
    ctx.scientific.core.collapse_risk = RiskSignal(collapse_risk)

    ctx.scientific.regime_state.regime = regime
    ctx.scientific.switching.switching_safe = switching_safe
    ctx.scientific.composite.delta_w = delta_w

    ctx.observability.system_tension = system_tension

    return ctx


def attach_test_ir(
    ctx: CognitivePipelineContext,
) -> CognitivePipelineContext:
    ctx.decision_layer.ir_decision = CognitiveDecisionIR(
        decision_id="d1",
        decision_kind="action",
        memory_intent="none",
    )

    ctx.ir_gate = CognitiveGateIR(
        verdict=CognitiveGateVerdictIR.ALLOW,
        bundle_id="b1",
        reason_codes=("ok",),
        risk_level=0.2,
    )

    ctx.ir_state = CognitiveStateIR(
        state_id="s1",
        bundle_id="b1",
        dv=0.1,
        collapse_risk=CognitiveRiskIR(
            mh_risk=0.1,
            world_risk=0.2,
            forecast_risk=0.3,
            fused_risk=0.3,
            smoothed_risk=0.25,
        ),
        epsilon=0.15,
        early_warning=False,
    )

    return ctx


def build_test_context_with_ir() -> CognitivePipelineContext:
    return attach_test_ir(build_test_context())
