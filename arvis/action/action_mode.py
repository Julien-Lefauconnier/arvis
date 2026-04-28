# arvis/action/action_mode.py

from enum import Enum


class ActionMode(str, Enum):
    """
    Describes how an action is initiated and validated.

    Kernel invariant:
    - declarative only
    """

    MANUAL = "manual"
    ASSISTED = "assisted"
    AUTOMATIC = "automatic"
    BLOCKED = "blocked"
