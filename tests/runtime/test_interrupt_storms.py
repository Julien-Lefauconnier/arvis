# tests/runtime/test_interrupt_storms.py

from __future__ import annotations

from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState
from arvis.runtime.cognitive_scheduler import CognitiveScheduler
from arvis.kernel_core.interrupts.interrupt import CognitiveInterrupt
from arvis.kernel_core.interrupts.interrupt_type import CognitiveInterruptType
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
        raise RuntimeError("not used")


def make_process(pid: str) -> CognitiveProcess:
    return CognitiveProcess(
        process_id=CognitiveProcessId(pid),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(10.0),
        budget=CognitiveBudget(reasoning_steps=2, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id=pid, cognitive_input={}),
        created_tick=0,
        user_id=pid,
    )


def test_interrupt_storm_does_not_duplicate_ready_queue():
    runtime_state = CognitiveRuntimeState()
    scheduler = CognitiveScheduler(
        runtime_state=runtime_state, process_executor=StubExecutor()
    )

    proc = make_process("p1")
    scheduler.enqueue(proc)

    proc.mark_running(tick=0, score=1.0)
    scheduler.block(proc.process_id, waiting_on="external")

    for i in range(10):
        runtime_state.interrupt_bus.emit(
            CognitiveInterrupt(
                type=CognitiveInterruptType.SYSTEM_SIGNAL,
                target_process_id=proc.process_id,
                payload={"i": i},
            )
        )

    scheduler._process_interrupts()

    ready = runtime_state.scheduler_state.ready_queue
    assert ready.count(proc.process_id) == 1


def test_system_signal_wakes_only_non_final_processes():
    runtime_state = CognitiveRuntimeState()
    scheduler = CognitiveScheduler(
        runtime_state=runtime_state, process_executor=StubExecutor()
    )

    blocked = make_process("blocked")
    scheduler.enqueue(blocked)
    blocked.mark_running(tick=0, score=1.0)
    scheduler.block(blocked.process_id, waiting_on="external")

    completed = CognitiveProcess(
        process_id=CognitiveProcessId("done"),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.COMPLETED,
        priority=CognitivePriority(10.0),
        budget=CognitiveBudget(reasoning_steps=2, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id="done", cognitive_input={}),
        created_tick=0,
        user_id="done",
    )
    runtime_state.processes[completed.process_id] = completed

    runtime_state.interrupt_bus.emit(
        CognitiveInterrupt(
            type=CognitiveInterruptType.SYSTEM_SIGNAL,
            target_process_id=None,
            payload={"reason": "wake"},
        )
    )

    scheduler._process_interrupts()

    assert blocked.process_id in runtime_state.scheduler_state.ready_queue
    assert completed.process_id not in runtime_state.scheduler_state.ready_queue
