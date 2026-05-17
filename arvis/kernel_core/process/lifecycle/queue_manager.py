# arvis/kernel_core/process/lifecycle/queue_manager.py

from __future__ import annotations

from arvis.kernel_core.process.types import CognitiveProcessId
from arvis.kernel_core.state.scheduler_state import SchedulerState


class QueueManager:
    """
    Single authority for scheduler queue mutations.
    """

    def __init__(self, state: SchedulerState) -> None:
        self.state = state

    def remove_from_all(self, process_id: CognitiveProcessId) -> None:
        for queue in (
            self.state.ready_queue,
            self.state.blocked_queue,
            self.state.suspended_queue,
            self.state.waiting_confirmation_queue,
            self.state.completed_queue,
            self.state.aborted_queue,
        ):
            while process_id in queue:
                queue.remove(process_id)

    def append_unique(
        self,
        queue: list[CognitiveProcessId],
        process_id: CognitiveProcessId,
    ) -> None:
        if process_id not in queue:
            queue.append(process_id)

    def move_to_ready(self, process_id: CognitiveProcessId) -> None:
        self.remove_from_all(process_id)
        self.append_unique(self.state.ready_queue, process_id)

    def move_to_blocked(self, process_id: CognitiveProcessId) -> None:
        self.remove_from_all(process_id)
        self.append_unique(self.state.blocked_queue, process_id)

    def move_to_suspended(self, process_id: CognitiveProcessId) -> None:
        self.remove_from_all(process_id)
        self.append_unique(self.state.suspended_queue, process_id)

    def move_to_waiting_confirmation(
        self,
        process_id: CognitiveProcessId,
    ) -> None:
        self.remove_from_all(process_id)
        self.append_unique(
            self.state.waiting_confirmation_queue,
            process_id,
        )

    def move_to_completed(self, process_id: CognitiveProcessId) -> None:
        self.remove_from_all(process_id)
        self.append_unique(self.state.completed_queue, process_id)

    def move_to_aborted(self, process_id: CognitiveProcessId) -> None:
        self.remove_from_all(process_id)
        self.append_unique(self.state.aborted_queue, process_id)
