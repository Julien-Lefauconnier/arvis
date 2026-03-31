# arvis/timeline/insight/irg_timeline_insight_builder.py

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
        unique_types = list(set(entry_types))

        return IRGTimelineInsight(
            view_role=view.role,
            dominant_entry_types=unique_types,
            confidence=0.5,
            message=(
                f"This timeline view exposes "
                f"{len(unique_types)} categories of timeline events."
            ),
        )