# tests/kernel/stages/test_conflict_stage_adoption.py
"""The conflict stage's pressure channel: host adoption and computation.

Campaign RELEASE (LOT R2). The host may inject conflict pressure
through the documented ``extra["conflict_pressure"]`` boundary key,
either as a scalar or as a prebuilt signal; absent an injection the
stage computes pressure from the run's own conflict evaluations. The
adoption branch feeds the gate confirmation flag (DS4a) downstream,
so its exact semantics are pinned here.
"""

from __future__ import annotations

from types import SimpleNamespace

from arvis.cognition.conflict.conflict_evaluator import ConflictEvaluator
from arvis.cognition.conflict.conflict_pressure_engine import (
    ConflictPressureEngine,
)
from arvis.cognition.conflict.default_rules import default_conflict_rules
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.stages.conflict_stage import ConflictStage
from arvis.math.signals.conflict import ConflictSignal


def _pipeline() -> SimpleNamespace:
    return SimpleNamespace(
        conflict_evaluator=ConflictEvaluator(default_conflict_rules()),
        conflict_pressure_engine=ConflictPressureEngine(),
    )


def _ctx() -> CognitivePipelineContext:
    return CognitivePipelineContext(user_id="test", cognitive_input={})


def test_scalar_injection_is_adopted_through_from_scalar() -> None:
    ctx = _ctx()
    ctx.extra["conflict_pressure"] = 0.7

    ConflictStage().run(_pipeline(), ctx)

    assert isinstance(ctx.conflict_pressure, ConflictSignal)
    assert ctx.conflict_pressure.global_score == 0.7
    # from_scalar maps the scalar onto the decisional axis
    assert ctx.conflict_pressure.decisional == 0.7


def test_signal_injection_passes_through_unchanged() -> None:
    ctx = _ctx()
    injected = ConflictSignal(global_score=0.9, ethical=0.9)
    ctx.extra["conflict_pressure"] = injected

    ConflictStage().run(_pipeline(), ctx)

    assert ctx.conflict_pressure is injected


def test_scalar_injection_is_clamped_to_the_unit_interval() -> None:
    ctx = _ctx()
    ctx.extra["conflict_pressure"] = 7.0

    ConflictStage().run(_pipeline(), ctx)

    assert ctx.conflict_pressure is not None
    assert ctx.conflict_pressure.global_score == 1.0


def test_no_injection_and_no_conflicts_yields_zero_pressure() -> None:
    ctx = _ctx()

    ConflictStage().run(_pipeline(), ctx)

    assert ctx.conflict_pressure is not None
    assert ctx.conflict_pressure.is_zero()
    # the evaluation channel is populated either way
    assert ctx.conflict is not None


def test_active_conflicts_produce_computed_pressure() -> None:
    """When the run's own evaluations carry active conflict, pressure
    is computed from them (not from the empty-list fast path)."""
    ctx = _ctx()
    pipeline = _pipeline()

    class _Engine(ConflictPressureEngine):
        def __init__(self) -> None:
            self.saw: list[object] | None = None

        def compute(self, conflicts):  # type: ignore[override]
            self.saw = list(conflicts)
            return super().compute(conflicts)

    engine = _Engine()
    pipeline.conflict_pressure_engine = engine

    class _Evaluator:
        def apply(self, *, targets, conflicts):
            return [
                SimpleNamespace(
                    target_id=targets[0], score=0.6, active=True, conflicts=[]
                )
            ]

    pipeline.conflict_evaluator = _Evaluator()

    ConflictStage().run(pipeline, ctx)

    assert engine.saw is not None and len(engine.saw) == 1
    assert ctx.conflict_pressure is not None
    assert ctx.conflict_pressure.global_score == 0.6
