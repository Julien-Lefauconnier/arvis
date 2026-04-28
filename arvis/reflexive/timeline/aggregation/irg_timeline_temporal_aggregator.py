# arvis/reflexive/timeline/aggregation/irg_timeline_temporal_aggregator.py

from datetime import datetime, timezone

from arvis.reflexive.timeline.aggregation.irg_timeline_insight_aggregate import (
    IRGTimelineInsightAggregate,
)
from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_snapshot import (
    IRGTimelineTemporalSnapshot,
)


class IRGTimelineTemporalAggregator:
    """
    Builds temporal snapshots from aggregated IRG timeline insights.

    This class:
    - Does not store history
    - Does not compare snapshots
    - Produces immutable temporal observations
    """

    @staticmethod
    def snapshot(
        aggregate: IRGTimelineInsightAggregate,
        *,
        observed_at: datetime | None = None,
    ) -> IRGTimelineTemporalSnapshot:
        return IRGTimelineTemporalSnapshot(
            observed_at=observed_at or datetime.now(timezone.utc),
            observed_views=aggregate.observed_views,
            dominant_entry_types=aggregate.dominant_entry_types,
            confidence=aggregate.confidence,
        )
