# arvis/tools/executor.py

import time
from typing import Any

import jsonschema

from arvis.errors import normalize_error
from arvis.errors.tool_runtime import (
    ToolAuthorizationError,
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
from arvis.tools.tool_result import ToolResult


def _schema_violation(instance: Any, schema: dict[str, Any]) -> str | None:
    """Validate an instance against a declared JSON schema (F-020).

    Returns a structural path on violation and None when valid. ZK: the
    description carries schema paths only, never the offending values.
    A malformed declared schema cannot validate anything, so it counts
    as a violation on the tool side (fail-closed).
    """
    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.ValidationError as exc:
        path = "/".join(str(part) for part in exc.absolute_path)
        return path or "<root>"
    except jsonschema.SchemaError:
        return "<invalid_schema>"
    return None


class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        # D-7: the single minting authority for this executor. The
        # manager reads it to mint capabilities after policy; the
        # executor honours only the capabilities this authority minted.
        self.authority = InvocationAuthority()

    def execute_invocation(
        self,
        authorized: AuthorizedInvocation,
        result: Any,
        ctx: Any,
    ) -> ToolResult | None:
        """Execute a tool from a verified authorization capability (D-7).

        The executor runs a tool ONLY when handed an
        :class:`AuthorizedInvocation` this executor's authority minted.
        A bare invocation, a forged capability or one from a different
        authority raises :class:`UnauthorizedExecutionError` and the
        effect never runs: there is no path to an effect that the
        manager's policy did not authorize.

        The wrapped ``ToolInvocation`` is the exact object the policy
        evaluated, without reconstruction, so identity, tenant, real
        risk, consent and idempotency are never lost between
        authorization and execution.
        """
        if not isinstance(
            authorized, AuthorizedInvocation
        ) or not self.authority.verifies(authorized):
            raise UnauthorizedExecutionError(
                "tool execution requires a verified AuthorizedInvocation "
                "minted by the tool manager's policy"
            )
        invocation = authorized.invocation

        if result is None or ctx is None:
            return None

        decision = getattr(result, "action_decision", None)
        if decision is None:
            return None

        tool_name: str = invocation.tool_name
        tool_payload = invocation.payload or {}

        # legacy payload (kept for compatibility)
        payload_runtime: dict[str, Any] = {
            "decision": decision,
            "context": ctx,
            "tool_payload": tool_payload,
            "invocation": invocation,  # 👈 NEW BRIDGE
        }

        try:
            start = time.perf_counter()

            tool = self.registry.get(tool_name)

            if tool is None:
                ctx._tool_failure = True
                unknown_error = UnknownToolError(f"Unknown tool: {tool_name}")
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error=unknown_error,
                    latency_ms=None,
                )

            spec = tool.spec
            if spec is not None:
                ctx._last_tool_spec = spec

            # F-020: the declared input schema is validated before the
            # call; a violating payload never reaches the tool.
            if spec is not None and spec.input_schema:
                violation = _schema_violation(tool_payload, spec.input_schema)
                if violation is not None:
                    ctx._tool_failure = True
                    return ToolResult(
                        tool_name=tool_name,
                        success=False,
                        error=ToolInputValidationError(
                            f"tool {tool_name!r} input violates its "
                            "declared input_schema",
                            details={"schema_path": violation},
                        ),
                        latency_ms=None,
                    )

            tool.validate(payload_runtime)
            # --- NEW: dual execution support ---
            if hasattr(tool, "execute_invocation"):
                output = tool.execute_invocation(invocation)
            else:
                output = tool.execute(payload_runtime)

            latency = (time.perf_counter() - start) * 1000

            # F-014: deadline semantics. The tool ran to completion but
            # past its declared budget; the late result is rejected
            # instead of being used, and the violation is surfaced. The
            # effect may still have happened: this is a deadline on
            # result acceptance, not an interruption (process isolation
            # is a later chantier).
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
                )

            # F-020: the declared output schema is validated after the
            # call; an invalid response gets its specific failure status
            # instead of flowing downstream as a success.
            if spec is not None and spec.output_schema:
                violation = _schema_violation(output, spec.output_schema)
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
                    )

            return ToolResult(
                tool_name=tool_name,
                success=True,
                output=output,
                error=None,
                latency_ms=latency,
            )

        except Exception as e:
            ctx._tool_failure = True
            normalized_error = normalize_error(e)
            error = ToolExecutionError(
                normalized_error.message,
                cause=normalized_error.cause,
                details={
                    "exception_type": type(e).__name__,
                },
            )

            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=error,
                latency_ms=None,
            )

    def execute(self, arg1: Any, arg2: Any | None = None) -> ToolResult | None:
        """Direct execution is forbidden (D-7).

        There is no unauthorized path to an effect. A tool runs only
        through :meth:`execute_invocation` handed a capability the tool
        manager minted after its policy authorized the invocation. Every
        direct form raises, so neither a tool name nor a rebuilt
        result/ctx can drive an effect that policy never evaluated.
        """
        raise ToolAuthorizationError(
            "direct_tool_execution_forbidden: a tool runs only from an "
            "AuthorizedInvocation minted by the tool manager's policy"
        )
