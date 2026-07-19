# arvis/adapters/tools/authorization_snapshot.py
"""Full authorization snapshot bound into the effect commitment (D-4).

The a7 intent bound the effect parameters, but not the full
authorization context that permitted them. Two identical effects
authorized under different confirmations, or at different risk, or by
different principals, produced the same engagement material once the
parameters matched. The audit (constat 11) asked for a snapshot binding
the whole authorization decision.

``ToolAuthorizationSnapshot`` is that material: the policy verdict and
its reason, the bound confirmation commitment (the canonical payload
hash of the consumed confirmation, or None), the principal, the tenant
and the real turn risk. It is JSON-safe and canonicalized injectively
by the campaign-5 encoder when it enters the intent, so any difference
in the authorization that permitted an effect yields a different
commitment.

It carries no payload content: the confirmation is represented by its
commitment hash, never its body (ZK).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolAuthorizationSnapshot:
    """Engagement material for a tool authorization decision."""

    tool_name: str
    allowed: bool
    reason: str
    principal: str | None
    tenant: str | None
    risk_score: float
    confirmed: bool
    confirmation_commitment: str | None
    authentication_source: str | None = None
    authentication_strength: str | None = None
    service_id: str | None = None
    session_id_hash: str | None = None

    def to_material(self) -> dict[str, Any]:
        """Deterministic, JSON-safe binding material for the commitment.

        Every field that made the authorization what it was, and nothing
        derived from payload content. Fed to the injective canonical
        encoder, so two authorizations differing in any of these fields
        commit differently.
        """
        material = {
            "authorization_version": 1,
            "tool_name": self.tool_name,
            "allowed": self.allowed,
            "reason": self.reason,
            "principal": self.principal,
            "tenant": self.tenant,
            # Risk is quantized to avoid float noise across runs while
            # still binding materially different risk levels.
            "risk_bucket": round(float(self.risk_score), 4),
            "confirmed": self.confirmed,
            "confirmation_commitment": self.confirmation_commitment,
        }
        if self.authentication_source is not None:
            material["authorization_version"] = 2
            material["authentication"] = {
                "source": self.authentication_source,
                "strength": self.authentication_strength,
                "service_id": self.service_id,
                "session_id_hash": self.session_id_hash,
            }
        return material


__all__ = ["ToolAuthorizationSnapshot"]
