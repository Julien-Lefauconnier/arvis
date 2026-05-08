# arvis/runtime/execution/execution_llm_state.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ExecutionLLMState:
    observation: dict[str, Any] | None = None
    evaluation: dict[str, Any] | None = None
    risk_signal: dict[str, float] | None = None
    retry_events: list[dict[str, Any]] = field(default_factory=list)
    validation_errors: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
