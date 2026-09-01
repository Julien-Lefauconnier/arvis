# tests/kernel/test_pipeline_math_alignment.py

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from tests.kernel.test_cognitive_pipeline import make_ctx


def test_pipeline_exposes_math_objects():
    pipeline = CognitivePipeline()
    ctx = make_ctx()

    pipeline.run(ctx)

    regime_state = ctx.scientific.regime_state
    assert hasattr(regime_state, "fast_dynamics")
    assert hasattr(regime_state, "perturbation")
    assert hasattr(ctx.scientific.composite, "delta_w")
    assert hasattr(regime_state, "theoretical_regime")


def test_fast_dynamics_consistency_in_pipeline():
    pipeline = CognitivePipeline()
    ctx = make_ctx()

    pipeline.run(ctx)
    pipeline.run(ctx)

    fd = ctx.scientific.regime_state.fast_dynamics

    if fd and fd.is_valid():
        assert fd.delta_norm >= 0


def test_perturbation_exists_in_pipeline():
    pipeline = CognitivePipeline()
    ctx = make_ctx()

    pipeline.run(ctx)

    assert ctx.scientific.regime_state.perturbation is not None


def test_pipeline_exposes_composite_metrics(pipeline, ctx):
    pipeline.run(ctx)

    assert ctx.scientific.composite.w_current is not None
    assert ctx.scientific.composite.delta_w is not None
    assert ctx.scientific.switching.switching_runtime is not None
    assert ctx.scientific.switching.switching_metrics is not None
