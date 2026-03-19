# arvis/cognition/conflict/conflict_type.py

from dataclasses import dataclass


@dataclass(frozen=True)
class ConflictType:
    """
    Kernel-level conflict identifier.

    Must be:
    - stable
    - unique
    - domain-agnostic
    """

    name: str

REASON_MISMATCH = ConflictType("reason_mismatch")