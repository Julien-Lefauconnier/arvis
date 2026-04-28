# tests/timeline/test_timeline_cursor_full.py

import pytest
from datetime import datetime, timezone, timedelta

from arvis.timeline.timeline_cursor import TimelineCursor


# ============================================================
# Helpers
# ============================================================

VALID_HASH = "a" * 64


def utc_now():
    return datetime.now(timezone.utc)


# ============================================================
# __post_init__ validations
# ============================================================


def test_timestamp_none():
    with pytest.raises(ValueError):
        TimelineCursor(timestamp=None)


def test_timestamp_naive():
    with pytest.raises(ValueError):
        TimelineCursor(timestamp=datetime.now())


def test_timestamp_not_utc():
    tz = timezone(timedelta(hours=1))
    with pytest.raises(ValueError):
        TimelineCursor(timestamp=datetime.now(tz))


def test_negative_total_entries():
    with pytest.raises(ValueError):
        TimelineCursor(timestamp=utc_now(), total_entries=-1)


def test_empty_cursor_with_entries():
    with pytest.raises(ValueError):
        TimelineCursor(timestamp=utc_now(), head=None, total_entries=1)


def test_head_invalid_length():
    with pytest.raises(ValueError):
        TimelineCursor(timestamp=utc_now(), head="abc", total_entries=1)


def test_head_invalid_hex():
    bad = "g" * 64  # not hex
    with pytest.raises(ValueError):
        TimelineCursor(timestamp=utc_now(), head=bad, total_entries=1)


def test_valid_empty_cursor():
    c = TimelineCursor(timestamp=utc_now())
    assert c.head is None
    assert c.total_entries == 0


def test_valid_full_cursor():
    c = TimelineCursor(
        timestamp=utc_now(),
        head=VALID_HASH,
        total_entries=10,
    )
    assert c.head == VALID_HASH


# ============================================================
# Equality / hash
# ============================================================


def test_cursor_equality():
    ts = utc_now()

    c1 = TimelineCursor(ts, VALID_HASH, 10)
    c2 = TimelineCursor(ts, VALID_HASH, 10)

    assert c1 == c2
    assert hash(c1) == hash(c2)


def test_cursor_inequality():
    ts = utc_now()

    c1 = TimelineCursor(ts, VALID_HASH, 10)
    c2 = TimelineCursor(ts, VALID_HASH, 11)

    assert c1 != c2


def test_cursor_not_equal_other_type():
    c = TimelineCursor(timestamp=utc_now())
    assert c != "not a cursor"


# ============================================================
# Serialization
# ============================================================


def test_to_dict_empty():
    c = TimelineCursor(timestamp=utc_now())

    d = c.to_dict()

    assert "timestamp" in d
    assert "head" not in d


def test_to_dict_full():
    c = TimelineCursor(timestamp=utc_now(), head=VALID_HASH, total_entries=5)

    d = c.to_dict()

    assert d["head"] == VALID_HASH
    assert d["total_entries"] == 5


def test_from_dict_valid():
    ts = utc_now()

    payload = {
        "timestamp": ts.isoformat(),
        "head": VALID_HASH,
        "total_entries": 3,
    }

    c = TimelineCursor.from_dict(payload)

    assert c.head == VALID_HASH
    assert c.total_entries == 3


def test_from_dict_non_utc_fails():
    ts = datetime.now()  # naive

    payload = {"timestamp": ts.isoformat()}

    with pytest.raises(ValueError):
        TimelineCursor.from_dict(payload)


# ============================================================
# now()
# ============================================================


def test_now_cursor():
    c = TimelineCursor.now()

    assert c.timestamp.tzinfo is not None
    assert c.timestamp.tzinfo.utcoffset(c.timestamp) == timedelta(0)
    assert c.head is None
