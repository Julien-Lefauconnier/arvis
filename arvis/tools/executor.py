# arvis/tools/executor.py

import time
from typing import Any, Dict, Optional, Union

from arvis.tools.registry import ToolRegistry
from arvis.tools.tool_result import ToolResult


class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def execute(
        self,
        arg1: Union[str, Any],
        arg2: Optional[Any] = None,
    ) -> Optional[Any]:
        """
        Dual mode:
        - execute(tool_name, payload)
        - execute(result, ctx)
        """

        # -------------------------
        # MODE 1 — direct call
        # -------------------------
        if isinstance(arg1, str):
            tool_name_direct = arg1

            if isinstance(arg2, dict):
                payload_direct: Dict[str, Any] = arg2
            else:
                payload_direct = {}

            tool = self.registry.get(tool_name_direct)
            tool.validate(payload_direct)
            return tool.execute(payload_direct)

        # -------------------------
        # MODE 2 — runtime
        # -------------------------
        result = arg1
        ctx = arg2

        if result is None or ctx is None:
            return None

        decision = getattr(result, "action_decision", None)
        if decision is None:
            return None

        tool_name_raw = getattr(decision, "tool", None)
        if not isinstance(tool_name_raw, str):
            return None

        tool_name: str = tool_name_raw

        payload_runtime: Dict[str, Any] = {
            "decision": decision,
            "context": ctx,
            "tool_payload": getattr(decision, "tool_payload", {}) or {},
        }

        try:
            tool = self.registry.get(tool_name)
            start = time.time()

            tool.validate(payload_runtime)
            output = tool.execute(payload_runtime)

            latency = (time.time() - start) * 1000

            tool_result = ToolResult(
                tool_name=tool_name,
                success=True,
                output=output,
                latency_ms=latency if hasattr(ToolResult, "latency_ms") else None,
            )

            ctx.extra.setdefault("tool_results", []).append(tool_result)
            ctx.extra["last_tool_result"] = tool_result
            ctx.extra.setdefault("tool_payloads", []).append({
                "tool": tool_name,
                "payload": payload_runtime.get("tool_payload", {}),
            })

            return tool_result

        except Exception as e:
            tool_result = ToolResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
                latency_ms=None,
            )

            ctx.extra.setdefault("tool_results", []).append(tool_result)
            ctx.extra["last_tool_result"] = tool_result
            ctx.extra.setdefault("tool_payloads", []).append({
                "tool": tool_name,
                "payload": payload_runtime.get("tool_payload", {}),
            })

            setattr(ctx, "_tool_failure", True)

            return tool_result