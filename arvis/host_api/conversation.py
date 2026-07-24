# arvis/host_api/conversation.py

"""The propose-confirm conversational spine.

Pending turns and continuation resolution: how a host carries a
governed proposal across turns until it is confirmed or dropped.

Re-export layer only: every symbol is defined where it lives; this
module pins the import path (see VERSIONING.md, host integration
surface).
"""

from arvis.conversation.continuation import resolve_continuation
from arvis.conversation.pending_turn import (
    PendingTurn,
    PendingTurnStatus,
)

__all__ = [
    "PendingTurn",
    "PendingTurnStatus",
    "resolve_continuation",
]
