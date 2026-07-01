# arvis/conversation/continuation.py

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from arvis.conversation.pending_turn import PendingTurn


@runtime_checkable
class ContinuationResolver(Protocol):
    """Boundary contract for deciding, purely, whether a follow-up turn answers
    a pending continuation.

    A resolver handles exactly one ``kind``. ``try_resolve`` inspects the
    pending turn and the raw follow-up text and returns an opaque reference when
    the turn answers the pending (an identifier the product maps back to an
    action, or a token such as a confirm or cancel marker), or ``None`` when the
    turn does not answer it. A resolver never executes and never performs IO:
    turning a reference into an effect is the product's responsibility.
    """

    @property
    def kind(self) -> str: ...

    def try_resolve(self, pending: PendingTurn, turn_text: str) -> str | None: ...


def resolve_continuation(
    pending: PendingTurn,
    turn_text: str,
    resolvers: Sequence[ContinuationResolver],
) -> str | None:
    """Dispatch a follow-up turn to the resolver whose kind matches the pending.

    Returns the opaque reference chosen by that resolver when the turn answers
    the pending, or ``None`` when no resolver handles the pending's kind or the
    turn does not answer it. A ``None`` result means the pending should be
    abandoned and normal routing should resume. Pure: no IO, no execution.
    """
    for resolver in resolvers:
        if resolver.kind == pending.kind:
            return resolver.try_resolve(pending, turn_text)
    return None
