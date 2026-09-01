# tests/kernel/stages/test_adaptive_gate_integration.py

from types import SimpleNamespace

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.stages.gate_stage import GateStage
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.control.eps_adaptive import CognitiveMode
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def _base_pipeline():
    return SimpleNamespace(
        theoretical_enforcement_mode="monitor",
        delta_w_strict_threshold=0.1,
        delta_w_monitor_threshold=0.2,
        w_bound_tolerance=1.05,
        composite_rec_soft_threshold=0.0,
        composite_rec_strong_threshold=0.05,
    )


def _base_ctx() -> CognitivePipelineContext:
    """Real pipeline context seeded through the canonical scientific
    paths (campaign STRUCT, LOT S4)."""
    ctx = CognitivePipelineContext(user_id="u", cognitive_input={})

    # SimpleNamespace fast states: structurally invalid on purpose, the
    # adaptive veto must decide from the adaptive snapshot alone.
    ctx.scientific.lyapunov.prev_lyap = SimpleNamespace()
    ctx.scientific.lyapunov.cur_lyap = SimpleNamespace()

    ctx.scientific.switching.switching_runtime = SimpleNamespace(
        dwell_time=lambda: 10.0,
        total_switches=0,
    )
    ctx.scientific.switching.switching_params = SimpleNamespace(
        J=1.1,
        alpha=0.3,
        gamma_z=1.0,
        eta=0.05,
        L_T=1.0,
    )

    ctx.scientific.core.collapse_risk = 0.1
    ctx.scientific.core.drift_score = 0.1
    ctx.scientific.regime_state.regime = "stable"
    ctx.scientific.regime_state.stable = True
    ctx.regime_confidence = 1.0

    ctx.control_snapshot = SimpleNamespace(
        gate_mode=None,
        epsilon=1.0,
        smoothed_risk=0.1,
        exploration=1.0,
        drift={},
        regime=None,
        calibration=None,
    )

    ctx.scientific.composite.delta_w_history = []
    ctx._epsilon = 1.0
    ctx._cognitive_mode = CognitiveMode.NORMAL

    return ctx


def test_adaptive_gate_veto_on_instability():
    stage = GateStage()
    pipeline = _base_pipeline()
    ctx = _base_ctx()

    ctx.scientific.adaptive.adaptive_snapshot = AdaptiveSnapshot(
        kappa_eff=0.0,
        margin=0.1,
        regime="unstable",
        available=True,
    )

    stage.run(pipeline, ctx)

    assert ctx.gate_result == LyapunovVerdict.ABSTAIN
    assert ctx.gate_result == LyapunovVerdict.ABSTAIN


def test_adaptive_gate_warn_on_marginal():
    stage = GateStage()
    pipeline = _base_pipeline()
    ctx = _base_ctx()

    ctx.scientific.adaptive.adaptive_snapshot = AdaptiveSnapshot(
        kappa_eff=0.1,
        margin=-0.01,
        regime="critical",
        available=True,
    )

    stage.run(pipeline, ctx)

    assert "adaptive_margin_warning" in ctx.extra.get("fusion_reasons", [])
    assert ctx.gate_result in {
        LyapunovVerdict.REQUIRE_CONFIRMATION,
        LyapunovVerdict.ABSTAIN,
        LyapunovVerdict.ALLOW,
    }


def test_adaptive_gate_stable_no_regression():
    stage = GateStage()
    pipeline = _base_pipeline()
    ctx = _base_ctx()

    ctx.scientific.adaptive.adaptive_snapshot = AdaptiveSnapshot(
        kappa_eff=0.5,
        margin=-0.1,
        regime="stable",
        available=True,
    )

    stage.run(pipeline, ctx)

    assert "adaptive_instability_veto" not in ctx.extra.get("fusion_reasons", [])
