# tests/runtime/test_runtime_snapshot.py

from __future__ import annotations

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
from arvis.runtime.cognitive_scheduler import CognitiveScheduler
from arvis.runtime.runtime_snapshot_builder import RuntimeSnapshotBuilder


class StubExecutor:
    def execute_process(self, process):
        raise RuntimeError("not used")


def make_process(pid: str, priority: float = 10.0) -> CognitiveProcess:
    return CognitiveProcess(
        process_id=CognitiveProcessId(pid),
        kind=CognitiveProcessKind.USER_REQUEST,
        status=CognitiveProcessStatus.READY,
        priority=CognitivePriority(priority),
        budget=CognitiveBudget(reasoning_steps=2, time_slice_ms=100),
        local_state=CognitivePipelineContext(user_id="u1", cognitive_input={}),
        created_tick=0,
        user_id="u1",
    )


def test_runtime_snapshot_is_deterministically_ordered():
    runtime_state = CognitiveRuntimeState()
    scheduler = CognitiveScheduler(runtime_state, process_executor=StubExecutor())

    scheduler.enqueue(make_process("p2"))
    scheduler.enqueue(make_process("p1"))

    snapshot = RuntimeSnapshotBuilder(runtime_state).build()

    assert [p.process_id for p in snapshot.processes] == ["p1", "p2"]
    assert snapshot.ready_queue == ("p2", "p1")
    assert snapshot.tick_count == 0
    assert snapshot.timeline_commitment


def test_runtime_snapshot_captures_active_process():
    runtime_state = CognitiveRuntimeState()
    scheduler = CognitiveScheduler(runtime_state, process_executor=StubExecutor())

    process = make_process("p1")
    scheduler.enqueue(process)

    scheduler.lifecycle.transition(
        process,
        CognitiveProcessStatus.RUNNING,
        tick=1,
        score=42.0,
    )

    snapshot = RuntimeSnapshotBuilder(runtime_state).build()

    assert snapshot.active_process_id == "p1"
    assert snapshot.ready_queue == ()

    proc_snapshot = snapshot.processes[0]
    assert proc_snapshot.status == "running"
    assert proc_snapshot.run_count == 1
    assert proc_snapshot.last_run_tick == 1


def test_runtime_snapshot_is_immutable_projection():
    runtime_state = CognitiveRuntimeState()
    scheduler = CognitiveScheduler(runtime_state, process_executor=StubExecutor())

    process = make_process("p1")
    scheduler.enqueue(process)

    snapshot = RuntimeSnapshotBuilder(runtime_state).build()

    process.runtime.consumed_reasoning_steps = 99

    assert snapshot.processes[0].consumed_reasoning_steps == 0
