# arvis/adapters/tools/invocation.py

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolInvocation:
    tool_name: str
    payload: dict[str, Any]

    # runtime context (minimal & contrôlé)
    process_id: str
    user_id: str | None = None

    # governance
    # risk_score is the real risk of the turn (hardening composition of
    # the declared input risk and the assessed collapse risk), wired by
    # the tool manager; 0.0 only when no signal is available.
    risk_score: float = 0.0
    audit_required: bool = False

    # F-006-a5: complete invocation context (skeleton). Opaque to
    # arvis; the host assigns meaning (same doctrine as capability
    # grants). principal and tenant are threaded from the trusted
    # context identity channel when a Principal is stamped;
    # consent_granted is reserved for a host composition channel and
    # stays empty until one exists.
    principal: str | None = None
    tenant: str | None = None
    consent_granted: tuple[str, ...] = ()

    # execution semantics
    idempotency_key: str | None = None
    context: Any | None = None
