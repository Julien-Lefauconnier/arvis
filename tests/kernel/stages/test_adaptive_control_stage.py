# tests/kernel/stages/test_adaptive_control_stage.py

from types import SimpleNamespace

from arvis.kernel.pipeline.stages.control_stage import ControlStage
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from tests.fixtures.builders.context_builder import build_test_context


def test_control_stage_applies_adaptive_modulation():
    stage = ControlStage()
    stage._adaptive_policy.compute = lambda **_: SimpleNamespace(exploration_scale=0.5)

    pipeline = SimpleNamespace(
        hysteresis=SimpleNamespace(update=lambda **_: None),
        epsilon_controller=SimpleNamespace(compute=lambda **_: 1.0),
        regime_policy=SimpleNamespace(
            compute=lambda _: SimpleNamespace(epsilon_multiplier=1.0)
        ),
        exploration=SimpleNamespace(compute=lambda **_: {}),
    )

    ctx = build_test_context(
        user_id="u",
        collapse_risk=0.5,
        drift_score=0.2,
        regime="stable",
    )

    ctx.scientific.regime_state.regime_confidence = 1.0
    ctx.scientific.regime_state.stable = True
    ctx.timeline = None

    ctx.scientific.adaptive.adaptive_snapshot = AdaptiveSnapshot(
        kappa_eff=0.1,
        margin=0.1,
        regime="unstable",
        available=True,
    )

    stage.run(pipeline, ctx)

    # epsilon should be reduced (unstable → low exploration)
    assert ctx._epsilon < 1.0
    assert ctx.adaptive_control is not None
