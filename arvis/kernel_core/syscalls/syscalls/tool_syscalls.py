# arvis/kernel_core/syscalls/syscalls/tool_syscalls.py

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from arvis.errors.base import (
    ArvisError,
    ArvisRuntimeError,
    ErrorDomain,
)
from arvis.errors.manager import ErrorManager
from arvis.errors.provenance import ErrorOrigin
from arvis.kernel_core.access.resolvers import turn_owner_resolver
from arvis.kernel_core.syscalls.artifact import ExecutionArtifact
from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import (
    SyscallEffect,
    register_syscall,
)


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


@register_syscall(
    "tool.execute",
    effect=SyscallEffect.EFFECT,
    triggers_external=True,
    summary="Execute an external tool.",
    access=turn_owner_resolver(SyscallEffect.EFFECT, "tool.execute"),
)
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
        error = ErrorManager.normalize_for_boundary(
            exc,
            boundary="external",
            code="tool_execution_failed",
            domain=ErrorDomain.TOOL,
            origin=ErrorOrigin(
                component="tool.execute",
                subsystem="kernel.syscall",
                syscall="tool.execute",
            ),
            details={
                "syscall": "tool.execute",
                "retry_class": "transient",
            },
        )

        return SyscallResult.failure(error)

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
        tool_error: Any | None = getattr(tool_result, "error", None)
        tool_name = getattr(tool_result, "tool_name", None)
    else:
        success = True
        output = tool_result
        tool_error = None
        tool_name = None

    normalized_error: ArvisError | None = None

    if tool_error is not None:
        if isinstance(tool_error, ArvisError):
            normalized_error = tool_error

            normalized_error.details.setdefault(
                "classification",
                "external",
            )
            normalized_error.details.setdefault(
                "retry_class",
                "transient",
            )
        elif isinstance(tool_error, Exception):
            normalized_error = ErrorManager.normalize_for_boundary(
                tool_error,
                boundary="external",
                code="tool_execution_error",
                domain=ErrorDomain.TOOL,
                details={
                    "classification": "external",
                    "retry_class": "transient",
                },
            )
        else:
            normalized_error = ArvisRuntimeError(
                str(tool_error),
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
            "retry_attempt": int(kwargs.get("retry_attempt") or 0),
            "retry_chain_id": kwargs.get("retry_chain_id"),
            "retry_parent_syscall_id": kwargs.get("retry_parent_syscall_id"),
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
