# arvis/kernel_core/process/lifecycle/lifecycle_manager.py

from __future__ import annotations

from typing import Any

from arvis.kernel_core.process.lifecycle.queue_manager import QueueManager
from arvis.kernel_core.process.process import CognitiveProcess
from arvis.kernel_core.process.transitions import ProcessTransitionManager
from arvis.kernel_core.process.types import CognitiveProcessStatus


class LifecycleManager:
    """
    Single authority for process lifecycle transitions.

    Responsibilities:
    - transition legality
    - queue mutations
    - scheduler active process ownership
    """

    def __init__(
        self,
        runtime_state: Any,
    ) -> None:
        self.runtime_state = runtime_state
        self.queue_manager = QueueManager(runtime_state.scheduler_state)

    def transition(
        self,
        process: CognitiveProcess,
        target: CognitiveProcessStatus,
        *,
        tick: int | None = None,
        score: float | None = None,
        waiting_on: str | None = None,
        reason: str | None = None,
        result: Any = None,
        error: str | None = None,
    ) -> None:
        state = self.runtime_state.scheduler_state

        ProcessTransitionManager.transition(process, target)

        pid = process.process_id

        if target == CognitiveProcessStatus.READY:
            process.waiting_on = None
            self.queue_manager.move_to_ready(pid)

        elif target == CognitiveProcessStatus.BLOCKED:
            process.waiting_on = waiting_on
            self.queue_manager.move_to_blocked(pid)

        elif target == CognitiveProcessStatus.SUSPENDED:
            process.waiting_on = reason or "suspended"
            self.queue_manager.move_to_suspended(pid)

        elif target == CognitiveProcessStatus.WAITING_CONFIRMATION:
            process.waiting_on = waiting_on or "confirmation"
            self.queue_manager.move_to_waiting_confirmation(pid)

        elif target == CognitiveProcessStatus.COMPLETED:
            process.last_result = result
            process.waiting_on = None
            self.queue_manager.move_to_completed(pid)

        elif target == CognitiveProcessStatus.ABORTED:
            process.last_error = error
            self.queue_manager.move_to_aborted(pid)

        elif target == CognitiveProcessStatus.RUNNING:
            self.queue_manager.remove_from_all(pid)
            state.active_process_id = pid
            if tick is not None:
                process.last_run_tick = tick
            process.run_count += 1
            if score is not None:
                process.last_score = score
            return

        if state.active_process_id == pid:
            state.active_process_id = None
