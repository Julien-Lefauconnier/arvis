# arvis/reflexive/timeline/aggregation/irg_timeline_temporal_comparator.py

from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_snapshot import (
    IRGTimelineTemporalSnapshot,
)
from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_diff import (
    IRGTimelineTemporalDiff,
)


class IRGTimelineTemporalComparator:
    """
    Compares two IRG timeline temporal snapshots.

    Produces a declarative diff with no semantic escalation.
    """

    @staticmethod
    def compare(
        previous: IRGTimelineTemporalSnapshot,
        current: IRGTimelineTemporalSnapshot,
        *,
        confidence_epsilon: float = 0.05,
    ) -> IRGTimelineTemporalDiff:
        prev_views = set(previous.observed_views)
        curr_views = set(current.observed_views)

        prev_types = set(previous.dominant_entry_types)
        curr_types = set(current.dominant_entry_types)

        views_added = sorted(curr_views - prev_views)
        views_removed = sorted(prev_views - curr_views)

        types_added = sorted(curr_types - prev_types, key=lambda t: t.value)
        types_removed = sorted(prev_types - curr_types, key=lambda t: t.value)

        confidence_delta = round(
            current.confidence - previous.confidence,
            3,
        )

        is_stable = (
            not views_added
            and not views_removed
            and not types_added
            and not types_removed
            and abs(confidence_delta) <= confidence_epsilon
        )

        return IRGTimelineTemporalDiff(
            from_timestamp=previous.observed_at.isoformat(),
            to_timestamp=current.observed_at.isoformat(),
            views_added=views_added,
            views_removed=views_removed,
            entry_types_added=types_added,
            entry_types_removed=types_removed,
            confidence_delta=confidence_delta,
            is_stable=is_stable,
        )
