# tests/api/test_timeline_view.py

from arvis.api.os import CognitiveOS
from arvis.api.timeline import TimelineView
from arvis.timeline.timeline_snapshot import TimelineSnapshot
from tests.timeline.helpers import make_entries


def test_timeline_view_from_snapshot():
    entries = tuple(make_entries(3))
    snapshot = TimelineSnapshot.build(entries)

    view = TimelineView.from_snapshot(snapshot)

    assert view.total_entries == 3
    assert view.head == snapshot.head
    assert len(view.entries) == 3


def test_timeline_entry_view_fields():
    entries = tuple(make_entries(1))
    snapshot = TimelineSnapshot.build(entries)

    view = TimelineView.from_snapshot(snapshot)
    entry = view.entries[0]

    assert entry.entry_id is not None
    assert entry.timestamp is not None
    assert entry.title is not None


def test_timeline_view_to_dict():
    entries = tuple(make_entries(2))
    snapshot = TimelineSnapshot.build(entries)

    view = TimelineView.from_snapshot(snapshot)
    data = view.to_dict()

    assert "entries" in data
    assert "head" in data
    assert "total_entries" in data
    assert isinstance(data["entries"], list)


def test_timeline_view_empty():
    snapshot = TimelineSnapshot.build([])

    view = TimelineView.from_snapshot(snapshot)

    assert view.total_entries == 0
    assert view.head is None
    assert view.entries == []


def test_os_returns_timeline_view():
    os = CognitiveOS()

    result = os.run(user_id="u1", cognitive_input="hello")

    assert hasattr(result, "timeline_view")
