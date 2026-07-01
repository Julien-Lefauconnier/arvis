# tests/conversation/test_pending_turn.py

from datetime import UTC, datetime

import pytest

from arvis.conversation.pending_turn import PendingTurn, PendingTurnStatus


def _pending() -> PendingTurn:
    return PendingTurn(
        turn_id="t1",
        conversation_id="c1",
        user_id="u1",
        kind="mail_selection",
        payload={"candidates": ("7", "8")},
        created_at=datetime(2026, 7, 1, tzinfo=UTC),
        status=PendingTurnStatus.PENDING,
    )


def test_status_values() -> None:
    assert PendingTurnStatus.PENDING == "pending"
    assert PendingTurnStatus.CONSUMED == "consumed"
    assert PendingTurnStatus.ABANDONED == "abandoned"


def test_fields_are_carried() -> None:
    pending = _pending()

    assert pending.kind == "mail_selection"
    assert pending.payload["candidates"] == ("7", "8")
    assert pending.status is PendingTurnStatus.PENDING


def test_is_immutable() -> None:
    pending = _pending()

    with pytest.raises(AttributeError):
        pending.status = PendingTurnStatus.CONSUMED  # type: ignore[misc]
