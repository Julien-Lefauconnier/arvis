# arvis/kernel_core/syscalls/syscalls/tool_syscalls.py

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, runtime_checkable

from arvis.kernel_core.syscalls.artifact import ExecutionArtifact
from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import register_syscall


@runtime_checkable
class ToolExecutorLike(Protocol):
    def execute(self, result: Any, ctx: Any) -> Any:
        ...


class ServiceRegistryLike(Protocol):
    tool_executor: Optional[ToolExecutorLike]


class SyscallHandlerLike(Protocol):
    services: ServiceRegistryLike
    runtime_state: Optional[Any]


def _compute_artifact_timestamp(
    handler: SyscallHandlerLike,
    kwargs: Dict[str, Any],
) -> float:
    """
    Kernel-controlled timestamp derivation.

    Priority:
    1. explicit tick syscall arg
    2. runtime scheduler tick
    3. fallback = 0.0
    """
    tick = kwargs.get("tick")
    if tick is not None:
        return float(tick)

    runtime_state = getattr(handler, "runtime_state", None)
    if runtime_state is not None:
        return float(runtime_state.scheduler_state.tick_count)

    return 0.0


@register_syscall("tool.execute")
def tool_execute(
    handler: SyscallHandlerLike,
    result: Any,
    ctx: Any,
    **kwargs: Any,
) -> SyscallResult:
    tool_executor = handler.services.tool_executor

    if tool_executor is None:
        return SyscallResult(
            success=False,
            error="no_tool_executor",
        )

    try:
        tool_result = tool_executor.execute(result, ctx)
    except Exception as exc:
        return SyscallResult(
            success=False,
            error=f"{type(exc).__name__}:{str(exc)}",
        )

    if tool_result is None:
        return SyscallResult(
            success=False,
            error="no_tool_execution",
        )

    if hasattr(tool_result, "success"):
        success = bool(getattr(tool_result, "success"))
        output = getattr(tool_result, "output", None)
        error = getattr(tool_result, "error", None)
        tool_name = getattr(tool_result, "tool_name", None)
    else:
        success = True
        output = tool_result
        error = None
        tool_name = None

    artifact = ExecutionArtifact(
        artifact_type="tool_execution",
        syscall="tool.execute",
        status="success" if success else "error",
        output=output,
        error=error,
        metadata={
            "tool": tool_name,
            "seq": getattr(handler, "_local_counter", 0),
        },
        replay_policy="journal_only_replay",
        process_id=kwargs.get("process_id"),
        tick=kwargs.get("tick"),
        timestamp=_compute_artifact_timestamp(handler, kwargs),
        causal_id=kwargs.get("causal_id"),
    )

    return SyscallResult(
        success=artifact.success,
        result=artifact,
        error=artifact.error,
    )