# arvis/runtime/invariants/scheduler_invariants.py

from __future__ import annotations

from arvis.errors.runtime_scheduler import SchedulerInvariantViolation
from arvis.kernel_core.process import CognitiveProcessStatus
from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState


class SchedulerInvariantValidator:
    def __init__(self, runtime_state: CognitiveRuntimeState) -> None:
        self.runtime_state = runtime_state

    def validate(self) -> None:
        self.validate_single_running_process()
        self.validate_active_process_consistency()

    def validate_single_running_process(self) -> None:
        running = [
            process
            for process in self.runtime_state.processes.values()
            if process.status == CognitiveProcessStatus.RUNNING
        ]

        if len(running) > 1:
            raise SchedulerInvariantViolation(
                "Scheduler invariant violated: more than one RUNNING process",
                details={
                    "running_count": len(running),
                    "invariant": "single_running_process",
                    "retry_class": "permanent",
                },
            )

    def validate_active_process_consistency(self) -> None:
        active_id = self.runtime_state.scheduler_state.active_process_id

        if active_id is None:
            return

        process = self.runtime_state.get_process(active_id)

        if process.status != CognitiveProcessStatus.RUNNING:
            raise SchedulerInvariantViolation(
                "Scheduler invariant violated: active process is not RUNNING",
                details={
                    "process_id": active_id.value,
                    "status": process.status.value,
                    "invariant": "active_process_must_be_running",
                    "retry_class": "permanent",
                },
            )
