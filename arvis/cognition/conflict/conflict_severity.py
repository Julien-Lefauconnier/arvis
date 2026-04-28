# arvis/cognition/conflict/conflict_severity.py

from enum import StrEnum


class ConflictSeverity(StrEnum):
    """
    Declarative severity levels for cognitive conflicts.

    Informational only.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
