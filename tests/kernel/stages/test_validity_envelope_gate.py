# tests/kernel/stages/test_validity_envelope_gate.py

from types import SimpleNamespace

from arvis.kernel.pipeline.stages.gate_stage import GateStage
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def test_gate_exports_validity_envelope():
    stage = GateStage()
    ctx = SimpleNamespace(
        prev_lyap=1.0,
        cur_lyap=0.9,
        delta_w_history=[],
        extra={},
        switching_runtime=None,
        switching_params=None,
        control_snapshot=None,
        collapse_risk=0.0,
        stable=True,
        global_stability_action="ignore",
        _epsilon=1.0,
        _cognitive_mode=None,
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
    ctx = SimpleNamespace(
        prev_lyap=None,
        cur_lyap=None,
        delta_w_history=[],
        extra={},
        switching_runtime=None,
        switching_params=None,
        control_snapshot=None,
        collapse_risk=0.0,
        stable=True,
        global_stability_action="ignore",
        _epsilon=1.0,
        _cognitive_mode=None,
    )
    pipeline = SimpleNamespace(
        theoretical_enforcement_mode="monitor",
        w_bound_tolerance=1.05,
        composite_rec_soft_threshold=0.0,
        composite_rec_strong_threshold=0.05,
    )
    stage.run(pipeline, ctx)
    assert "validity_projection_unavailable" in ctx.extra.get("fusion_reasons", [])
    assert ctx.gate_result in {LyapunovVerdict.REQUIRE_CONFIRMATION, LyapunovVerdict.ABSTAIN}