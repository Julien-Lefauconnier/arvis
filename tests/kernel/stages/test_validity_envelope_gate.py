# tests/kernel/stages/test_validity_envelope_gate.py

from types import SimpleNamespace
from typing import Any

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.stages.gate_stage import GateStage
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def _gate_ctx(
    *,
    prev_lyap: Any = None,
    cur_lyap: Any = None,
    collapse_risk: float = 0.0,
    stable: bool = True,
    **attrs: Any,
) -> CognitivePipelineContext:
    """Real pipeline context seeded through the canonical scientific
    paths (campaign STRUCT, LOT S4); extra keyword attributes are set
    on the context for gate channels the tests exercise."""
    ctx = CognitivePipelineContext(user_id="test", cognitive_input={})
    ctx.scientific.lyapunov.prev_lyap = prev_lyap
    ctx.scientific.lyapunov.cur_lyap = cur_lyap
    ctx.scientific.composite.delta_w_history = []
    ctx.scientific.core.collapse_risk = collapse_risk
    ctx.scientific.regime_state.stable = stable
    ctx._epsilon = 1.0
    for key, value in attrs.items():
        setattr(ctx, key, value)
    return ctx


def test_gate_exports_validity_envelope():
    stage = GateStage()
    ctx = _gate_ctx(
        prev_lyap=1.0,
        cur_lyap=0.9,
        collapse_risk=0.0,
        stable=True,
    )
    pipeline = SimpleNamespace(
        theoretical_enforcement_mode="monitor",
        w_bound_tolerance=1.05,
        composite_rec_soft_threshold=0.0,
        composite_rec_strong_threshold=0.05,
    )

    stage.run(pipeline, ctx)

    assert ctx.validity_envelope is not None
    assert "validity_envelope" in ctx.extra


def test_gate_reacts_to_invalid_envelope():
    stage = GateStage()
    ctx = _gate_ctx(
        prev_lyap=None,
        cur_lyap=None,
        collapse_risk=0.0,
        stable=True,
    )
    pipeline = SimpleNamespace(
        theoretical_enforcement_mode="monitor",
        w_bound_tolerance=1.05,
        composite_rec_soft_threshold=0.0,
        composite_rec_strong_threshold=0.05,
    )
    stage.run(pipeline, ctx)
    assert "validity_projection_unavailable" in ctx.extra.get("fusion_reasons", [])
    assert ctx.gate_result in {
        LyapunovVerdict.REQUIRE_CONFIRMATION,
        LyapunovVerdict.ABSTAIN,
    }


def test_gate_projection_enforcement_soft_downgrades_allow():
    stage = GateStage()
    ctx = _gate_ctx(
        prev_lyap=1.0,
        cur_lyap=0.8,
        collapse_risk=0.0,
        stable=True,
    )
    # Canonical projection channel (LOT S4): the root-attribute
    # fallback is for legacy duck contexts only.
    ctx.projection.certificate = SimpleNamespace(
        domain_valid=True,
        margin_to_boundary=1.0,
        is_projection_safe=False,
    )
    ctx.projection.view = {"state.system_tension": 0.5}
    pipeline = SimpleNamespace(
        theoretical_enforcement_mode="monitor",
        w_bound_tolerance=1.05,
        composite_rec_soft_threshold=0.0,
        composite_rec_strong_threshold=0.05,
        projection_boundary_threshold=0.1,
    )

    stage.run(pipeline, ctx)

    assert ctx.gate_result in {
        LyapunovVerdict.REQUIRE_CONFIRMATION,
        LyapunovVerdict.ABSTAIN,
    }


def test_gate_projection_lyapunov_incompatibility_downgrades_allow():
    stage = GateStage()
    ctx = _gate_ctx(
        prev_lyap=1.0,
        cur_lyap=0.8,
        collapse_risk=0.0,
        stable=True,
    )
    ctx.projection.certificate = SimpleNamespace(
        domain_valid=True,
        margin_to_boundary=1.0,
        is_projection_safe=True,
        lyapunov_compatibility_ok=False,
    )
    ctx.projection.view = {"state.system_tension": 0.5}
    pipeline = SimpleNamespace(
        theoretical_enforcement_mode="monitor",
        w_bound_tolerance=1.05,
        composite_rec_soft_threshold=0.0,
        composite_rec_strong_threshold=0.05,
        projection_boundary_threshold=0.1,
    )

    stage.run(pipeline, ctx)

    assert "projection_lyapunov_incompatible" in ctx.extra.get("fusion_reasons", [])
    assert ctx.gate_result in {
        LyapunovVerdict.REQUIRE_CONFIRMATION,
        LyapunovVerdict.ABSTAIN,
    }
