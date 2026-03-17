# arvis/action/action_context.py

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionContext:
    """
    Minimal kernel-safe action context.

    Kernel invariants:
    - immutable
    - no backend dependency
    - no place/control coupling
    """

    user_id: str
    responsibility_mode: str = "standard"