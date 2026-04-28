# tests/reflexive/timeline/aggregation/test_irg_timeline_temporal_comparator.py

from datetime import UTC, datetime

from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_comparator import (
    IRGTimelineTemporalComparator,
)
from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_snapshot import (
    IRGTimelineTemporalSnapshot,
)
from arvis.timeline.timeline_types import TimelineEntryType

# --------------------------------------------------
# Helpers
# --------------------------------------------------


def make_snapshot(
    *,
    views=None,
    types=None,
    confidence=1.0,
    ts=None,
):
    return IRGTimelineTemporalSnapshot(
        observed_views=views or [],
        dominant_entry_types=types or [],
        confidence=confidence,
        observed_at=ts or datetime.now(UTC),
    )


# --------------------------------------------------
# No change → stable
# --------------------------------------------------


def test_no_change_is_stable():
    s1 = make_snapshot(
        views=["a"],
        types=[TimelineEntryType.CONFLICT],
        confidence=0.5,
    )
    s2 = make_snapshot(
        views=["a"],
        types=[TimelineEntryType.CONFLICT],
        confidence=0.5,
    )

    diff = IRGTimelineTemporalComparator.compare(s1, s2)

    assert diff.views_added == []
    assert diff.views_removed == []
    assert diff.entry_types_added == []
    assert diff.entry_types_removed == []
    assert diff.is_stable is True


# --------------------------------------------------
# Views diff
# --------------------------------------------------


def test_views_added_and_removed():
    s1 = make_snapshot(views=["a", "b"])
    s2 = make_snapshot(views=["b", "c"])

    diff = IRGTimelineTemporalComparator.compare(s1, s2)

    assert diff.views_added == ["c"]
    assert diff.views_removed == ["a"]
    assert diff.is_stable is False


# --------------------------------------------------
# Entry types diff
# --------------------------------------------------


def test_entry_types_added_and_removed():
    s1 = make_snapshot(types=[TimelineEntryType.CONFLICT])
    s2 = make_snapshot(
        types=[
            TimelineEntryType.CONFLICT,
            TimelineEntryType.REASONING_GAP,
        ]
    )

    diff = IRGTimelineTemporalComparator.compare(s1, s2)

    assert TimelineEntryType.REASONING_GAP in diff.entry_types_added
    assert diff.entry_types_removed == []
    assert diff.is_stable is False


# --------------------------------------------------
# Confidence delta
# --------------------------------------------------


def test_confidence_delta_computation():
    s1 = make_snapshot(confidence=0.5)
    s2 = make_snapshot(confidence=0.65)

    diff = IRGTimelineTemporalComparator.compare(s1, s2)

    assert diff.confidence_delta == 0.15


def test_confidence_rounding():
    s1 = make_snapshot(confidence=0.1234)
    s2 = make_snapshot(confidence=0.1266)

    diff = IRGTimelineTemporalComparator.compare(s1, s2)

    # round(..., 3)
    assert diff.confidence_delta == round(0.1266 - 0.1234, 3)


# --------------------------------------------------
# Stability threshold
# --------------------------------------------------


def test_confidence_within_epsilon_is_stable():
    s1 = make_snapshot(confidence=0.5)
    s2 = make_snapshot(confidence=0.53)

    diff = IRGTimelineTemporalComparator.compare(s1, s2, confidence_epsilon=0.05)

    assert diff.is_stable is True


def test_confidence_outside_epsilon_is_not_stable():
    s1 = make_snapshot(confidence=0.5)
    s2 = make_snapshot(confidence=0.6)

    diff = IRGTimelineTemporalComparator.compare(s1, s2, confidence_epsilon=0.05)

    assert diff.is_stable is False


# --------------------------------------------------
# Combined instability
# --------------------------------------------------


def test_combined_changes_force_instability():
    s1 = make_snapshot(
        views=["a"],
        types=[TimelineEntryType.CONFLICT],
        confidence=0.5,
    )
    s2 = make_snapshot(
        views=["b"],
        types=[TimelineEntryType.REASONING_GAP],
        confidence=0.5,
    )

    diff = IRGTimelineTemporalComparator.compare(s1, s2)

    assert diff.views_added == ["b"]
    assert diff.views_removed == ["a"]
    assert diff.entry_types_added != []
    assert diff.entry_types_removed != []
    assert diff.is_stable is False


# --------------------------------------------------
# Sorting guarantees
# --------------------------------------------------


def test_views_are_sorted():
    s1 = make_snapshot(views=["z"])
    s2 = make_snapshot(views=["a", "z", "m"])

    diff = IRGTimelineTemporalComparator.compare(s1, s2)

    assert diff.views_added == sorted(diff.views_added)


def test_types_sorted_by_value():
    s1 = make_snapshot(types=[])
    s2 = make_snapshot(
        types=[
            TimelineEntryType.CONFLICT,
            TimelineEntryType.REASONING_GAP,
        ]
    )

    diff = IRGTimelineTemporalComparator.compare(s1, s2)

    values = [t.value for t in diff.entry_types_added]
    assert values == sorted(values)


# --------------------------------------------------
# Timestamp formatting
# --------------------------------------------------


def test_timestamps_are_iso_strings():
    s1 = make_snapshot()
    s2 = make_snapshot()

    diff = IRGTimelineTemporalComparator.compare(s1, s2)

    assert isinstance(diff.from_timestamp, str)
    assert isinstance(diff.to_timestamp, str)
    assert "T" in diff.from_timestamp
