# arvis/timeline/insight/irg_timeline_insight_builder.py

from collections import Counter

from arvis.reflexive.timeline.insight.irg_timeline_insight import (
    IRGTimelineInsight,
)
from arvis.timeline.timeline_view import TimelineView


class IRGTimelineInsightBuilder:
    """
    Builds passive reflexive insights from a TimelineView.

    This builder:
    - Does NOT inspect user data
    - Uses only observable structural properties
    """

    @staticmethod
    def build(
        view: TimelineView,
    ) -> IRGTimelineInsight:

        entries = view.entries

        if not entries:
            return IRGTimelineInsight(
                view_role=view.role,
                dominant_entry_types=[],
                confidence=0.1,
                message=(
                    "This timeline view exposes no observable "
                    "timeline events."
                ),
            )

        entry_types = [entry.type for entry in entries]
        counts = Counter(entry_types)

        # ordered by decreasing frequencies
        sorted_types = sorted(
            counts.items(),
            key=lambda x: (-x[1], x[0].value)
        )

        dominant_types = [t for t, _ in sorted_types]
        top_type, top_count = sorted_types[0]
        dominance_ratio = top_count / len(entries)

        return IRGTimelineInsight(
            view_role=view.role,
            dominant_entry_types=dominant_types,
            confidence=min(1.0, 0.3 + dominance_ratio),
            message=(
                f"This timeline is dominated by '{top_type.value}' events "
                f"({top_count}/{len(entries)}), across {len(dominant_types)} categories."
            ),
        )