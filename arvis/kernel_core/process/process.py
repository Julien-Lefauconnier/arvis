# arvis/kernel_core/process/process.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from arvis.kernel_core.process.budget import BudgetConsumption, CognitiveBudget
from arvis.kernel_core.process.priority import CognitivePriority
from arvis.kernel_core.process.transitions import ProcessTransitionManager
from arvis.kernel_core.process.types import (
    CognitiveProcessId,
    CognitiveProcessStatus,
    CognitiveProcessKind,
)

from arvis.kernel_core.process.process_descriptor import ProcessDescriptor
from arvis.kernel_core.process.process_runtime_state import ProcessRuntimeState
from arvis.kernel_core.process.process_execution_state import ProcessExecutionState
from arvis.kernel_core.process.process_interrupt_state import ProcessInterruptState


@dataclass(init=False)
class CognitiveProcess:
    """
    V2 façade (backward compatible).

    Internally split into:
    - descriptor (immutable-ish identity)
    - runtime (scheduler state)
    - execution (pipeline state)
    - interrupts (event subscriptions)
    """

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Dual constructor:
        - V1 (legacy): process_id=..., kind=..., ...
        - V2 (new): descriptor=..., runtime=..., ...
        """

        # -----------------------------------------
        # V2 PATH (new kernel)
        # -----------------------------------------
        if "descriptor" in kwargs:
            self.descriptor = kwargs["descriptor"]
            self.runtime = kwargs["runtime"]
            self.execution = kwargs["execution"]
            self.interrupts = kwargs["interrupts"]
            self.local_state = kwargs.get("local_state")
            return

        # -----------------------------------------
        # V1 PATH (legacy compatibility)
        # -----------------------------------------
        descriptor = ProcessDescriptor(
            process_id=kwargs["process_id"],
            kind=kwargs["kind"],
            priority=kwargs["priority"],
            budget=kwargs["budget"],
            created_tick=kwargs["created_tick"],
            user_id=kwargs.get("user_id"),
            parent_process_id=kwargs.get("parent_process_id"),
            metadata=kwargs.get("metadata", {}),
        )

        runtime = ProcessRuntimeState(
            status=kwargs["status"],
        )

        execution = ProcessExecutionState()
        interrupts = ProcessInterruptState()

        # legacy fields migration
        runtime.waiting_on = kwargs.get("waiting_on")

        runtime.last_result = kwargs.get("last_result")
        runtime.last_error = kwargs.get("last_error")
        runtime.last_score = kwargs.get("last_score")

        runtime.run_count = kwargs.get("run_count", 0)
        runtime.last_run_tick = kwargs.get("last_run_tick")

        runtime.consumed_reasoning_steps = kwargs.get("consumed_reasoning_steps", 0)
        runtime.consumed_attention_tokens = kwargs.get("consumed_attention_tokens", 0)
        runtime.consumed_uncertainty = kwargs.get("consumed_uncertainty", 0.0)
        runtime.consumed_elapsed_ms = kwargs.get("consumed_elapsed_ms", 0)
        runtime.consumed_memory_span = kwargs.get("consumed_memory_span", 0)

        execution.current_stage_index = kwargs.get("current_stage_index", 0)
        execution.stage_history = kwargs.get("stage_history", [])
        execution.total_stage_count = kwargs.get("total_stage_count")
        execution.pipeline_prepared = kwargs.get("pipeline_prepared", False)
        execution.pipeline_finalized = kwargs.get("pipeline_finalized", False)

        interrupts.subscribed_interrupts = kwargs.get(
            "subscribed_interrupts", set()
        )

        self.descriptor = descriptor
        self.runtime = runtime
        self.execution = execution
        self.interrupts = interrupts
        self.local_state = kwargs.get("local_state")

    descriptor: ProcessDescriptor
    runtime: ProcessRuntimeState
    execution: ProcessExecutionState
    interrupts: ProcessInterruptState
    local_state: Any

    # -------------------------
    # BACKWARD COMPAT PROPERTIES
    # -------------------------

    @property
    def process_id(self) -> CognitiveProcessId:
        return self.descriptor.process_id

    @property
    def kind(self) -> CognitiveProcessKind:
        return self.descriptor.kind

    @property
    def priority(self) -> CognitivePriority:
        return self.descriptor.priority

    @property
    def budget(self) -> CognitiveBudget:
        return self.descriptor.budget

    @property
    def created_tick(self) -> int:
        return self.descriptor.created_tick

    @property
    def user_id(self) -> Optional[str]:
        return self.descriptor.user_id

    @property
    def parent_process_id(self) -> Optional[CognitiveProcessId]:
        return self.descriptor.parent_process_id

    @property
    def metadata(self) -> dict[str, Any]:
        return self.descriptor.metadata

    # runtime

    @property
    def status(self) -> CognitiveProcessStatus:
        return self.runtime.status

    @status.setter
    def status(self, value: CognitiveProcessStatus) -> None:
        self.runtime.status = value

    @property
    def waiting_on(self) -> Optional[str]:
        return self.runtime.waiting_on

    @waiting_on.setter
    def waiting_on(self, value: Optional[str]) -> None:
        self.runtime.waiting_on = value

    # execution

    @property
    def current_stage_index(self) -> int:
        return self.execution.current_stage_index

    @current_stage_index.setter
    def current_stage_index(self, value: int) -> None:
        self.execution.current_stage_index = value

    @property
    def stage_history(self) -> list[str]:
        return self.execution.stage_history

    @stage_history.setter
    def stage_history(self, value: list[str]) -> None:
        self.execution.stage_history = value

    @property
    def total_stage_count(self) -> Optional[int]:
        return self.execution.total_stage_count

    @total_stage_count.setter
    def total_stage_count(self, value: Optional[int]) -> None:
        self.execution.total_stage_count = value

    @property
    def pipeline_prepared(self) -> bool:
        return self.execution.pipeline_prepared

    @pipeline_prepared.setter
    def pipeline_prepared(self, value: bool) -> None:
        self.execution.pipeline_prepared = value

    @property
    def pipeline_finalized(self) -> bool:
        return self.execution.pipeline_finalized

    @pipeline_finalized.setter
    def pipeline_finalized(self, value: bool) -> None:
        self.execution.pipeline_finalized = value

    # interrupts

    @property
    def subscribed_interrupts(self) -> set[str]:
        return self.interrupts.subscribed_interrupts

    @subscribed_interrupts.setter
    def subscribed_interrupts(self, value: set[str]) -> None:
        self.interrupts.subscribed_interrupts = value

    # -------------------------
    # BUDGET
    # -------------------------

    def remaining_budget(self) -> CognitiveBudget:
        return CognitiveBudget(
            reasoning_steps=max(
                0,
                self.budget.reasoning_steps
                - self.runtime.consumed_reasoning_steps,
            ),
            attention_tokens=max(
                0,
                self.budget.attention_tokens
                - self.runtime.consumed_attention_tokens,
            ),
            uncertainty_budget=max(
                0.0,
                self.budget.uncertainty_budget
                - self.runtime.consumed_uncertainty,
            ),
            time_slice_ms=max(
                0,
                self.budget.time_slice_ms
                - self.runtime.consumed_elapsed_ms,
            ),
            memory_span=max(
                0,
                self.budget.memory_span
                - self.runtime.consumed_memory_span,
            ),
        )

    def has_budget(self) -> bool:
        remaining = self.remaining_budget()
        return remaining.reasoning_steps > 0 and remaining.time_slice_ms > 0

    def consume(self, consumption: BudgetConsumption) -> None:
        consumption.validate()
        self.runtime.consumed_reasoning_steps += consumption.reasoning_steps
        self.runtime.consumed_attention_tokens += consumption.attention_tokens
        self.runtime.consumed_uncertainty += consumption.uncertainty_spent
        self.runtime.consumed_elapsed_ms += consumption.elapsed_ms
        self.runtime.consumed_memory_span += consumption.memory_span_used

    # -------------------------
    # STATE
    # -------------------------

    def is_terminal(self) -> bool:
        return self.status in (
            CognitiveProcessStatus.COMPLETED,
            CognitiveProcessStatus.ABORTED,
        )

    def mark_running(self, tick: int, score: Optional[float] = None) -> None:
        ProcessTransitionManager.transition(self, CognitiveProcessStatus.RUNNING)
        self.runtime.last_run_tick = tick
        self.runtime.run_count += 1
        if score is not None:
            self.runtime.last_score = score

    def mark_ready(self) -> None:
        ProcessTransitionManager.transition(self, CognitiveProcessStatus.READY)
        self.waiting_on = None

    def mark_blocked(self, waiting_on: str) -> None:
        ProcessTransitionManager.transition(self, CognitiveProcessStatus.BLOCKED)
        self.waiting_on = waiting_on

    def mark_waiting_confirmation(self, waiting_on: str = "confirmation") -> None:
        ProcessTransitionManager.transition(
            self, CognitiveProcessStatus.WAITING_CONFIRMATION
        )
        self.waiting_on = waiting_on

    def mark_suspended(self, reason: str = "suspended") -> None:
        ProcessTransitionManager.transition(self, CognitiveProcessStatus.SUSPENDED)
        self.waiting_on = reason

    def mark_completed(self, result: Any = None) -> None:
        ProcessTransitionManager.transition(self, CognitiveProcessStatus.COMPLETED)
        self.runtime.last_result = result
        self.waiting_on = None

    def mark_aborted(self, error: str) -> None:
        ProcessTransitionManager.transition(self, CognitiveProcessStatus.ABORTED)
        self.runtime.last_error = error

    # -------------------------
    # EXECUTION STATE
    # -------------------------

    def set_total_stage_count(self, count: int) -> None:
        if count < 0:
            raise ValueError("total stage count must be >= 0")
        self.execution.total_stage_count = count

    def has_remaining_stages(self) -> bool:
        if self.execution.total_stage_count is None:
            return True
        return (
            self.execution.current_stage_index
            < self.execution.total_stage_count
        )

    def advance_stage(self, stage_name: str) -> None:
        self.execution.stage_history.append(stage_name)
        self.execution.current_stage_index += 1

    def mark_pipeline_prepared(self) -> None:
        self.execution.pipeline_prepared = True

    def mark_pipeline_finalized(self) -> None:
        self.execution.pipeline_finalized = True

    # -------------------------
    # VALIDATION
    # -------------------------

    def validate(self) -> None:
        self.budget.validate()
        if not self.process_id.value:
            raise ValueError("process_id.value must not be empty")
        if self.priority.normalized() < 0.0:
            raise ValueError("priority must be >= 0")
        if self.execution.current_stage_index < 0:
            raise ValueError("current_stage_index must be >= 0")
        if (
            self.execution.total_stage_count is not None
            and self.execution.total_stage_count < 0
        ):
            raise ValueError("total_stage_count must be >= 0")
        
    
    # -------------------------
    # BACKWARD COMPAT - RUNTIME
    # -------------------------

    @property
    def last_result(self) -> Any:
        return self.runtime.last_result

    @last_result.setter
    def last_result(self, value: Any) -> None:
        self.runtime.last_result = value


    @property
    def last_error(self) -> Optional[str]:
        return self.runtime.last_error

    @last_error.setter
    def last_error(self, value: Optional[str]) -> None:
        self.runtime.last_error = value

    @property
    def error(self) -> Optional[str]:
        return self.runtime.last_error

    @error.setter
    def error(self, value: Optional[str]) -> None:
        self.runtime.last_error = value

    @property
    def last_score(self) -> Optional[float]:
        return self.runtime.last_score

    @last_score.setter
    def last_score(self, value: Optional[float]) -> None:
        self.runtime.last_score = value

    @property
    def run_count(self) -> int:
        return self.runtime.run_count

    @run_count.setter
    def run_count(self, value: int) -> None:
        self.runtime.run_count = value


    @property
    def last_run_tick(self) -> Optional[int]:
        return self.runtime.last_run_tick

    @last_run_tick.setter
    def last_run_tick(self, value: Optional[int]) -> None:
        self.runtime.last_run_tick = value