# arvis/kernel_core/syscalls/syscalls/tool_syscalls.py

from __future__ import annotations

from typing import Any, Protocol

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
from arvis.tools.manager import ToolAuthorizationOutcome


class SyscallHandlerLike(Protocol):
    runtime_state: Any | None

    def _execute_tool_authorized(
        self, authorized: Any, result: Any, ctx: Any
    ) -> Any: ...


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


def _dispatch_authorized_tool(
    handler: SyscallHandlerLike,
    result: Any,
    ctx: Any,
    authorization: ToolAuthorizationOutcome,
) -> Any:
    if authorization.refusal is not None:
        return authorization.refusal
    if authorization.authorized is not None:
        return handler._execute_tool_authorized(
            authorization.authorized,
            result,
            ctx,
        )
    return None


def _normalize_tool_error(tool_error: Any, success: bool) -> ArvisError | None:
    normalized: ArvisError | None = None
    if tool_error is not None:
        if isinstance(tool_error, ArvisError):
            normalized = tool_error
            normalized.details.setdefault("classification", "external")
            normalized.details.setdefault("retry_class", "transient")
        elif isinstance(tool_error, Exception):
            normalized = ErrorManager.normalize_for_boundary(
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
            normalized = ArvisRuntimeError(
                str(tool_error),
                code="tool_execution_error",
                domain=ErrorDomain.TOOL,
            )
    if not success and normalized is None:
        normalized = ArvisRuntimeError(
            "Tool execution failed without explicit error",
            code="tool_execution_unknown_failure",
            domain=ErrorDomain.TOOL,
            details={"retry_class": "unknown"},
        )
    return normalized


def _build_tool_artifact(
    handler: SyscallHandlerLike,
    tool_result: Any,
    kwargs: dict[str, Any],
) -> ExecutionArtifact:
    if hasattr(tool_result, "success"):
        success = bool(tool_result.success)
        output = getattr(tool_result, "output", None)
        tool_error = getattr(tool_result, "error", None)
        tool_name = getattr(tool_result, "tool_name", None)
    else:
        success = True
        output = tool_result
        tool_error = None
        tool_name = None

    normalized_error = _normalize_tool_error(tool_error, success)
    return ExecutionArtifact(
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
    authorization: Any | None = None,
    **kwargs: Any,
) -> SyscallResult:
    if not callable(getattr(handler, "_execute_tool_authorized", None)):
        return SyscallResult.failure(
            ArvisRuntimeError(
                "Tool manager not configured",
                code="no_tool_manager",
                domain=ErrorDomain.TOOL,
            )
        )
    if type(authorization) is not ToolAuthorizationOutcome:
        return SyscallResult.failure(
            ArvisRuntimeError(
                "Tool execution requires an exact authorization outcome",
                code="invalid_tool_authorization_outcome",
                domain=ErrorDomain.TOOL,
            )
        )

    try:
        tool_result = _dispatch_authorized_tool(
            handler,
            result,
            ctx,
            authorization,
        )
    except Exception as exc:
        return SyscallResult.failure(
            ErrorManager.normalize_for_boundary(
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
        )
    if tool_result is None:
        return SyscallResult.failure(
            ArvisRuntimeError(
                "Tool execution returned no result",
                code="no_tool_execution",
                domain=ErrorDomain.TOOL,
            )
        )

    artifact = _build_tool_artifact(handler, tool_result, kwargs)
    return SyscallResult(
        success=artifact.success,
        result=artifact,
        error=artifact.error,
    )
