# arvis/kernel_core/state/scheduler_state.py

from __future__ import annotations

from dataclasses import dataclass, field

from arvis.kernel_core.process import CognitiveProcessId


@dataclass
class SchedulerState:
    ready_queue: list[CognitiveProcessId] = field(default_factory=list)
    blocked_queue: list[CognitiveProcessId] = field(default_factory=list)
    suspended_queue: list[CognitiveProcessId] = field(default_factory=list)
    waiting_confirmation_queue: list[CognitiveProcessId] = field(default_factory=list)
    completed_queue: list[CognitiveProcessId] = field(default_factory=list)
    aborted_queue: list[CognitiveProcessId] = field(default_factory=list)

    active_process_id: CognitiveProcessId | None = None
    tick_count: int = 0

    # -----------------------------------------------------
    # TICK MANAGEMENT
    # -----------------------------------------------------
    def note_tick(self) -> None:
        self.tick_count += 1

    # -----------------------------------------------------
    # QUEUE MANAGEMENT
    # -----------------------------------------------------
    def remove_from_all_queues(self, process_id: CognitiveProcessId) -> None:
        for queue in (
            self.ready_queue,
            self.blocked_queue,
            self.suspended_queue,
            self.waiting_confirmation_queue,
            self.completed_queue,
            self.aborted_queue,
        ):
            while process_id in queue:
                queue.remove(process_id)

    def append_unique(
        self, queue: list[CognitiveProcessId], process_id: CognitiveProcessId
    ) -> None:
        if process_id not in queue:
            queue.append(process_id)

    # -----------------------------------------------------
    # INVARIANTS
    # -----------------------------------------------------
    def validate_single_running_invariant(self, running_count: int) -> None:
        if running_count > 1:
            raise RuntimeError(
                "Scheduler invariant violated: more than one RUNNING process"
            )
