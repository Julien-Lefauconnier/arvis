# arvis/tools/executor.py

import time
from typing import Any

from arvis.adapters.tools.invocation import ToolInvocation
from arvis.tools.registry import ToolRegistry
from arvis.tools.tool_result import ToolResult


class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def execute_authorized(
        self,
        result: Any,
        ctx: Any,
    ) -> ToolResult | None:
        """
        Authorized runtime execution only.
        Must be called from syscall layer.
        """

        if result is None or ctx is None:
            return None

        decision = getattr(result, "action_decision", None)
        if decision is None:
            return None

        tool_name_raw = getattr(decision, "tool", None)
        if not isinstance(tool_name_raw, str):
            return None

        tool_name: str = tool_name_raw

        tool_payload = getattr(decision, "tool_payload", {}) or {}

        # --- NEW: canonical invocation ---
        invocation = ToolInvocation(
            tool_name=tool_name,
            payload=tool_payload,
            process_id=getattr(ctx, "_process_id", "unknown"),
            context=ctx,
        )

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
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error="unknown_tool",
                    latency_ms=None,
                )

            if tool.spec is not None:
                ctx._last_tool_spec = tool.spec

            tool.validate(payload_runtime)
            # --- NEW: dual execution support ---
            if hasattr(tool, "execute_invocation"):
                output = tool.execute_invocation(invocation)
            else:
                output = tool.execute(payload_runtime)

            latency = (time.perf_counter() - start) * 1000

            return ToolResult(
                tool_name=tool_name,
                success=True,
                output=output,
                latency_ms=latency,
            )

        except Exception as e:
            ctx._tool_failure = True

            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
                latency_ms=None,
            )

    def execute(self, arg1: Any, arg2: Any | None = None) -> ToolResult | None:
        """
        Backward-compatible entrypoint.
        Direct production execution is forbidden.
        """
        if isinstance(arg1, str):
            raise RuntimeError(
                "direct_tool_execution_forbidden: "
                "use syscall authority via SyscallHandler"
            )

        return self.execute_authorized(arg1, arg2)
