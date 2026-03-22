# tests/kernel/stages/test_kappa_margin_control.py

from types import SimpleNamespace

from arvis.kernel.pipeline.stages.control_stage import ControlStage
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot


def test_control_stage_reduces_epsilon_in_critical_kappa_band():
    stage = ControlStage()
    stage._adaptive_policy.compute = lambda **_: SimpleNamespace(exploration_scale=1.0)

    pipeline = SimpleNamespace(
        hysteresis=SimpleNamespace(update=lambda **_: None),
        epsilon_controller=SimpleNamespace(compute=lambda **_: 1.0),
        regime_policy=SimpleNamespace(
            compute=lambda _: SimpleNamespace(epsilon_multiplier=1.0)
        ),
        exploration=SimpleNamespace(compute=lambda **_: {}),
    )

    ctx = SimpleNamespace(
        user_id="u",
        collapse_risk=0.1,
        drift_score=0.1,
        regime="stable",
        regime_confidence=1.0,
        stable=True,
        timeline=None,
        adaptive_snapshot=AdaptiveSnapshot(
            kappa_eff=0.9,
            margin=-0.01,
            regime="critical",
            available=True,
        ),
    )

    stage.run(pipeline, ctx)

    assert ctx.kappa_band == "critical"
    assert ctx._epsilon < 1.0