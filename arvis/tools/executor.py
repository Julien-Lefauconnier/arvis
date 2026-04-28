# arvis/tools/executor.py

from typing import Any

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

        payload_runtime: dict[str, Any] = {
            "decision": decision,
            "context": ctx,
            "tool_payload": getattr(decision, "tool_payload", {}) or {},
        }

        try:
            tool = self.registry.get(tool_name)
            if tool is None:
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    error="unknown_tool",
                )

            tool.validate(payload_runtime)
            output = tool.execute(payload_runtime)

            return ToolResult(
                tool_name=tool_name,
                success=True,
                output=output,
                latency_ms=None,
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
