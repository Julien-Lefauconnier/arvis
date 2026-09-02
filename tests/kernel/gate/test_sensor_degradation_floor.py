# tests/kernel/gate/test_sensor_degradation_floor.py
"""Recorded sensor degradations constrain the verdict.

Campaign HARDEN (DM-H8 option A, audit P1-11, 2026-09-02). The
decision-path sensors fail open individually by design (a failed
drift cast reads as no drift, a swallowed adaptive control as no
clamp) and journal every failure through ErrorManager; but nothing on
the decision path consumed the journal: should_escalate had no caller
outside tests, degraded_mode no reader in any gate stage, so a
degraded run was governed exactly like a healthy one. The floor is
the consumer: an escalating error record floors ALLOW to
REQUIRE_CONFIRMATION, monotone and traced; a clean turn is untouched.
"""

from __future__ import annotations

from types import SimpleNamespace

from arvis.errors.manager import ErrorManager
from arvis.errors.pipeline import PipelineStageDegradedError
from arvis.kernel.pipeline.stages.gate.enforcement import (
    apply_sensor_degradation_floor,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def _ctx() -> SimpleNamespace:
    return SimpleNamespace(extra={})


def _degrade(ctx: SimpleNamespace, count: int = 1) -> None:
    """Attach enough degraded errors to reach the escalation
    predicate's degraded threshold."""
    for index in range(count):
        ErrorManager.attach(
            ctx,
            PipelineStageDegradedError(
                message=f"probe degradation {index}",
                details={"component": "probe_sensor"},
            ),
        )


def _escalate(ctx: SimpleNamespace) -> None:
    """Attach degraded errors until the escalation predicate fires
    (the statistics are created lazily by the first attach, so the
    first degradation always precedes the first predicate call)."""
    for _ in range(50):
        _degrade(ctx)
        if ErrorManager.should_escalate(ctx):
            return
    raise AssertionError("escalation predicate unreachable by degradations")


def test_a_clean_turn_is_untouched() -> None:
    ctx = _ctx()
    out = apply_sensor_degradation_floor(ctx, LyapunovVerdict.ALLOW)
    assert out is LyapunovVerdict.ALLOW
    assert ctx.extra.get("fusion_reasons") in (None, [])


def test_an_escalating_record_floors_allow_to_confirmation() -> None:
    ctx = _ctx()
    _escalate(ctx)
    out = apply_sensor_degradation_floor(ctx, LyapunovVerdict.ALLOW)
    assert out is LyapunovVerdict.REQUIRE_CONFIRMATION


def test_the_floor_records_its_reason_and_transition() -> None:
    ctx = _ctx()
    _escalate(ctx)
    apply_sensor_degradation_floor(ctx, LyapunovVerdict.ALLOW)
    transitions = ctx.extra.get("verdict_transition_trace") or []
    assert any(
        entry.get("stage") == "sensor_degradation_floor"
        and entry.get("before") == "ALLOW"
        and entry.get("after") == "REQUIRE_CONFIRMATION"
        for entry in transitions
    ), transitions


def test_the_floor_never_relaxes() -> None:
    ctx = _ctx()
    _escalate(ctx)
    assert (
        apply_sensor_degradation_floor(ctx, LyapunovVerdict.ABSTAIN)
        is LyapunovVerdict.ABSTAIN
    )
    assert (
        apply_sensor_degradation_floor(ctx, LyapunovVerdict.REQUIRE_CONFIRMATION)
        is LyapunovVerdict.REQUIRE_CONFIRMATION
    )


def test_below_the_threshold_nothing_moves() -> None:
    ctx = _ctx()
    _degrade(ctx, count=1)
    if ErrorManager.should_escalate(ctx):
        # The predicate escalates on a single degradation in this
        # configuration; the below-threshold case does not exist.
        return
    out = apply_sensor_degradation_floor(ctx, LyapunovVerdict.ALLOW)
    assert out is LyapunovVerdict.ALLOW


def test_the_floor_is_wired_into_the_decision_stack() -> None:
    """The consumer stays consumed (same source-pin precedent as the
    DM-F1 duck-default pin): the stack must route the verdict through
    the floor under monotone enforcement."""
    import inspect

    from arvis.kernel.pipeline.stages.gate import decision_stack

    src = inspect.getsource(decision_stack)
    assert "apply_sensor_degradation_floor(ctx, verdict)" in src
    assert '"sensor_degradation_floor"' in src
