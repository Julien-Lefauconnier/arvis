# arvis/runtime/cognitive_process.py

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


@dataclass(frozen=True)
class CognitiveProcessId:
    value: str


class CognitiveProcessStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    WAITING_CONFIRMATION = "waiting_confirmation"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    ABORTED = "aborted"


class CognitiveProcessKind(str, Enum):
    USER_REQUEST = "user_request"
    MEMORY_CONSOLIDATION = "memory_consolidation"
    CONFLICT_RESOLUTION = "conflict_resolution"
    EXPLANATION = "explanation"
    COUNTERFACTUAL = "counterfactual"
    GOVERNANCE_REVIEW = "governance_review"
    REFLEXIVE_INTROSPECTION = "reflexive_introspection"
    SYSTEM_MAINTENANCE = "system_maintenance"


@dataclass(frozen=True)
class CognitivePriority:
    value: float

    def normalized(self) -> float:
        if self.value < 0.0:
            return 0.0
        if self.value > 100.0:
            return 100.0
        return float(self.value)


@dataclass(frozen=True)
class CognitiveBudget:
    """
    Initial V1 budget dimensions.

    These are OS-level cognitive resources, not model/provider resources.
    """
    reasoning_steps: int = 1
    attention_tokens: int = 100
    uncertainty_budget: float = 1.0
    time_slice_ms: int = 50
    memory_span: int = 10

    def validate(self) -> None:
        if self.reasoning_steps < 0:
            raise ValueError("reasoning_steps must be >= 0")
        if self.attention_tokens < 0:
            raise ValueError("attention_tokens must be >= 0")
        if self.uncertainty_budget < 0.0:
            raise ValueError("uncertainty_budget must be >= 0")
        if self.time_slice_ms < 0:
            raise ValueError("time_slice_ms must be >= 0")
        if self.memory_span < 0:
            raise ValueError("memory_span must be >= 0")


@dataclass(frozen=True)
class BudgetConsumption:
    reasoning_steps: int = 0
    attention_tokens: int = 0
    uncertainty_spent: float = 0.0
    elapsed_ms: int = 0
    memory_span_used: int = 0

    def validate(self) -> None:
        if self.reasoning_steps < 0:
            raise ValueError("reasoning_steps must be >= 0")
        if self.attention_tokens < 0:
            raise ValueError("attention_tokens must be >= 0")
        if self.uncertainty_spent < 0.0:
            raise ValueError("uncertainty_spent must be >= 0")
        if self.elapsed_ms < 0:
            raise ValueError("elapsed_ms must be >= 0")
        if self.memory_span_used < 0:
            raise ValueError("memory_span_used must be >= 0")


@dataclass
class CognitiveProcess:
    process_id: CognitiveProcessId
    kind: CognitiveProcessKind
    status: CognitiveProcessStatus
    priority: CognitivePriority
    budget: CognitiveBudget
    local_state: Any
    created_tick: int
    user_id: Optional[str] = None
    parent_process_id: Optional[CognitiveProcessId] = None
    waiting_on: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    consumed_reasoning_steps: int = 0
    consumed_attention_tokens: int = 0
    consumed_uncertainty: float = 0.0
    consumed_elapsed_ms: int = 0
    consumed_memory_span: int = 0

    last_result: Any = None
    last_error: Optional[str] = None
    last_score: Optional[float] = None
    run_count: int = 0
    last_run_tick: Optional[int] = None

    # -----------------------------------------------------
    # Iterative pipeline state (NEW)
    # -----------------------------------------------------
    current_stage_index: int = 0
    stage_history: list[str] = field(default_factory=list)
    total_stage_count: Optional[int] = None
    pipeline_prepared: bool = False
    pipeline_finalized: bool = False

    def __post_init__(self)-> None:
        # defensive safety (important si désérialisation future)
        if self.stage_history is None:
            object.__setattr__(self, "stage_history", [])

    def remaining_budget(self) -> CognitiveBudget:
        return CognitiveBudget(
            reasoning_steps=max(0, self.budget.reasoning_steps - self.consumed_reasoning_steps),
            attention_tokens=max(0, self.budget.attention_tokens - self.consumed_attention_tokens),
            uncertainty_budget=max(0.0, self.budget.uncertainty_budget - self.consumed_uncertainty),
            time_slice_ms=max(0, self.budget.time_slice_ms - self.consumed_elapsed_ms),
            memory_span=max(0, self.budget.memory_span - self.consumed_memory_span),
        )

    def has_budget(self) -> bool:
        remaining = self.remaining_budget()
        return (
            remaining.reasoning_steps > 0
            and remaining.time_slice_ms > 0
        )
    

    
    def is_terminal(self) -> bool:
        return self.status in (
            CognitiveProcessStatus.COMPLETED,
            CognitiveProcessStatus.ABORTED,
        )

    def set_total_stage_count(self, count: int) -> None:
        if count < 0:
            raise ValueError("total stage count must be >= 0")
        self.total_stage_count = count

    def has_remaining_stages(self) -> bool:
        if self.total_stage_count is None:
            return True
        return self.current_stage_index < self.total_stage_count

    def advance_stage(self, stage_name: str) -> None:
        self.stage_history.append(stage_name)
        self.current_stage_index += 1

    def mark_pipeline_prepared(self) -> None:
        self.pipeline_prepared = True

    def mark_pipeline_finalized(self) -> None:
        self.pipeline_finalized = True

    def consume(self, consumption: BudgetConsumption) -> None:
        consumption.validate()
        self.consumed_reasoning_steps += consumption.reasoning_steps
        self.consumed_attention_tokens += consumption.attention_tokens
        self.consumed_uncertainty += consumption.uncertainty_spent
        self.consumed_elapsed_ms += consumption.elapsed_ms
        self.consumed_memory_span += consumption.memory_span_used

    def mark_running(self, tick: int, score: Optional[float] = None) -> None:
        self.status = CognitiveProcessStatus.RUNNING
        self.last_run_tick = tick
        self.run_count += 1
        if score is not None:
            self.last_score = score

    def mark_ready(self) -> None:
        self.status = CognitiveProcessStatus.READY
        self.waiting_on = None

    def mark_blocked(self, waiting_on: str) -> None:
        self.status = CognitiveProcessStatus.BLOCKED
        self.waiting_on = waiting_on

    def mark_waiting_confirmation(self, waiting_on: str = "confirmation") -> None:
        self.status = CognitiveProcessStatus.WAITING_CONFIRMATION
        self.waiting_on = waiting_on

    def mark_suspended(self, reason: str = "suspended") -> None:
        self.status = CognitiveProcessStatus.SUSPENDED
        self.waiting_on = reason

    def mark_completed(self, result: Any = None) -> None:
        self.status = CognitiveProcessStatus.COMPLETED
        self.last_result = result
        self.waiting_on = None

    def mark_aborted(self, error: str) -> None:
        self.status = CognitiveProcessStatus.ABORTED
        self.last_error = error

    def validate(self) -> None:
        self.budget.validate()
        if not self.process_id.value:
            raise ValueError("process_id.value must not be empty")
        if self.priority.normalized() < 0.0:
            raise ValueError("priority must be >= 0")
        if self.current_stage_index < 0:
            raise ValueError("current_stage_index must be >= 0")
        if self.total_stage_count is not None and self.total_stage_count < 0:
            raise ValueError("total_stage_count must be >= 0")
        if self.stage_history is None:
            raise ValueError("stage_history must be initialized")