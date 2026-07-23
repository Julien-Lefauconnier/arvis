"""Capability-consuming effect dispatcher.

This module owns the transition from an ACTIVE capability to one classified
``ToolResult``. ``ToolExecutor`` remains the private composition facade; the
large effect body is isolated here for review and testing.
"""

from __future__ import annotations

import time
from contextlib import suppress
from typing import Any

from arvis.errors import normalize_error
from arvis.errors.base import ArvisSecurityError
from arvis.errors.tool_runtime import (
    ToolExecutionError,
    ToolInputValidationError,
    ToolOutputValidationError,
    ToolTimeoutError,
    UnknownToolError,
)
from arvis.tools.authorized_invocation import (
    AuthorizedInvocation,
    InvocationAuthority,
    UnauthorizedExecutionError,
)
from arvis.tools.registry import ToolRegistry
from arvis.tools.tool_result import (
    EFFECT_COMPLETED,
    EFFECT_FAILED,
    EFFECT_NOT_STARTED,
    PRE_EFFECT_REFUSAL,
    ToolResult,
)
from arvis.tools.tool_schema import schema_violation


class EffectDispatcher:
    """Consume exactly one capability and dispatch its frozen invocation."""

    def __init__(
        self,
        registry: ToolRegistry,
        authority: InvocationAuthority,
    ) -> None:
        self._registry = registry
        self._authority = authority

    def dispatch(
        self,
        authorized: AuthorizedInvocation,
        result: Any,
        ctx: Any,
    ) -> ToolResult | None:
        """Execute one active capability with explicit boundary semantics."""
        if not isinstance(
            authorized, AuthorizedInvocation
        ) or not self._authority.consume(authorized):
            raise UnauthorizedExecutionError(
                "tool execution requires an active, registered, intact and unused "
                "AuthorizedInvocation minted by the tool manager's policy"
            )

        invocation = authorized.invocation
        tool_name = invocation.tool_name
        try:
            prepared = self._prepare(invocation, result, ctx)
        except Exception as exc:  # arvis-broad: normalize pre-effect preparation
            with suppress(Exception):
                ctx._tool_failure = True
            return self._preparation_failure(tool_name, exc)
        if prepared is None or isinstance(prepared, ToolResult):
            return prepared

        decision, tool, spec = prepared
        try:
            execution_payload = invocation.materialize_payload()
            payload_runtime: dict[str, Any] = {
                "decision": decision,
                "effect_context": invocation.effect_context,
                "tool_payload": execution_payload,
                "idempotency_key": invocation.idempotency_key,
                "invocation": invocation,
            }
            start = time.perf_counter()
            if hasattr(tool, "execute_invocation"):
                output = tool.execute_invocation(invocation)
            else:
                output = tool.execute(payload_runtime)
            latency = (time.perf_counter() - start) * 1000
            return self._classify_output(
                tool_name=tool_name,
                output=output,
                latency=latency,
                spec=spec,
                ctx=ctx,
            )
        except Exception as exc:
            ctx._tool_failure = True
            normalized_error = normalize_error(exc)
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=ToolExecutionError(
                    normalized_error.message,
                    cause=normalized_error.cause,
                    details={"exception_type": type(exc).__name__},
                ),
                latency_ms=None,
                effect_boundary=EFFECT_FAILED,
            )

    def _prepare(
        self,
        invocation: Any,
        result: Any,
        ctx: Any,
    ) -> tuple[Any, Any, Any] | ToolResult | None:
        if result is None or ctx is None:
            return None
        decision = getattr(result, "action_decision", None)
        if decision is None:
            return None

        tool_name = invocation.tool_name
        validation_payload = invocation.materialize_payload()
        validation_runtime: dict[str, Any] = {
            "decision": decision,
            "effect_context": invocation.effect_context,
            "tool_payload": validation_payload,
            "idempotency_key": invocation.idempotency_key,
            "invocation": invocation,
        }
        tool = self._registry.get(tool_name)
        if tool is None:
            ctx._tool_failure = True
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=UnknownToolError(f"Unknown tool: {tool_name}"),
                latency_ms=None,
                effect_boundary=PRE_EFFECT_REFUSAL,
            )

        try:
            spec = self._registry.verified_spec(tool_name)
        except ArvisSecurityError as exc:
            ctx._tool_failure = True
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=exc,
                latency_ms=None,
                effect_boundary=PRE_EFFECT_REFUSAL,
            )
        if spec is not None:
            ctx._last_tool_spec = spec
        if spec is not None and spec.input_schema:
            violation = schema_violation(validation_payload, spec.input_schema)
            if violation is not None:
                ctx._tool_failure = True
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error=ToolInputValidationError(
                        f"tool {tool_name!r} input violates its declared input_schema",
                        details={"schema_path": violation},
                    ),
                    latency_ms=None,
                    effect_boundary=PRE_EFFECT_REFUSAL,
                )
        try:
            tool.validate(validation_runtime)
        except Exception as exc:
            ctx._tool_failure = True
            normalized_error = normalize_error(exc)
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=ToolExecutionError(
                    normalized_error.message,
                    cause=normalized_error.cause,
                    details={
                        "exception_type": type(exc).__name__,
                        "phase": "tool_validate",
                    },
                ),
                latency_ms=None,
                effect_boundary=EFFECT_NOT_STARTED,
            )
        return decision, tool, spec

    @staticmethod
    def _preparation_failure(tool_name: str, exc: Exception) -> ToolResult:
        normalized_error = normalize_error(exc)
        return ToolResult(
            tool_name=tool_name,
            success=False,
            error=ToolExecutionError(
                normalized_error.message,
                cause=normalized_error.cause,
                details={
                    "exception_type": type(exc).__name__,
                    "phase": "pre_effect_preparation",
                },
            ),
            latency_ms=None,
            effect_boundary=EFFECT_NOT_STARTED,
        )

    @staticmethod
    def _classify_output(
        *,
        tool_name: str,
        output: Any,
        latency: float,
        spec: Any,
        ctx: Any,
    ) -> ToolResult:
        if (
            spec is not None
            and spec.timeout_seconds is not None
            and latency > float(spec.timeout_seconds) * 1000.0
        ):
            ctx._tool_failure = True
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=ToolTimeoutError(
                    f"tool {tool_name!r} exceeded its declared timeout",
                    details={
                        "timeout_seconds": spec.timeout_seconds,
                        "elapsed_ms": round(latency, 3),
                    },
                ),
                latency_ms=latency,
                effect_boundary=EFFECT_COMPLETED,
            )
        if spec is not None and spec.output_schema:
            violation = schema_violation(output, spec.output_schema)
            if violation is not None:
                ctx._tool_failure = True
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error=ToolOutputValidationError(
                        f"tool {tool_name!r} output violates its "
                        "declared output_schema",
                        details={"schema_path": violation},
                    ),
                    latency_ms=latency,
                    effect_boundary=EFFECT_COMPLETED,
                )
        return ToolResult(
            tool_name=tool_name,
            success=True,
            output=output,
            error=None,
            latency_ms=latency,
            effect_boundary=EFFECT_COMPLETED,
        )


__all__ = ["EffectDispatcher"]
