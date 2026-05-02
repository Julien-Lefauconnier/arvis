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
    risk_score: float = 0.0
    audit_required: bool = False

    # execution semantics
    idempotency_key: str | None = None
    context: Any | None = None
