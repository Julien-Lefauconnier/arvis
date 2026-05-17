# tests/runtime/test_scheduler_error_semantics.py

from __future__ import annotations

import pytest

from arvis.errors.runtime_scheduler import SchedulerInvariantViolation
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.kernel_core.process import (
    CognitiveBudget,
    CognitivePriority,
    CognitiveProcess,
    CognitiveProcessId,
    CognitiveProcessKind,
    CognitiveProcessStatus,
)
from arvis.kernel_core.state.scheduler_state import SchedulerState


def make_process() -> CognitiveProcess:
    return CognitiveProcess(
        process_id=CognitiveProcessId("p1"),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(10.0),
        budget=CognitiveBudget(reasoning_steps=1, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id="u1", cognitive_input={}),
        created_tick=0,
        user_id="u1",
    )


def test_scheduler_single_running_invariant_uses_arvis_error() -> None:
    state = SchedulerState()

    with pytest.raises(SchedulerInvariantViolation) as exc_info:
        state.validate_single_running_invariant(2)

    error = exc_info.value

    assert error.code == "scheduler_invariant_violation"
    assert error.details["running_count"] == 2
    assert error.details["invariant"] == "single_running_process"
    assert error.details["retry_class"] == "permanent"


def test_process_set_total_stage_count_uses_arvis_error() -> None:
    process = make_process()

    with pytest.raises(SchedulerInvariantViolation) as exc_info:
        process.set_total_stage_count(-1)

    error = exc_info.value

    assert error.code == "scheduler_invariant_violation"
    assert error.details["process_id"] == "p1"
    assert error.details["total_stage_count"] == -1
    assert error.details["invariant"] == "non_negative_total_stage_count"


def test_process_validate_negative_stage_index_uses_arvis_error() -> None:
    process = make_process()
    process.current_stage_index = -1

    with pytest.raises(SchedulerInvariantViolation) as exc_info:
        process.validate()

    error = exc_info.value

    assert error.code == "scheduler_invariant_violation"
    assert error.details["process_id"] == "p1"
    assert error.details["current_stage_index"] == -1
    assert error.details["invariant"] == "non_negative_current_stage_index"
