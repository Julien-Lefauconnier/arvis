# arvis/cognition/conflict/conflict_hint.py

from dataclasses import dataclass

from .conflict_severity import ConflictSeverity
from .conflict_type import ConflictType


@dataclass(frozen=True)
class ConflictHint:
    """
    Declarative interpretation of a conflict signal.
    """

    conflict_type: ConflictType
    message: str
    severity: ConflictSeverity
    recommendation: str | None = None
