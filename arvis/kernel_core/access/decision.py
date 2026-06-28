# arvis/kernel_core/access/decision.py

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AccessDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass(slots=True, frozen=True)
class AccessVerdict:
    """Outcome of an authorization evaluation.

    ``reason_code`` is populated on DENY with a canonical access-layer reason
    code (see ``ARVIS_ACCESS_SPEC_V1`` and the ``ReasonCodeRegistry``). It is
    ``None`` on ALLOW.
    """

    decision: AccessDecision
    reason_code: str | None = None

    @property
    def allowed(self) -> bool:
        return self.decision is AccessDecision.ALLOW
