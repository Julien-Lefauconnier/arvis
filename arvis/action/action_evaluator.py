# arvis/action/action_evaluator.py

from __future__ import annotations

from typing import Any

from arvis.math.signals import RiskSignal

from .action_template import ActionTemplate
from .action_decision import ActionDecision
from .action_mapper import map_verdict_to_action
from arvis.action.action_context import ActionContext


def evaluate_action(
    verdict: Any,
    template: ActionTemplate,
    risk: RiskSignal,
    context: ActionContext | None = None,
) -> ActionDecision:
    """
    Context-aware action evaluation.

    Combines:
    - cognitive verdict
    - action capabilities
    - system risk

    Kernel invariants:
    - deterministic
    - no side effects
    - no external dependencies
    """

    base_decision = map_verdict_to_action(verdict)

    # --------------------------------------------------
    # Risk overrides
    # --------------------------------------------------

    # High risk + destructive action → block
    if float(risk) > 0.7 and template.writes_data:
        return ActionDecision(
            allowed=False,
            requires_user_validation=False,
            denied_reason="high_risk_write_block",
            audit_required=True,
            action_mode=base_decision.action_mode,
        )

    # External trigger + medium risk → require validation
    if float(risk) > 0.4 and template.triggers_external:
        return ActionDecision(
            allowed=True,
            requires_user_validation=True,
            denied_reason=None,
            audit_required=True,
            action_mode=base_decision.action_mode,
        )

    # Irreversible + any risk → require validation
    if not template.reversible and float(risk) > 0.2:
        return ActionDecision(
            allowed=True,
            requires_user_validation=True,
            denied_reason=None,
            audit_required=True,
            action_mode=base_decision.action_mode,
        )
    
    # --------------------------------------------------
    # Context overrides (user responsibility)
    # --------------------------------------------------

    if context is not None:

        # Strict mode → force validation
        if context.responsibility_mode == "strict":
            return ActionDecision(
                allowed=base_decision.allowed,
                requires_user_validation=True,
                denied_reason=base_decision.denied_reason,
                audit_required=True,
                action_mode=base_decision.action_mode,
            )

        # Autonomous mode → reduce friction (safe only)
        if context.responsibility_mode == "autonomous":
            if base_decision.allowed and float(risk) < 0.3:
                return ActionDecision(
                    allowed=True,
                    requires_user_validation=False,
                    denied_reason=None,
                    audit_required=False,
                    action_mode=base_decision.action_mode,
                )

    return base_decision