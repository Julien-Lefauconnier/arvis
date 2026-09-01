# tests/kernel/test_pi_impl.py

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.projection.pi_impl import PiImpl


def DummyCtx() -> CognitivePipelineContext:
    """Real pipeline context (campaign STRUCT, LOT S4)."""
    ctx = CognitivePipelineContext(user_id="test", cognitive_input={})
    ctx.observability.diagnostics.system_tension = 42.0
    ctx.conflict_pressure = 12.5
    ctx.coherence_score = 0.8
    ctx.control_signal = 30.0
    ctx.adaptive_kappa_eff = 0.25
    ctx.observability.predictive_snapshot = {"ok": True}
    return ctx


def test_pi_impl_projects_runtime_signals():
    ctx = DummyCtx()
    pi_impl = PiImpl()

    projected = pi_impl.project(ctx)
    view = projected.to_projection_view()

    assert projected.state_signals["system_tension"] == 42.0
    assert view["state.system_tension"] == 42.0
    assert view["risk.conflict_pressure"] == 12.5
    assert view["state.coherence_score"] == 0.8
    assert view["control.control_signal"] == 30.0
    assert view["trace.adaptive_kappa_eff"] == 0.25
