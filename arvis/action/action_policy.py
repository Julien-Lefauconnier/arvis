# arvis/action/action_policy.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.action.action_decision import ActionDecision
from arvis.action.action_mode import ActionMode
from arvis.math.signals import RiskSignal


@dataclass(frozen=True)
class ActionPolicy:
    """
    Global policy layer (system-level constraints)

    ZKCS-safe:
    - deterministic
    - no external calls
    """

    max_risk_threshold: float = 0.85
    require_audit_above: float = 0.6

    def apply(
        self,
        decision: ActionDecision,
        risk: RiskSignal,
    ) -> ActionDecision:

        # --------------------------------------------------
        # 1. Hard block (system safety)
        # --------------------------------------------------
        if float(risk) >= self.max_risk_threshold:
            return ActionDecision(
                allowed=False,
                requires_user_validation=False,
                denied_reason="policy_risk_threshold",
                audit_required=True,
                tool=decision.tool,
                tool_payload=decision.tool_payload,
                action_mode=ActionMode.BLOCKED,
            )

        # --------------------------------------------------
        # 2. Force audit
        # --------------------------------------------------
        if float(risk) >= self.require_audit_above:
            return ActionDecision(
                allowed=decision.allowed,
                requires_user_validation=decision.requires_user_validation,
                denied_reason=decision.denied_reason,
                audit_required=True,
                tool=decision.tool,
                tool_payload=decision.tool_payload,
                action_mode=decision.action_mode,
            )

        # --------------------------------------------------
        # 3. passthrough
        # --------------------------------------------------
        return decision