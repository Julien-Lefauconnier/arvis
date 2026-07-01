# arvis/conversation/pending_turn.py

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PendingTurnStatus(StrEnum):
    """Lifecycle of a pending continuation.

    A pending turn is created ``PENDING``. It is ``CONSUMED`` when the next turn
    answers it, or ``ABANDONED`` when the next turn is unrelated or a newer
    pending replaces it. There is at most one active pending per conversation.
    """

    PENDING = "pending"
    CONSUMED = "consumed"
    ABANDONED = "abandoned"


@dataclass(frozen=True)
class PendingTurn:
    """A deferred conversational continuation: the engine asked something and
    awaits a follow-up of a given ``kind``.

    Kernel invariants:
    - immutable
    - declarative
    - no execution

    ``kind`` and ``payload`` are opaque to arvis. A downstream product names the
    kind (for instance a selection among candidates, or a confirmation) and is
    the only party that interprets the payload. The payload carries references
    only (identifiers, short markers), never heavy content such as message
    bodies, so a pending turn stays bounded and auditable.
    """

    turn_id: str
    conversation_id: str
    user_id: str
    kind: str
    payload: Mapping[str, object]
    created_at: datetime
    status: PendingTurnStatus
