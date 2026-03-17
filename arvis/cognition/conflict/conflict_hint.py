# arvis/cognition/conflict/conflict_hint.py

from dataclasses import dataclass
from typing import Optional

from .conflict_type import ConflictType
from .conflict_severity import ConflictSeverity


@dataclass(frozen=True)
class ConflictHint:
    """
    Declarative interpretation of a conflict signal.
    """

    conflict_type: ConflictType
    message: str
    severity: ConflictSeverity
    recommendation: Optional[str] = None