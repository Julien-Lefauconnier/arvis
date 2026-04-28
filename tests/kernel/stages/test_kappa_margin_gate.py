# tests/kernel/stages/test_kappa_margin_gate.py

from types import SimpleNamespace

from arvis.kernel.pipeline.stages.gate_stage import GateStage
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot


def _pipeline():
    return SimpleNamespace(
        theoretical_enforcement_mode="monitor",
        w_bound_tolerance=1.05,
        composite_rec_soft_threshold=0.0,
        composite_rec_strong_threshold=0.05,
    )


def _ctx():
    return SimpleNamespace(
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


def test_kappa_margin_critical_forces_confirmation():
    stage = GateStage()
    ctx = _ctx()
    pipeline = _pipeline()

    ctx.adaptive_snapshot = AdaptiveSnapshot(
        kappa_eff=0.9,
        margin=-0.01,
        regime="critical",
        available=True,
    )

    stage.run(pipeline, ctx)

    assert ctx.extra.get("kappa_band") == "critical"
    assert "kappa_margin_critical" in ctx.extra.get("fusion_reasons", [])
    assert ctx.gate_result in {
        LyapunovVerdict.REQUIRE_CONFIRMATION,
        LyapunovVerdict.ABSTAIN,
    }


def test_kappa_margin_warning_is_traced():
    stage = GateStage()
    ctx = _ctx()
    pipeline = _pipeline()

    ctx.adaptive_snapshot = AdaptiveSnapshot(
        kappa_eff=0.7,
        margin=-0.03,
        regime="stable",
        available=True,
    )

    stage.run(pipeline, ctx)

    assert ctx.extra.get("kappa_band") == "warning"
    assert "kappa_margin_warning" in ctx.extra.get("fusion_reasons", [])
