# tests/kernel/stages/test_kappa_gate_integration.py

from types import SimpleNamespace

from arvis.kernel.pipeline.stages.gate_stage import GateStage
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def test_gate_reacts_to_kappa_violation():
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
        global_stability_metrics=SimpleNamespace(kappa_violation=True),
    )

    pipeline = SimpleNamespace(theoretical_enforcement_mode="monitor")

    stage.run(pipeline, ctx)

    assert "kappa_violation" in ctx.extra.get("fusion_reasons", [])
    assert ctx.gate_result in {
        LyapunovVerdict.REQUIRE_CONFIRMATION,
        LyapunovVerdict.ABSTAIN,
    }
