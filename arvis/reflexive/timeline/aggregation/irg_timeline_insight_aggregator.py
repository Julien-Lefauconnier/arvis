# arvis/reflexive/timeline/aggregation/irg_timeline_insight_aggregator.py

from collections import Counter
from collections.abc import Sequence

from arvis.reflexive.timeline.aggregation.irg_timeline_insight_aggregate import (
    IRGTimelineInsightAggregate,
)
from arvis.reflexive.timeline.insight.irg_timeline_insight import (
    IRGTimelineInsight,
)
from arvis.timeline.timeline_types import TimelineEntryType


class IRGTimelineInsightAggregator:
    """
    Aggregates multiple IRGTimelineInsight objects into a
    higher-level reflexive observation.

    This aggregator:
    - Never mutates input
    - Never infers intent
    - Never grants authority
    """

    @staticmethod
    def aggregate(
        insights: Sequence[IRGTimelineInsight],
    ) -> IRGTimelineInsightAggregate:
        if not insights:
            return IRGTimelineInsightAggregate(
                observed_views=[],
                dominant_entry_types=[],
                confidence=0.0,
                message="No reflexive timeline insights available.",
            )

        view_roles = [insight.view_role for insight in insights]

        entry_type_counter: Counter[TimelineEntryType] = Counter()
        confidences = []

        for insight in insights:
            entry_type_counter.update(insight.dominant_entry_types)
            confidences.append(insight.confidence)

        dominant_types = [
            entry_type for entry_type, _ in entry_type_counter.most_common()
        ]

        average_confidence = sum(confidences) / len(confidences)

        return IRGTimelineInsightAggregate(
            observed_views=view_roles,
            dominant_entry_types=dominant_types,
            confidence=round(average_confidence, 2),
            message=(f"Aggregated insights over {len(view_roles)} timeline views."),
        )
