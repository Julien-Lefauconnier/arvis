# arvis/cognition/conflict/conflict_severity.py

from enum import Enum


class ConflictSeverity(str, Enum):
    """
    Declarative severity levels for cognitive conflicts.

    Informational only.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"