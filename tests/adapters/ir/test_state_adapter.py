# tests/adapters/ir/test_state_adapter.py

from __future__ import annotations

from types import SimpleNamespace

from arvis.adapters.ir.state_adapter import StateIRAdapter
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)


def test_state_adapter_builds_state_from_context() -> None:
    ctx = CognitivePipelineContext(user_id="test", cognitive_input={})
    ctx.decision_layer.bundle = SimpleNamespace(bundle_id="bundle-1")
    ctx.scientific.core.collapse_risk = 0.2
    ctx.observability.projections.multi_horizon = SimpleNamespace(risk=0.11)
    ctx.observability.projections.global_forecast = {"world_risk": 0.22}
    ctx.observability.projections.predictive_snapshot = SimpleNamespace(
        forecast_risk=0.33
    )
    ctx.observability.projections.global_stability = {"fused_risk": 0.44}
    ctx.control_snapshot = SimpleNamespace(epsilon=0.55, smoothed_risk=0.66)
    ctx.scientific.core.drift_score = 0.07
    # Typed channel (campaign OBS, LOT O2): early_warning reads the journal.
    ctx.journal.global_instability_warning = True
    ctx.introspection = "irg-state"

    ir = StateIRAdapter.from_context(ctx)

    assert ir.bundle_id == "bundle-1"
    assert ir.dv == 0.07
    assert ir.collapse_risk.mh_risk == 0.11
    assert ir.collapse_risk.world_risk == 0.22
    assert ir.collapse_risk.forecast_risk == 0.33
    assert ir.collapse_risk.fused_risk == 0.44
    assert ir.collapse_risk.smoothed_risk == 0.66
    assert ir.epsilon == 0.55
    assert ir.early_warning is True
    assert ir.irg == "irg-state"


def test_state_adapter_falls_back_to_context_values() -> None:
    ctx = CognitivePipelineContext(user_id="test", cognitive_input={})
    ctx.decision_layer.bundle = SimpleNamespace(bundle_id="bundle-2")
    ctx.scientific.core.collapse_risk = 0.81
    ctx.scientific.core.drift_score = 0.02

    ir = StateIRAdapter.from_context(ctx)

    assert ir.bundle_id == "bundle-2"
    assert ir.collapse_risk.fused_risk == 0.81
    assert ir.early_warning is True
