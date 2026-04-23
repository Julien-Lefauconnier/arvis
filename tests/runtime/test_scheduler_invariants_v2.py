# tests/runtime/test_scheduler_invariants_v2.py

from __future__ import annotations

import pytest

from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState
from arvis.runtime.cognitive_scheduler import CognitiveScheduler
from arvis.kernel_core.process import (
    CognitiveBudget,
    CognitivePriority,
    CognitiveProcess,
    CognitiveProcessId,
    CognitiveProcessKind,
    CognitiveProcessStatus,
)


class StubExecutor:
    def execute_process(self, process):
        raise RuntimeError("should not execute")


def make_process(
    process_id: str,
    *,
    status=CognitiveProcessStatus.READY,
) -> CognitiveProcess:
    return CognitiveProcess(
        process_id=CognitiveProcessId(process_id),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=status,
        priority=CognitivePriority(10.0),
        budget=CognitiveBudget(reasoning_steps=2, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id="u1", cognitive_input={}),
        created_tick=0,
        user_id="u1",
    )

def test_enqueue_rejects_final_process():
    runtime_state = CognitiveRuntimeState()
    scheduler = CognitiveScheduler(runtime_state=runtime_state, process_executor=StubExecutor())

    proc = make_process("p-final", status=CognitiveProcessStatus.COMPLETED)

    with pytest.raises(ValueError, match="Cannot enqueue final process"):
        scheduler.enqueue(proc)


def test_ready_queue_does_not_duplicate_on_resume():
    runtime_state = CognitiveRuntimeState()
    scheduler = CognitiveScheduler(runtime_state=runtime_state, process_executor=StubExecutor())

    proc = make_process("p1")
    scheduler.enqueue(proc)

    # READY -> RUNNING first (legal path)
    proc.mark_running(tick=0, score=1.0)

    scheduler.block(proc.process_id, waiting_on="io")
    scheduler.resume(proc.process_id)
    scheduler.resume(proc.process_id)

    ready_queue = runtime_state.scheduler_state.ready_queue
    assert ready_queue.count(proc.process_id) == 1


def test_completed_process_is_not_rescheduled():
    runtime_state = CognitiveRuntimeState()
    scheduler = CognitiveScheduler(runtime_state=runtime_state, process_executor=StubExecutor())

    p_completed = make_process("p-completed", status=CognitiveProcessStatus.COMPLETED)
    runtime_state.processes[p_completed.process_id] = p_completed
    runtime_state.scheduler_state.append_unique(
        runtime_state.scheduler_state.ready_queue, p_completed.process_id
    )

    decision = scheduler._select_next_process()

    assert decision.selected_process_id is None
    assert decision.rationale == "no schedulable ready process"


def test_blocked_process_is_not_selected_even_if_in_ready_queue():
    runtime_state = CognitiveRuntimeState()
    scheduler = CognitiveScheduler(runtime_state=runtime_state, process_executor=StubExecutor())

    proc = make_process("p-blocked", status=CognitiveProcessStatus.BLOCKED)
    runtime_state.processes[proc.process_id] = proc
    runtime_state.scheduler_state.append_unique(
        runtime_state.scheduler_state.ready_queue, proc.process_id
    )

    decision = scheduler._select_next_process()

    assert decision.selected_process_id is None
    assert decision.rationale == "no schedulable ready process"


def test_interrupt_resume_does_not_duplicate_ready_queue():
    from arvis.kernel_core.interrupts.interrupt import CognitiveInterrupt
    from arvis.kernel_core.interrupts.interrupt_type import CognitiveInterruptType

    runtime_state = CognitiveRuntimeState()
    scheduler = CognitiveScheduler(runtime_state=runtime_state, process_executor=StubExecutor())

    proc = make_process("p-int")
    scheduler.enqueue(proc)

    # READY -> RUNNING first
    proc.mark_running(tick=0, score=1.0)
    scheduler.block(proc.process_id, waiting_on="external_event")

    interrupt = CognitiveInterrupt(
        type=CognitiveInterruptType.SYSTEM_SIGNAL,
        target_process_id=proc.process_id,
        payload={"reason": "resume"},
    )

    runtime_state.interrupt_bus.emit(interrupt)

    scheduler._process_interrupts()
    scheduler._process_interrupts()

    ready_queue = runtime_state.scheduler_state.ready_queue
    assert ready_queue.count(proc.process_id) == 1