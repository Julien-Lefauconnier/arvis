# arvis/kernel/execution/cognitive_execution_state.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from arvis.kernel.execution.execution_gate_status import ExecutionGateStatus
from arvis.kernel.execution.execution_llm_state import ExecutionLLMState


@dataclass(slots=True)
class CognitiveExecutionState:
    """
    Typed execution state for runtime-owned pipeline execution.

    Non-breaking first step:
    - does not replace CognitivePipelineContext yet
    - progressively absorbs ctx.extra runtime keys
    - remains IO-free and kernel-safe
    """

    process_id: str | None = None
    tick: int = 0

    llm: ExecutionLLMState = field(default_factory=ExecutionLLMState)

    syscall_results: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)

    # ---------------------------------
    # execution authority
    # ---------------------------------
    can_execute: bool = False
    requires_confirmation: bool = False
    needs_confirmation: bool = False

    execution_status: ExecutionGateStatus | None = None

    metadata: dict[str, Any] = field(default_factory=dict)
