# arvis/adapters/tools/policy.py

from arvis.adapters.tools.authorization import ToolAuthorizationDecision
from arvis.adapters.tools.invocation import ToolInvocation
from arvis.tools.registry import ToolRegistry


class ToolPolicyEvaluator:
    @staticmethod
    def evaluate(
        invocation: ToolInvocation,
        registry: ToolRegistry,
    ) -> ToolAuthorizationDecision:
        tool = registry.get(invocation.tool_name)

        if tool is None:
            return ToolAuthorizationDecision(
                allowed=False,
                reason="unknown_tool",
            )

        spec = tool.spec

        if spec is None:
            return ToolAuthorizationDecision(
                allowed=False,
                reason="missing_spec",
            )

        # --- risk gating ---
        if invocation.risk_score > spec.max_risk:
            return ToolAuthorizationDecision(
                allowed=False,
                reason="risk_exceeded",
            )

        # --- confirmation ---
        if spec.requires_confirmation:
            return ToolAuthorizationDecision(
                allowed=False,
                reason="confirmation_required",
                requires_confirmation=True,
            )

        return ToolAuthorizationDecision(
            allowed=True,
            reason="ok",
        )
