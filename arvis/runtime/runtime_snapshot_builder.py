# arvis/runtime/runtime_snapshot_builder.py

from __future__ import annotations

from arvis.kernel_core.process import CognitiveProcess
from arvis.kernel_core.process.snapshot import ProcessSnapshot
from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState
from arvis.runtime.runtime_snapshot import RuntimeSnapshot


class RuntimeSnapshotBuilder:
    def __init__(self, runtime_state: CognitiveRuntimeState) -> None:
        self.runtime_state = runtime_state

    def build(self) -> RuntimeSnapshot:
        state = self.runtime_state.scheduler_state

        processes = tuple(
            self._snapshot_process(process)
            for _, process in sorted(
                self.runtime_state.processes.items(),
                key=lambda item: item[0].value,
            )
        )

        return RuntimeSnapshot(
            tick_count=state.tick_count,
            active_process_id=(
                state.active_process_id.value
                if state.active_process_id is not None
                else None
            ),
            ready_queue=tuple(pid.value for pid in state.ready_queue),
            blocked_queue=tuple(pid.value for pid in state.blocked_queue),
            suspended_queue=tuple(pid.value for pid in state.suspended_queue),
            waiting_confirmation_queue=tuple(
                pid.value for pid in state.waiting_confirmation_queue
            ),
            completed_queue=tuple(pid.value for pid in state.completed_queue),
            aborted_queue=tuple(pid.value for pid in state.aborted_queue),
            processes=processes,
            timeline_commitment=self.runtime_state.compute_timeline_commitment(),
        )

    def _snapshot_process(self, process: CognitiveProcess) -> ProcessSnapshot:
        return ProcessSnapshot(
            process_id=process.process_id.value,
            kind=process.kind.value,
            status=process.status.value,
            priority=process.priority.normalized(),
            created_tick=process.created_tick,
            user_id=process.user_id,
            parent_process_id=(
                process.parent_process_id.value
                if process.parent_process_id is not None
                else None
            ),
            waiting_on=process.waiting_on,
            run_count=process.run_count,
            last_run_tick=process.last_run_tick,
            last_error=process.last_error,
            current_stage_index=process.current_stage_index,
            stage_history=tuple(process.stage_history),
            total_stage_count=process.total_stage_count,
            pipeline_prepared=process.pipeline_prepared,
            pipeline_finalized=process.pipeline_finalized,
            consumed_reasoning_steps=process.runtime.consumed_reasoning_steps,
            consumed_attention_tokens=process.runtime.consumed_attention_tokens,
            consumed_uncertainty=process.runtime.consumed_uncertainty,
            consumed_elapsed_ms=process.runtime.consumed_elapsed_ms,
            consumed_memory_span=process.runtime.consumed_memory_span,
            subscribed_interrupts=tuple(sorted(process.subscribed_interrupts)),
        )
