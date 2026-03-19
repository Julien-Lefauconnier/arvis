# arvis/action/action_resolver.py

from __future__ import annotations

from typing import Any

from arvis.action.action_template import ActionTemplate


def resolve_action(decision_result: Any) -> ActionTemplate:
    """
    Resolve an ActionTemplate from a cognitive decision.

    Kernel invariants:
    - deterministic
    - no side effects
    - no external dependency
    - no pipeline coupling
    """

    # Minimal v1 strategy:
    # fallback to generic safe action

    # You can branch later on decision_result.reason, intent, etc.

    return ActionTemplate(
        action_id="default_read",
        description="default safe read action",
        reads_data=True,
        writes_data=False,
        triggers_external=False,
        risk_level="low",
        reversible=True,
    )