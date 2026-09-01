# tests/kernel/stages/test_slow_drift_structured.py
"""RED-first pin of LOT C1 (campaign MATH-C): the structured branch
of the slow-drift detector must actually work on SlowState pairs.

The scalar-era code computed abs(cur_slow - prev_slow); SlowState
carries no subtraction, so on every structured turn the branch raised
TypeError, swallowed as slow_drift_detection_failure, and the
detector silently measured nothing (found live by the M10 harness:
the fail-soft was captured on every threaded turn of corpus D).
"""

from __future__ import annotations

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.stages.gate.composite import detect_slow_drift
from arvis.math.lyapunov.slow_state import SlowState


def _ctx() -> CognitivePipelineContext:
    return CognitivePipelineContext(user_id="test", cognitive_input={})


def _codes(ctx: CognitivePipelineContext) -> list[str]:
    return [
        str(payload.get("code"))
        for payload in ctx.extra.get("errors", [])
        if isinstance(payload, dict)
    ]


def test_structured_slow_states_feed_the_drift_history() -> None:
    ctx = _ctx()
    prev = SlowState(0.10, 0.20, 0.30, 0.40)
    cur = SlowState(0.11, 0.21, 0.31, 0.41)

    detect_slow_drift(ctx, prev, cur, delta_w=0.1)

    assert "slow_drift_detection_failure" not in _codes(ctx)
    history = ctx.scientific.drift.slow_drift_history
    assert len(history) == 1
    # euclidean norm of the componentwise delta (0.01 on each axis)
    assert abs(history[0] - 0.02) < 1e-9


def test_structured_stagnation_under_expansion_warns() -> None:
    """The detector's purpose: a near-frozen slow state while the
    consumed energy expands is the drift signature."""
    ctx = _ctx()
    frozen = SlowState(0.5, 0.5, 0.5, 0.5)

    for _ in range(5):
        detect_slow_drift(ctx, frozen, frozen, delta_w=0.05)

    assert "slow_drift_detection_failure" not in _codes(ctx)
    assert ctx.scientific.drift.slow_drift_warning is True


def test_scalar_era_slow_values_still_work() -> None:
    """Duck compatibility: the scalar path of the structured branch
    stays alive (existing gate tests feed floats)."""
    ctx = _ctx()

    detect_slow_drift(ctx, 1.0, 1.001, delta_w=0.1)

    assert "slow_drift_detection_failure" not in _codes(ctx)
    history = ctx.scientific.drift.slow_drift_history
    assert len(history) == 1
    assert abs(history[0] - 0.001) < 1e-12
