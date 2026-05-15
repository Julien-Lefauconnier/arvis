# arvis/kernel_core/syscalls/syscalls/tool_syscalls.py

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from arvis.errors.base import (
    ArvisError,
    ArvisExternalError,
    ArvisRuntimeError,
    ErrorDomain,
)
from arvis.errors.normalization import normalize_error
from arvis.errors.provenance import cause_from_exception
from arvis.kernel_core.syscalls.artifact import ExecutionArtifact
from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import register_syscall


@runtime_checkable
class ToolManagerLike(Protocol):
    def run(self, result: Any, ctx: Any) -> Any: ...


class ServiceRegistryLike(Protocol):
    tool_manager: ToolManagerLike | None


class SyscallHandlerLike(Protocol):
    services: ServiceRegistryLike
    runtime_state: Any | None


def _compute_artifact_timestamp(
    handler: SyscallHandlerLike,
    kwargs: dict[str, Any],
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
    tool_manager = handler.services.tool_manager

    if tool_manager is None:
        return SyscallResult.failure(
            ArvisRuntimeError(
                "Tool manager not configured",
                code="no_tool_manager",
                domain=ErrorDomain.TOOL,
            )
        )

    try:
        tool_result = tool_manager.run(result, ctx)
    except Exception as exc:
        normalized = normalize_error(exc)

        return SyscallResult.failure(
            ArvisExternalError(
                normalized.message,
                code="tool_execution_failed",
                domain=ErrorDomain.TOOL,
                details={
                    "exception": type(exc).__name__,
                    "wrapped_error_code": normalized.code,
                    "wrapped_error_domain": normalized.domain.value,
                    "retry_class": "transient",
                },
                cause=cause_from_exception(exc),
                replay_safe=False,
            )
        )

    if tool_result is None:
        return SyscallResult.failure(
            ArvisRuntimeError(
                "Tool execution returned no result",
                code="no_tool_execution",
                domain=ErrorDomain.TOOL,
            )
        )

    if hasattr(tool_result, "success"):
        success = bool(tool_result.success)
        output = getattr(tool_result, "output", None)
        error = getattr(tool_result, "error", None)
        tool_name = getattr(tool_result, "tool_name", None)
    else:
        success = True
        output = tool_result
        error = None
        tool_name = None

    normalized_error: ArvisError | None = None

    if error is not None:
        if isinstance(error, ArvisError):
            normalized_error = error
        elif isinstance(error, Exception):
            wrapped_error = normalize_error(error)
            normalized_error = ArvisExternalError(
                wrapped_error.message,
                code="tool_execution_error",
                domain=ErrorDomain.TOOL,
                details={
                    "exception": type(error).__name__,
                    "wrapped_error_code": wrapped_error.code,
                    "wrapped_error_domain": wrapped_error.domain.value,
                    "retry_class": "transient",
                },
                cause=cause_from_exception(error),
                replay_safe=False,
            )
        else:
            normalized_error = ArvisRuntimeError(
                str(error),
                code="tool_execution_error",
                domain=ErrorDomain.TOOL,
            )

    if not success and normalized_error is None:
        normalized_error = ArvisRuntimeError(
            "Tool execution failed without explicit error",
            code="tool_execution_unknown_failure",
            domain=ErrorDomain.TOOL,
            details={
                "retry_class": "unknown",
            },
        )

    artifact = ExecutionArtifact(
        artifact_type="tool_execution",
        syscall="tool.execute",
        status="success" if success else "error",
        output=output,
        error=normalized_error,
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
