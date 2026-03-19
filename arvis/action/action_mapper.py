# arvis/action/action_mapper.py

from __future__ import annotations

from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict

from .action_decision import ActionDecision
from .action_mode import ActionMode


def map_verdict_to_action(verdict: LyapunovVerdict) -> ActionDecision:
    """
    Pure mapping from cognitive verdict → action decision.

    Kernel invariants:
    - no side effects
    - deterministic
    - no external dependency
    - no pipeline coupling
    """

    if verdict == LyapunovVerdict.ABSTAIN:
        return ActionDecision(
            allowed=False,
            requires_user_validation=False,
            denied_reason="stability_guard",
            audit_required=True,
            action_mode=ActionMode.MANUAL,
        )

    if verdict == LyapunovVerdict.REQUIRE_CONFIRMATION:
        return ActionDecision(
            allowed=True,
            requires_user_validation=True,
            denied_reason=None,
            audit_required=True,
            action_mode=ActionMode.ASSISTED,
        )

    # ALLOW
    return ActionDecision(
        allowed=True,
        requires_user_validation=False,
        denied_reason=None,
        audit_required=False,
        action_mode=ActionMode.AUTOMATIC,
    )