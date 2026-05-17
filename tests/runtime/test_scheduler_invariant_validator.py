# tests/runtime/test_scheduler_invariant_validator.py

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
from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState
from arvis.runtime.invariants import SchedulerInvariantValidator


def make_process(pid: str, status: CognitiveProcessStatus) -> CognitiveProcess:
    return CognitiveProcess(
        process_id=CognitiveProcessId(pid),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=status,
        priority=CognitivePriority(10.0),
        budget=CognitiveBudget(reasoning_steps=2, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id="u", cognitive_input={}),
        created_tick=0,
        user_id="u",
    )


def test_validator_rejects_multiple_running_processes():
    runtime_state = CognitiveRuntimeState()
    p1 = make_process("p1", CognitiveProcessStatus.RUNNING)
    p2 = make_process("p2", CognitiveProcessStatus.RUNNING)

    runtime_state.processes[p1.process_id] = p1
    runtime_state.processes[p2.process_id] = p2

    validator = SchedulerInvariantValidator(runtime_state)

    with pytest.raises(SchedulerInvariantViolation) as exc_info:
        validator.validate()

    assert exc_info.value.details["invariant"] == "single_running_process"
    assert exc_info.value.details["running_count"] == 2


def test_validator_rejects_active_process_not_running():
    runtime_state = CognitiveRuntimeState()
    process = make_process("p1", CognitiveProcessStatus.READY)

    runtime_state.processes[process.process_id] = process
    runtime_state.scheduler_state.active_process_id = process.process_id

    validator = SchedulerInvariantValidator(runtime_state)

    with pytest.raises(SchedulerInvariantViolation) as exc_info:
        validator.validate()

    assert exc_info.value.details["invariant"] == "active_process_must_be_running"
    assert exc_info.value.details["status"] == "ready"
