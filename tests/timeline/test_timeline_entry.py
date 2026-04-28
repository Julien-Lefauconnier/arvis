# tests/timeline/test_timeline_entry.py

from datetime import datetime, timezone, timedelta
import pytest

from arvis.timeline.timeline_entry import TimelineEntry, TimelineEntryNature
from arvis.timeline.timeline_types import TimelineEntryType


def make_entry(**kwargs):
    base = dict(
        entry_id="entry12345",
        created_at=datetime.now(timezone.utc),
        type=TimelineEntryType.SYSTEM_NOTICE,
        title="Test entry",
        description="test description",
        action_id=None,
        place_id=None,
        origin_ref=None,
        nature=TimelineEntryNature.EVENT,
        device_id="0" * 64,
        lamport=0,
    )
    base.update(kwargs)
    return TimelineEntry(**base)


# ---------------------------------------------------------
# basic construction
# ---------------------------------------------------------


def test_timeline_entry_creation():
    e = make_entry()

    assert e.entry_id == "entry12345"
    assert e.timestamp == e.created_at
    assert e.lamport == 0


# ---------------------------------------------------------
# label behavior
# ---------------------------------------------------------


def test_label_uses_description():
    e = make_entry(description="hello")

    assert e.label == "hello"


def test_label_fallback_to_title():
    e = make_entry(description=None)

    assert e.label == "Test entry"


# ---------------------------------------------------------
# timestamp invariants
# ---------------------------------------------------------


def test_created_at_must_be_timezone_aware():
    with pytest.raises(ValueError):
        make_entry(created_at=datetime.now())


def test_created_at_must_be_utc():
    non_utc = datetime(2024, 1, 1, tzinfo=timezone(timedelta(hours=2)))

    with pytest.raises(ValueError):
        make_entry(created_at=non_utc)


# ---------------------------------------------------------
# entry_id validation
# ---------------------------------------------------------


def test_entry_id_ascii_only():
    with pytest.raises(ValueError):
        make_entry(entry_id="éééééééé")


def test_entry_id_length_limits():
    with pytest.raises(ValueError):
        make_entry(entry_id="short")

    with pytest.raises(ValueError):
        make_entry(entry_id="a" * 300)


def test_entry_id_control_chars():
    with pytest.raises(ValueError):
        make_entry(entry_id="entry\x01bad")


# ---------------------------------------------------------
# device id validation
# ---------------------------------------------------------


def test_device_id_length():
    with pytest.raises(ValueError):
        make_entry(device_id="abc")


def test_device_id_hex():
    with pytest.raises(ValueError):
        make_entry(device_id="z" * 64)


# ---------------------------------------------------------
# lamport validation
# ---------------------------------------------------------


def test_lamport_negative():
    with pytest.raises(ValueError):
        make_entry(lamport=-1)


def test_lamport_type():
    with pytest.raises(ValueError):
        make_entry(lamport="notint")


# ---------------------------------------------------------
# unsafe constructor
# ---------------------------------------------------------


def test_unsafe_constructor():
    e = TimelineEntry.unsafe(
        entry_id="entry12345",
        type=TimelineEntryType.SYSTEM_NOTICE,
        title="Unsafe",
        description=None,
        action_id=None,
    )

    assert e.entry_id == "entry12345"
    assert e.created_at.tzinfo == timezone.utc
