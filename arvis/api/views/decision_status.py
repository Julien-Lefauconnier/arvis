# arvis/api/views/decision_status.py

from __future__ import annotations

from enum import StrEnum
from typing import Any


class DecisionStatus(StrEnum):
    """Public, typed verdict of a governed run (beta contract, a15).

    The three risk bands of the governed gate, plus NONE for views that
    carry no decision (the minimal no-trace view). This enum, together
    with the structured ``decision`` block of
    ``CognitiveResultView.to_dict()``, is the public contract of a
    decision: consumers must never derive a verdict from the repr of an
    internal object (audit a14, A14-BETA-02).
    """

    ALLOWED = "ALLOWED"
    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"
    BLOCKED = "BLOCKED"
    NONE = "NONE"

    @classmethod
    def from_decision(cls, decision: Any) -> DecisionStatus:
        """Derive the public status from a decision object.

        Reads the declarative surface of the kernel decision
        (``allowed``, ``requires_user_validation``); a confirmation
        requirement is neither a clean pass nor a hard block, so it
        surfaces as its own band. An absent decision maps to NONE.
        """
        if decision is None:
            return cls.NONE
        if bool(getattr(decision, "allowed", False)):
            return cls.ALLOWED
        if bool(getattr(decision, "requires_user_validation", False)):
            return cls.REQUIRES_CONFIRMATION
        return cls.BLOCKED
