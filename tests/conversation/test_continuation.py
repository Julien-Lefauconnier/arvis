# tests/conversation/test_continuation.py

from datetime import UTC, datetime

from arvis.conversation.continuation import (
    ContinuationResolver,
    resolve_continuation,
)
from arvis.conversation.pending_turn import PendingTurn, PendingTurnStatus


def _pending(kind: str) -> PendingTurn:
    return PendingTurn(
        turn_id="t1",
        conversation_id="c1",
        user_id="u1",
        kind=kind,
        payload={},
        created_at=datetime(2026, 7, 1, tzinfo=UTC),
        status=PendingTurnStatus.PENDING,
    )


class _EchoResolver:
    """Test resolver: answers its kind by echoing a fixed reference unless the
    turn text is the sentinel 'non'."""

    def __init__(self, kind: str, reference: str) -> None:
        self._kind = kind
        self._reference = reference

    @property
    def kind(self) -> str:
        return self._kind

    def try_resolve(self, pending: PendingTurn, turn_text: str) -> str | None:
        if turn_text.strip().lower() == "non":
            return None
        return self._reference


def test_resolver_satisfies_protocol() -> None:
    resolver = _EchoResolver("mail_selection", "7")

    assert isinstance(resolver, ContinuationResolver)


def test_dispatch_matches_kind() -> None:
    resolvers = [
        _EchoResolver("action_confirmation", "confirm"),
        _EchoResolver("mail_selection", "7"),
    ]

    assert (
        resolve_continuation(_pending("mail_selection"), "le premier", resolvers) == "7"
    )


def test_no_resolver_for_kind_returns_none() -> None:
    resolvers = [_EchoResolver("action_confirmation", "confirm")]

    assert (
        resolve_continuation(_pending("mail_selection"), "le premier", resolvers)
        is None
    )


def test_resolver_declining_returns_none() -> None:
    resolvers = [_EchoResolver("mail_selection", "7")]

    assert resolve_continuation(_pending("mail_selection"), "non", resolvers) is None


def test_empty_resolvers_returns_none() -> None:
    assert resolve_continuation(_pending("mail_selection"), "le premier", []) is None
