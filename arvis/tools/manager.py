# arvis/tools/manager.py

from typing import Any

from arvis.adapters.tools.authorization import ToolAuthorizationDecision
from arvis.adapters.tools.invocation import ToolInvocation
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry
from arvis.tools.retry_policy import ToolRetryPolicy
from arvis.tools.tool_result import ToolResult


class ToolManager:
    """
    Unified tool lifecycle orchestrator.

    Responsibilities:
    - build invocation
    - evaluate policy
    - execute tool
    - handle retry
    """

    def __init__(
        self,
        registry: ToolRegistry,
        executor: ToolExecutor,
        retry_policy: ToolRetryPolicy | None = None,
    ) -> None:
        self.registry = registry
        self.executor = executor
        self.retry_policy = retry_policy or ToolRetryPolicy()

    def run(self, result: Any, ctx: Any) -> ToolResult | None:
        if result is None or ctx is None:
            return None

        decision = getattr(result, "action_decision", None)
        if decision is None:
            return None

        tool_name = getattr(decision, "tool", None)
        if not isinstance(tool_name, str):
            return None

        payload = getattr(decision, "tool_payload", {}) or {}

        # -----------------------------------------
        # FORCE EXECUTION OVERRIDE (kernel-level)
        # -----------------------------------------
        force_tool = ctx.extra.get("force_tool")
        force_execution = ctx.extra.get("_force_execution", False)

        bypass_policy = (
            force_execution and force_tool is not None and tool_name == force_tool
        )

        # --- build invocation ---
        invocation = ToolInvocation(
            tool_name=tool_name,
            payload=payload,
            process_id=getattr(ctx, "_process_id", "unknown"),
            context=ctx,
        )

        # --- policy evaluation ---
        if bypass_policy:
            policy = ToolAuthorizationDecision(
                allowed=True,
                reason="forced_execution",
            )
        else:
            policy = ToolPolicyEvaluator.evaluate(invocation, self.registry)

        if not policy.allowed:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=policy.reason,
                latency_ms=None,
            )

        # --- execution ---
        result_exec = self.executor.execute_authorized(result, ctx)

        # --- retry logic ---
        self.retry_policy.evaluate(ctx)

        if ctx.extra.get("execution_policy", {}).get("retry"):
            result_retry = self.executor.execute_authorized(result, ctx)
            return result_retry

        return result_exec
