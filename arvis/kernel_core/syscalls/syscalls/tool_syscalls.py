# arvis/kernel_core/syscalls/syscalls/tool_syscalls.py

from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable

from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import register_syscall

@runtime_checkable
class ToolExecutorLike(Protocol):
    def execute(self, result: Any, ctx: Any) -> Any: ...


class SyscallHandlerLike(Protocol):
    tool_executor: Optional[ToolExecutorLike]

@register_syscall("tool.execute")
def tool_execute(
    handler: SyscallHandlerLike,
    result: Any,
    ctx: Any,
) -> SyscallResult:
    if handler.tool_executor is None:
        return SyscallResult(success=False, error="no_tool_executor")

    try:
        output = handler.tool_executor.execute(result, ctx)
    except Exception as exc:
        return SyscallResult(
            success=False,
            error=f"{type(exc).__name__}:{str(exc)}",
        )


    if hasattr(output, "success"):
        success = bool(getattr(output, "success"))
        payload = getattr(output, "output", None)
        error = getattr(output, "error", None)
        return SyscallResult(
            success=success,
            result=payload,
            error=error,
        )

    return SyscallResult(
        success=True,
        result=output,
    )