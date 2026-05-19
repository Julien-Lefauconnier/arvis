# arvis/tools/manager.py

from typing import Any

from arvis.adapters.tools.authorization import ToolAuthorizationDecision
from arvis.adapters.tools.invocation import ToolInvocation
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.errors.tool_runtime import ToolAuthorizationError
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry
from arvis.tools.runtime.runtime_bindings import resolve_process_id
from arvis.tools.tool_result import ToolResult


class ToolManager:
    """
    Unified tool lifecycle orchestrator.

    Responsibilities:
    - build invocation
    - evaluate policy
    - execute tool
    - execute a single authorized tool invocation

    Retry orchestration is owned by CognitiveRuntime and must pass
    through SyscallHandler for audit/replay consistency.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        executor: ToolExecutor,
    ) -> None:
        self.registry = registry
        self.executor = executor

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
        runtime_policy = getattr(ctx, "runtime_policy", None)

        force_tool = runtime_policy.force_tool if runtime_policy is not None else None

        force_execution = (
            runtime_policy.force_execution if runtime_policy is not None else False
        )

        bypass_policy = (
            force_execution and force_tool is not None and tool_name == force_tool
        )

        # --- build invocation ---
        invocation = ToolInvocation(
            tool_name=tool_name,
            payload=payload,
            process_id=resolve_process_id(ctx),
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
            error = ToolAuthorizationError(policy.reason or "tool_policy_denied")
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=error,
                latency_ms=None,
            )

        # --- execution ---
        result_exec = self.executor.execute_authorized(result, ctx)

        return result_exec
