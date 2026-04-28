# tests/runtime/test_interrupts.py


from arvis.kernel_core.interrupts.interrupt import CognitiveInterrupt
from arvis.kernel_core.interrupts.interrupt_type import CognitiveInterruptType
from arvis.kernel_core.process import (
    CognitiveProcess,
    CognitiveProcessId,
    CognitiveProcessKind,
    CognitiveProcessStatus,
)
from arvis.kernel_core.process.budget import CognitiveBudget
from arvis.kernel_core.process.priority import CognitivePriority
from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState
from arvis.runtime.cognitive_scheduler import CognitiveScheduler


class DummyExecutor:
    def execute_process(self, process):
        class Outcome:
            completed = False
            consumption = CognitiveBudget(
                reasoning_steps=0,
                attention_tokens=0,
                uncertainty_budget=0.0,
                time_slice_ms=0,
                memory_span=0,
            )

        return Outcome()


def make_process(pid: str):
    return CognitiveProcess(
        process_id=CognitiveProcessId(pid),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(1.0),
        budget=CognitiveBudget(
            reasoning_steps=10,
            attention_tokens=10,
            uncertainty_budget=1.0,
            time_slice_ms=100,
            memory_span=10,
        ),
        local_state=None,
        created_tick=0,
    )


def test_interrupt_wakes_blocked_process():
    runtime = CognitiveRuntimeState()
    scheduler = CognitiveScheduler(runtime, process_executor=DummyExecutor())

    p = make_process("p1")
    scheduler.enqueue(p)

    # simulate scheduler selecting it
    p.mark_running(tick=0)

    scheduler.block(p.process_id, "waiting_io")

    assert p.status == CognitiveProcessStatus.BLOCKED

    # emit interrupt
    interrupt = CognitiveInterrupt(
        type=CognitiveInterruptType.EXTERNAL_EVENT,
        target_process_id=p.process_id,
    )
    runtime.interrupt_bus.emit(interrupt)

    scheduler.tick()

    assert p.status == CognitiveProcessStatus.READY
    assert p.process_id in runtime.scheduler_state.ready_queue


def test_interrupt_does_not_wake_completed():
    runtime = CognitiveRuntimeState()
    scheduler = CognitiveScheduler(runtime, process_executor=DummyExecutor())

    p = make_process("p2")
    scheduler.enqueue(p)

    p.mark_running(tick=0)
    p.mark_completed()

    interrupt = CognitiveInterrupt(
        type=CognitiveInterruptType.EXTERNAL_EVENT,
        target_process_id=p.process_id,
    )
    runtime.interrupt_bus.emit(interrupt)

    scheduler.tick()

    assert p.status == CognitiveProcessStatus.COMPLETED


def test_interrupt_broadcast():
    runtime = CognitiveRuntimeState()
    scheduler = CognitiveScheduler(runtime, process_executor=DummyExecutor())

    p1 = make_process("p1")
    p2 = make_process("p2")

    scheduler.enqueue(p1)
    scheduler.enqueue(p2)

    p1.mark_running(tick=0)
    p2.mark_running(tick=0)

    scheduler.block(p1.process_id, "io")
    scheduler.block(p2.process_id, "io")

    interrupt = CognitiveInterrupt(
        type=CognitiveInterruptType.SYSTEM_SIGNAL,
        target_process_id=None,  # broadcast
    )

    runtime.interrupt_bus.emit(interrupt)
    scheduler.tick()

    assert p1.status == CognitiveProcessStatus.READY
    assert p2.status == CognitiveProcessStatus.READY
