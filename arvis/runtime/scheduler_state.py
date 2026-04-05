# arvis/runtime/scheduler_state.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from arvis.runtime.cognitive_process import CognitiveProcessId


@dataclass
class SchedulerState:
    active_process_id: Optional[CognitiveProcessId] = None
    ready_queue: list[CognitiveProcessId] = field(default_factory=list)
    blocked_queue: list[CognitiveProcessId] = field(default_factory=list)
    waiting_confirmation_queue: list[CognitiveProcessId] = field(default_factory=list)
    suspended_queue: list[CognitiveProcessId] = field(default_factory=list)
    completed_queue: list[CognitiveProcessId] = field(default_factory=list)
    aborted_queue: list[CognitiveProcessId] = field(default_factory=list)
    tick_count: int = 0

    def validate_single_running_invariant(self, running_count: int) -> None:
        if running_count > 1:
            raise ValueError("Scheduler invariant violated: more than one running process")

    def note_tick(self) -> None:
        self.tick_count += 1

    def remove_from_all_queues(self, process_id: CognitiveProcessId) -> None:
        self.ready_queue = [pid for pid in self.ready_queue if pid != process_id]
        self.blocked_queue = [pid for pid in self.blocked_queue if pid != process_id]
        self.waiting_confirmation_queue = [
            pid for pid in self.waiting_confirmation_queue if pid != process_id
        ]
        self.suspended_queue = [pid for pid in self.suspended_queue if pid != process_id]
        self.completed_queue = [pid for pid in self.completed_queue if pid != process_id]
        self.aborted_queue = [pid for pid in self.aborted_queue if pid != process_id]