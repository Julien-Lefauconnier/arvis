# arvis/tools/executor.py

import time
from typing import Any

import jsonschema

from arvis.adapters.tools.invocation import ToolInvocation
from arvis.errors import normalize_error
from arvis.errors.tool_runtime import (
    ToolAuthorizationError,
    ToolExecutionError,
    ToolInputValidationError,
    ToolOutputValidationError,
    ToolTimeoutError,
    UnknownToolError,
)
from arvis.tools.registry import ToolRegistry
from arvis.tools.runtime.runtime_bindings import resolve_process_id
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

    def execute_authorized(
        self,
        result: Any,
        ctx: Any,
    ) -> ToolResult | None:
        """Compatibility entrypoint (deprecated, P1-5-a6).

        Rebuilds a MINIMAL invocation and delegates. The authorized
        path must use :meth:`execute_invocation` with the invocation
        object the policy actually evaluated, so identity, tenant, real
        risk, consent and idempotency are never lost between
        authorization and execution.
        """

        if result is None or ctx is None:
            return None

        decision = getattr(result, "action_decision", None)
        if decision is None:
            return None

        tool_name_raw = getattr(decision, "tool", None)
        if not isinstance(tool_name_raw, str):
            return None

        invocation = ToolInvocation(
            tool_name=tool_name_raw,
            payload=getattr(decision, "tool_payload", {}) or {},
            process_id=resolve_process_id(ctx),
            context=ctx,
        )
        return self.execute_invocation(invocation, result, ctx)

    def execute_invocation(
        self,
        invocation: ToolInvocation,
        result: Any,
        ctx: Any,
    ) -> ToolResult | None:
        """Authorized runtime execution of an already-evaluated invocation.

        P1-5-a6: the executor receives the SAME `ToolInvocation` the
        policy authorized, without reconstruction. The context the tool
        sees is the context that was authorized: user, principal,
        tenant, real turn risk, consent, audit and idempotency fields
        all travel to the tool. Must be called from the syscall layer.
        """

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
        """
        Backward-compatible entrypoint.
        Direct production execution is forbidden.
        """
        if isinstance(arg1, str):
            raise ToolAuthorizationError(
                "direct_tool_execution_forbidden: "
                "use syscall authority via SyscallHandler"
            )

        return self.execute_authorized(arg1, arg2)
