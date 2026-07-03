# arvis/adapters/tools/policy.py

from arvis.adapters.tools.authorization import ToolAuthorizationDecision
from arvis.adapters.tools.gates import ConsentGate, EgressGate
from arvis.adapters.tools.invocation import ToolInvocation
from arvis.tools.registry import ToolRegistry


class ToolPolicyEvaluator:
    @staticmethod
    def evaluate(
        invocation: ToolInvocation,
        registry: ToolRegistry,
        *,
        consent_gate: ConsentGate | None = None,
        egress_gate: EgressGate | None = None,
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

        # --- consent gating (manifest: required_consent) ---
        # Enforced only when the tool declares a consent and the host supplies a
        # gate; otherwise consent is the host's concern elsewhere (no gate here).
        if spec.required_consent is not None and consent_gate is not None:
            if not consent_gate.is_granted(invocation, spec.required_consent):
                return ToolAuthorizationDecision(
                    allowed=False,
                    reason="consent_required",
                )

        # --- egress gating (manifest: data_egress) ---
        if spec.data_egress and egress_gate is not None:
            if not egress_gate.is_allowed(invocation, spec):
                return ToolAuthorizationDecision(
                    allowed=False,
                    reason="egress_denied",
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
