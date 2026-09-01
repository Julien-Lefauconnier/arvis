# tests/kernel/stages/test_temporal_ownership.py
"""Temporal channel ownership (decision DS3, campaign STRUCT LOT S5).

The temporal stage computes the temporal regulation
(TemporalPressureSnapshot + TemporalModulation, multipliers clamped to
[0, 1] by the kernel invariant). Historically the control stage then
OVERWROTE both with an ad-hoc binary object whose 1.2 epsilon
multiplier bypassed the clamp, widening epsilon whenever a timeline
was present; the computed regulation never reached epsilon.

DS3: the temporal stage is the single owner of the channel; the
control stage consumes the clamped modulation. Widening disappears:
a timeline can only keep or tighten epsilon (monotone hardening).
"""

from __future__ import annotations

from arvis.cognition.control.temporal_modulation import TemporalModulation
from arvis.cognition.control.temporal_pressure import TemporalPressureSnapshot
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)


def _ctx(timeline: list | None = None) -> CognitivePipelineContext:
    return CognitivePipelineContext(
        user_id="test",
        cognitive_input={"input_id": "i1", "actor_id": "test"},
        timeline=timeline or [],
    )


def _run_through_control(ctx: CognitivePipelineContext) -> None:
    pipeline = CognitivePipeline()
    pipeline.temporal_stage.run(pipeline, ctx)
    pipeline.control_stage.run(pipeline, ctx)


def test_control_stage_preserves_temporal_stage_regulation() -> None:
    ctx = _ctx(timeline=[{"type": "note", "title": "conflict spotted"}])
    _run_through_control(ctx)

    assert isinstance(ctx.temporal_modulation, TemporalModulation), (
        "the control stage must consume the temporal stage's clamped "
        f"modulation, not overwrite it (got {type(ctx.temporal_modulation)!r})"
    )
    assert isinstance(ctx.temporal_pressure, TemporalPressureSnapshot), (
        "the pressure snapshot is owned by the temporal stage "
        f"(got {type(ctx.temporal_pressure)!r})"
    )


def test_modulation_respects_the_kernel_clamp() -> None:
    ctx = _ctx(timeline=[{"type": "note", "title": "anything"}])
    _run_through_control(ctx)

    assert 0.0 <= ctx.temporal_modulation.epsilon_multiplier <= 1.0, (
        "TemporalModulation clamps multipliers to [0, 1]; nothing on "
        "the pipeline path may bypass the invariant"
    )


def test_timeline_never_widens_epsilon() -> None:
    """A timeline may keep or tighten epsilon, never widen it."""
    with_timeline = _ctx(timeline=[{"type": "note", "title": "context"}])
    without_timeline = _ctx(timeline=[])

    _run_through_control(with_timeline)
    _run_through_control(without_timeline)

    assert with_timeline._epsilon is not None
    assert without_timeline._epsilon is not None
    assert with_timeline._epsilon <= without_timeline._epsilon + 1e-12, (
        "epsilon widened in the presence of a timeline "
        f"({with_timeline._epsilon} > {without_timeline._epsilon}): "
        "the ad-hoc x1.2 bypass is back"
    )
