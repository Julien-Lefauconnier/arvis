# arvis/action/action_mode.py

from enum import StrEnum


class ActionMode(StrEnum):
    """
    Describes how an action is initiated and validated.

    Kernel invariant:
    - declarative only
    """

    MANUAL = "manual"
    ASSISTED = "assisted"
    AUTOMATIC = "automatic"
    BLOCKED = "blocked"
