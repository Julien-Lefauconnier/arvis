# arvis/kernel_core/state/scheduler_state.py

from __future__ import annotations

from dataclasses import dataclass, field

from arvis.errors.runtime_scheduler import (
    SchedulerInvariantViolation,
)
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
    # INVARIANTS
    # -----------------------------------------------------
    def validate_single_running_invariant(self, running_count: int) -> None:
        if running_count > 1:
            raise SchedulerInvariantViolation(
                "Scheduler invariant violated: more than one RUNNING process",
                details={
                    "running_count": running_count,
                    "invariant": "single_running_process",
                    "retry_class": "permanent",
                },
            )
