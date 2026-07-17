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
        require_gates: bool = False,
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
        # With require_gates (production profile), a declared consent
        # without an installed gate is denied (F-017, deny-by-default).
        # Otherwise consent stays the host's concern (documented
        # fail-open for non-production profiles).
        if spec.required_consent is not None:
            if consent_gate is None:
                if require_gates:
                    return ToolAuthorizationDecision(
                        allowed=False,
                        reason="consent_gate_missing",
                    )
            elif not consent_gate.is_granted(invocation, spec.required_consent):
                return ToolAuthorizationDecision(
                    allowed=False,
                    reason="consent_required",
                )

        # --- egress gating (manifest: data_egress) ---
        # Same mechanics as consent (F-018).
        if spec.data_egress:
            if egress_gate is None:
                if require_gates:
                    return ToolAuthorizationDecision(
                        allowed=False,
                        reason="egress_gate_missing",
                    )
            elif not egress_gate.is_allowed(invocation, spec):
                return ToolAuthorizationDecision(
                    allowed=False,
                    reason="egress_denied",
                )

        # --- confirmation ---
        # P1-10-a6: a declared confirmation requirement is satisfiable.
        # The invocation carries a bound confirmation consumed from the
        # registry (exact tool, payload hash, principal, tenant match,
        # single use); anything else stays refused.
        if spec.requires_confirmation and not invocation.confirmed:
            return ToolAuthorizationDecision(
                allowed=False,
                reason="confirmation_required",
                requires_confirmation=True,
            )

        return ToolAuthorizationDecision(
            allowed=True,
            reason="ok",
        )
