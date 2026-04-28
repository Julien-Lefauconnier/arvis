# arvis/runtime/cognitive_scheduler.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, cast

from arvis.runtime.process_hooks import ProcessHookManager

from arvis.kernel_core.process import (
    CognitiveProcess,
    CognitiveProcessId,
    CognitiveProcessStatus,
)
from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState
from arvis.kernel_core.contracts.execution_contract import ProcessExecutor
from arvis.runtime.resource_model import ResourcePressure
from arvis.runtime.scheduler_decision import SchedulerDecision


@dataclass(frozen=True)
class SchedulingPolicyConfig:
    age_bonus_per_tick: float = 0.01
    pressure_penalty_scale: float = 5.0
    confirmation_penalty: float = 1000.0


class CognitiveScheduler:
    """
    V1 scheduler:
    - single running process invariant
    - deterministic score-based selection
    - one pipeline step per tick (preemptive execution)

    SCHEDULER INVARIANTS :

        1. At most one RUNNING process at any time
        2. Final states:
            - COMPLETED
            - ABORTED

            Parked states (non schedulable, resumable):
            - BLOCKED
            - WAITING_CONFIRMATION
            - SUSPENDED
        3. Only READY processes are schedulable.
        4. One tick = one execution step.
        4. outcome.completed=True is the only valid pipeline finalization trigger.


    """

    def __init__(
        self,
        runtime_state: CognitiveRuntimeState,
        process_executor: ProcessExecutor | None = None,
        *,
        policy: SchedulingPolicyConfig | None = None,
        pipeline_executor: ProcessExecutor | None = None,
        hooks: ProcessHookManager | None = None,
    ) -> None:
        executor = (
            process_executor if process_executor is not None else pipeline_executor
        )

        if executor is None:
            raise ValueError("A process executor is required")

        self.runtime_state = runtime_state
        self.process_executor = executor
        self.policy = policy or SchedulingPolicyConfig()
        self._interrupt_wakeup_pending = False
        # -----------------------------------------
        # Hooks are ALWAYS available (never None)
        # -----------------------------------------
        if hooks is None:
            hooks = ProcessHookManager(runtime_state=runtime_state)

        self.hooks = hooks

    def enqueue(self, process: CognitiveProcess) -> None:
        if process.is_final():
            raise ValueError(
                f"Cannot enqueue final process: {process.process_id.value} [{process.status.value}]"
            )
        self.runtime_state.register_process(process)
        state = self.runtime_state.scheduler_state
        state.remove_from_all_queues(process.process_id)
        process.mark_ready()
        state.append_unique(state.ready_queue, process.process_id)
        self.runtime_state.append_event(
            "process_enqueued",
            {
                "process_id": process.process_id.value,
                "kind": process.kind.value,
                "priority": process.priority.normalized(),
            },
        )

        self.hooks.on_enqueued(process)

    def suspend(
        self, process_id: CognitiveProcessId, reason: str = "suspended"
    ) -> None:
        process = self.runtime_state.get_process(process_id)
        state = self.runtime_state.scheduler_state
        state.remove_from_all_queues(process_id)
        if state.active_process_id == process_id:
            state.active_process_id = None
        process.mark_suspended(reason=reason)
        state.append_unique(state.suspended_queue, process_id)
        self.runtime_state.append_event(
            "process_suspended",
            {"process_id": process_id.value, "reason": reason},
        )

    def block(self, process_id: CognitiveProcessId, waiting_on: str) -> None:
        process = self.runtime_state.get_process(process_id)
        state = self.runtime_state.scheduler_state
        state.remove_from_all_queues(process_id)
        if state.active_process_id == process_id:
            state.active_process_id = None
        process.mark_blocked(waiting_on=waiting_on)
        state.append_unique(state.blocked_queue, process_id)
        self.runtime_state.append_event(
            "process_blocked",
            {"process_id": process_id.value, "waiting_on": waiting_on},
        )

    def wait_confirmation(self, process_id: CognitiveProcessId) -> None:
        process = self.runtime_state.get_process(process_id)
        state = self.runtime_state.scheduler_state
        state.remove_from_all_queues(process_id)
        if state.active_process_id == process_id:
            state.active_process_id = None
        process.mark_waiting_confirmation()
        state.append_unique(state.waiting_confirmation_queue, process_id)
        self.runtime_state.append_event(
            "process_waiting_confirmation",
            {"process_id": process_id.value},
        )

    def resume(self, process_id: CognitiveProcessId) -> None:
        process = self.runtime_state.get_process(process_id)
        state = self.runtime_state.scheduler_state
        state.remove_from_all_queues(process_id)
        process.mark_ready()
        state.append_unique(state.ready_queue, process_id)
        self.runtime_state.append_event(
            "process_resumed",
            {"process_id": process_id.value},
        )

    def tick(self) -> SchedulerDecision:
        state = self.runtime_state.scheduler_state
        state.note_tick()
        self.runtime_state.resource_state.note_tick()
        self._process_interrupts()

        # Important Do not schedule on interrupt wakeup tick
        if self._interrupt_wakeup_pending:
            self._interrupt_wakeup_pending = False
            return SchedulerDecision(
                selected_process_id=None,
                rationale="interrupt wakeup tick",
                resource_grant=None,
                score=None,
            )

        self._validate_invariants()

        decision = self._select_next_process()
        if decision.is_noop:
            self.runtime_state.append_event(
                "scheduler_noop",
                {"reason": decision.rationale},
            )
            return decision

        assert decision.selected_process_id is not None
        process = self.runtime_state.get_process(decision.selected_process_id)

        if process.status != CognitiveProcessStatus.READY:
            self.runtime_state.append_event(
                "scheduler_skipped_non_ready_process",
                {
                    "process_id": process.process_id.value,
                    "status": process.status.value,
                },
            )
            return decision

        state.remove_from_all_queues(process.process_id)
        state.active_process_id = process.process_id
        process.mark_running(tick=state.tick_count, score=decision.score)

        self.runtime_state.append_event(
            "scheduler_selected",
            {
                "process_id": process.process_id.value,
                "score": decision.score,
                "rationale": decision.rationale,
            },
        )

        self.hooks.on_selected(process, decision.score)

        try:
            outcome = self.process_executor.execute_process(process)
            process.consume(outcome.consumption)

            # =====================================================
            # FINALIZATION (single source of truth)
            # =====================================================

            if outcome.completed:
                result = outcome.result
                process.last_result = result

                requires_confirmation = getattr(result, "requires_confirmation", False)
                can_execute = getattr(result, "can_execute", True)

                # -----------------------------
                # Case 1: confirmation required
                # -----------------------------
                if requires_confirmation:
                    self.wait_confirmation(process.process_id)

                    self.hooks.on_waiting_confirmation(process)

                    decision.result = result
                    return decision

                # -----------------------------
                # Case 2: cannot execute → blocked
                # -----------------------------
                if not can_execute:
                    self.block(process.process_id, waiting_on="cannot_execute")

                    self.hooks.on_blocked(process, "cannot_execute")

                    decision.result = result
                    return decision

                # -----------------------------
                # Case 3: normal completion
                # -----------------------------
                process.mark_completed(result=result)
                state.active_process_id = None
                state.append_unique(state.completed_queue, process.process_id)
                self.runtime_state.append_event(
                    "process_completed",
                    {
                        "process_id": process.process_id.value,
                        "stage_name": outcome.stage_name,
                    },
                )

                self.hooks.on_completed(process, result)

                decision.result = result
                return decision

            # =====================================================
            # PREEMPTIVE EXECUTION LOGIC
            # =====================================================
            state.active_process_id = None

            if process.has_budget():
                process.last_result = None
                process.mark_ready()
                state.append_unique(state.ready_queue, process.process_id)

                self.runtime_state.append_event(
                    "process_preempted",
                    {
                        "process_id": process.process_id.value,
                        "stage_name": getattr(outcome, "stage_name", None),
                        "next_stage_index": getattr(
                            process, "current_stage_index", None
                        ),
                    },
                )

                return decision

            # -----------------------------
            # Budget exhausted BEFORE completion
            # -----------------------------
            process.mark_suspended(reason="budget_exhausted")
            state.append_unique(state.suspended_queue, process.process_id)

            self.hooks.on_suspended(process, "budget_exhausted")

            self.runtime_state.append_event(
                "process_suspended_budget_exhausted",
                {
                    "process_id": process.process_id.value,
                    "stage_name": getattr(outcome, "stage_name", None),
                    "next_stage_index": getattr(process, "current_stage_index", None),
                },
            )
            decision.result = None
            return decision

        except Exception as exc:
            # ----------------------------------------
            # Only TRUE execution errors should abort
            # ----------------------------------------
            # ----------------------------------------
            # NON-FATAL errors → let pipeline handle (retry etc.)
            # ----------------------------------------
            process.mark_aborted(error=str(exc))
            state.active_process_id = None
            state.append_unique(state.aborted_queue, process.process_id)
            self.runtime_state.append_event(
                "process_aborted",
                {
                    "process_id": process.process_id.value,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )

            self.hooks.on_aborted(process, str(exc))

            return SchedulerDecision(
                selected_process_id=process.process_id,
                rationale=f"execution failed: {type(exc).__name__}",
                resource_grant=process.remaining_budget(),
                score=process.last_score,
            )

    def _select_next_process(self) -> SchedulerDecision:
        state = self.runtime_state.scheduler_state
        if not state.ready_queue:
            return SchedulerDecision(
                selected_process_id=None,
                rationale="no ready process",
                resource_grant=None,
                score=None,
            )

        best_process: Optional[CognitiveProcess] = None
        best_score: Optional[float] = None

        for process_id in state.ready_queue:
            process = self.runtime_state.get_process(process_id)
            if not process.is_schedulable():
                continue

            score = self._score(process)
            if best_score is None or score > best_score:
                best_process = process
                best_score = score

        if best_process is None:
            return SchedulerDecision(
                selected_process_id=None,
                rationale="no schedulable ready process",
                resource_grant=None,
                score=None,
            )

        return SchedulerDecision(
            selected_process_id=best_process.process_id,
            rationale="highest scheduling score",
            resource_grant=best_process.remaining_budget(),
            score=best_score,
        )

    def _score(self, process: CognitiveProcess) -> float:
        priority_score = process.priority.normalized()
        age = max(
            0,
            self.runtime_state.scheduler_state.tick_count - process.created_tick,
        )
        age_bonus = age * self.policy.age_bonus_per_tick

        pressure = self.runtime_state.resource_state.pressure.total()
        pressure_penalty = pressure * self.policy.pressure_penalty_scale

        confirmation_penalty = 0.0
        if process.status == CognitiveProcessStatus.WAITING_CONFIRMATION:
            confirmation_penalty = self.policy.confirmation_penalty

        return priority_score + age_bonus - pressure_penalty - confirmation_penalty

    def _validate_invariants(self) -> None:
        running_count = sum(
            1
            for process in self.runtime_state.processes.values()
            if process.status == CognitiveProcessStatus.RUNNING
        )
        self.runtime_state.scheduler_state.validate_single_running_invariant(
            running_count
        )

    def set_resource_pressure(self, pressure: ResourcePressure) -> None:
        pressure.validate()
        self.runtime_state.resource_state.pressure = pressure

    # =====================================================
    # INTERRUPT PROCESSING
    # =====================================================
    def _process_interrupts(self) -> None:
        bus = self.runtime_state.interrupt_bus
        events = bus.drain()

        if not events:
            return

        state = self.runtime_state.scheduler_state

        woke_any_process = False

        for event in events:
            targets = cast(list[CognitiveProcessId], bus.match(event))

            # SYSTEM BROADCAST
            if event.type.value == "system_signal":
                targets = [
                    pid
                    for pid, proc in self.runtime_state.processes.items()
                    if not proc.is_final()
                ]

            for process_id in targets:
                if process_id not in self.runtime_state.processes:
                    continue

                process = self.runtime_state.get_process(process_id)

                if process.status in (
                    CognitiveProcessStatus.BLOCKED,
                    CognitiveProcessStatus.WAITING_CONFIRMATION,
                    CognitiveProcessStatus.SUSPENDED,
                ):
                    state.remove_from_all_queues(process_id)
                    process.mark_ready()
                    state.append_unique(state.ready_queue, process_id)
                    woke_any_process = True

                    self.runtime_state.append_event(
                        "process_resumed_by_interrupt",
                        {"process_id": process_id.value},
                    )

        # prevent execution this tick
        if woke_any_process:
            self._interrupt_wakeup_pending = True
