# # arvis/api/execution.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionTraceView:
    process_id: str | None
    execution_status: str | None

    can_execute: bool
    requires_confirmation: bool
    needs_confirmation: bool

    syscall_count: int
    error_count: int

    degraded: bool

    @staticmethod
    def from_execution_state(state: Any) -> ExecutionTraceView:
        syscall_results = getattr(state, "syscall_results", [])
        errors = getattr(state, "errors", [])

        return ExecutionTraceView(
            process_id=getattr(state, "process_id", None),
            execution_status=str(getattr(state, "execution_status", None)),
            can_execute=bool(getattr(state, "can_execute", False)),
            requires_confirmation=bool(getattr(state, "requires_confirmation", False)),
            needs_confirmation=bool(getattr(state, "needs_confirmation", False)),
            syscall_count=len(syscall_results),
            error_count=len(errors),
            degraded=len(errors) > 0,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": self.process_id,
            "execution_status": self.execution_status,
            "can_execute": self.can_execute,
            "requires_confirmation": self.requires_confirmation,
            "needs_confirmation": self.needs_confirmation,
            "syscall_count": self.syscall_count,
            "error_count": self.error_count,
            "degraded": self.degraded,
        }
