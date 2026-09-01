# tests/kernel/stages/test_conflict_channel_wiring.py
"""The declared conflict channels reach their intended consumers.

Campaign OBS (decision DS4). Historically the gate's confirmation
flag read ``ctx.conflict_signal`` (an attribute nothing writes; the
contribution was 0.0 on every run) and the decision trace's conflict
slot read ``ctx.extra["conflict"]`` (a key nothing writes; the slot
was None on every run). These tests pin the decided wiring:

- DS4a: ``sync_confirmation_flags`` consumes ``ctx.conflict_pressure``
  through the SAME canonical threshold function the confirmation stage
  uses (``requires_conflict_confirmation``, threshold 0.5), so the
  gate-time flag exports agree with the confirmation stage's own
  decision instead of ignoring conflict entirely.
- DS4b: ``DecisionTrace.conflict`` carries ``ctx.conflict``, the
  declared channel written by the conflict stage.

Direction check (F-001): the wiring can only raise the flag (a
pressure below threshold changes nothing; there is no path by which
conflict pressure lowers a confirmation requirement).
"""

from __future__ import annotations

from arvis.cognition.conflict.conflict_policy_result import ConflictPolicyResult
from arvis.cognition.gate.cognitive_gate_result import CognitiveGateResult
from arvis.kernel.execution.cognitive_execution_state import (
    CognitiveExecutionState,
)
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.factories.pipeline_trace_factory import (
    PipelineTraceFactory,
)
from arvis.kernel.pipeline.stages.gate.trace_helpers import (
    sync_confirmation_flags,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.signals.conflict import ConflictSignal


def _ctx() -> CognitivePipelineContext:
    ctx = CognitivePipelineContext(user_id="test", cognitive_input={})
    ctx.execution.execution_state = CognitiveExecutionState()
    return ctx


# ---------------------------------------------------------------------------
# DS4a: conflict pressure reaches the gate confirmation flag
# ---------------------------------------------------------------------------


def test_pressure_at_threshold_raises_the_gate_flag_on_allow() -> None:
    ctx = _ctx()
    ctx.conflict_pressure = ConflictSignal.from_scalar(0.6)

    sync_confirmation_flags(ctx, LyapunovVerdict.ALLOW)

    assert ctx.extra["requires_confirmation"] is True
    assert ctx.extra["needs_confirmation"] is True
    assert ctx.execution.execution_state is not None
    assert ctx.execution.execution_state.needs_confirmation is True


def test_pressure_below_threshold_leaves_an_allow_unflagged() -> None:
    ctx = _ctx()
    ctx.conflict_pressure = ConflictSignal.from_scalar(0.4)

    sync_confirmation_flags(ctx, LyapunovVerdict.ALLOW)

    assert ctx.extra["requires_confirmation"] is False
    assert ctx.extra["needs_confirmation"] is False


def test_absent_pressure_keeps_the_historical_flags() -> None:
    ctx = _ctx()
    assert ctx.conflict_pressure is None

    sync_confirmation_flags(ctx, LyapunovVerdict.ALLOW)

    assert ctx.extra["requires_confirmation"] is False


def test_confirmation_verdicts_flag_regardless_of_pressure() -> None:
    for verdict in (
        LyapunovVerdict.REQUIRE_CONFIRMATION,
        LyapunovVerdict.ABSTAIN,
    ):
        ctx = _ctx()

        sync_confirmation_flags(ctx, verdict)

        assert ctx.extra["requires_confirmation"] is True, verdict


def test_pressure_never_lowers_the_flag() -> None:
    """F-001 direction pin: with a flagging verdict, any pressure value
    (zero, sub-threshold, maximal) leaves the flag raised."""
    for scalar in (0.0, 0.49, 1.0):
        ctx = _ctx()
        ctx.conflict_pressure = ConflictSignal.from_scalar(scalar)

        sync_confirmation_flags(ctx, LyapunovVerdict.REQUIRE_CONFIRMATION)

        assert ctx.extra["requires_confirmation"] is True, scalar


def test_gate_flag_agrees_with_the_confirmation_stage_threshold() -> None:
    """One doctrine: the gate uses requires_conflict_confirmation, so
    the flag flips exactly where the confirmation stage's own conflict
    decision flips (0.5)."""
    flagged = []
    for scalar in (0.49, 0.5, 0.51):
        ctx = _ctx()
        ctx.conflict_pressure = ConflictSignal.from_scalar(scalar)
        sync_confirmation_flags(ctx, LyapunovVerdict.ALLOW)
        flagged.append(bool(ctx.extra["requires_confirmation"]))

    assert flagged == [False, True, True]


# ---------------------------------------------------------------------------
# DS4b: the declared conflict channel reaches the decision trace
# ---------------------------------------------------------------------------


def test_decision_trace_carries_the_declared_conflict_channel() -> None:
    ctx = _ctx()
    evaluations = [ConflictPolicyResult(target_id="bundle")]
    ctx.conflict = evaluations

    gate_result = CognitiveGateResult.from_lyapunov(LyapunovVerdict.ALLOW)
    trace = PipelineTraceFactory.build(ctx, gate_result)

    assert trace.conflict is evaluations


def test_decision_trace_conflict_stays_none_without_the_channel() -> None:
    ctx = _ctx()
    assert ctx.conflict is None

    gate_result = CognitiveGateResult.from_lyapunov(LyapunovVerdict.ALLOW)
    trace = PipelineTraceFactory.build(ctx, gate_result)

    assert trace.conflict is None
