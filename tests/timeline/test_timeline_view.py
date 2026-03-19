# tests/timeline/test_timeline_view.py

import pytest

from arvis.timeline.timeline_view import TimelineView

from tests.timeline.helpers import make_entries


def test_view_creation():

    entries = tuple(make_entries(3))

    view = TimelineView(
        role="observer",
        entries=entries,
    )

    assert len(view) == 3
    assert view.entries == entries
    assert view.role == "observer"


def test_view_iteration():

    entries = tuple(make_entries(4))

    view = TimelineView(
        role="observer",
        entries=entries,
    )

    collected = list(view)

    assert collected == list(entries)


def test_view_head():

    entries = tuple(make_entries(5))

    view = TimelineView(
        role="observer",
        entries=entries,
    )

    assert view.head == entries[-1]


def test_view_head_empty():

    view = TimelineView(
        role="observer",
        entries=(),
    )

    assert view.head is None


def test_invalid_role_empty():

    with pytest.raises(ValueError):

        TimelineView(
            role="",
            entries=(),
        )


def test_invalid_role_type():

    with pytest.raises(ValueError):

        TimelineView(
            role=123,  # type: ignore
            entries=(),
        )


def test_entries_not_none():

    with pytest.raises(ValueError):

        TimelineView(
            role="observer",
            entries=None,  # type: ignore
        )


def test_entries_must_be_timeline_entry():

    with pytest.raises(ValueError):

        TimelineView(
            role="observer",
            entries=("not_an_entry",),  # type: ignore
        )


def test_view_immutable():

    entries = tuple(make_entries(2))

    view = TimelineView(
        role="observer",
        entries=entries,
    )

    with pytest.raises(Exception):
        view.role = "admin"


def test_len_consistency():

    entries = tuple(make_entries(6))

    view = TimelineView(
        role="observer",
        entries=entries,
    )

    assert len(view) == len(entries)