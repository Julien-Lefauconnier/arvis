# arvis/reflexive/timeline/aggregation/irg_timeline_temporal_aggregator.py

from datetime import datetime

from arvis.reflexive.timeline.aggregation.irg_timeline_insight_aggregate import (
    IRGTimelineInsightAggregate,
)
from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_snapshot import (
    IRGTimelineTemporalSnapshot,
)
from arvis.types.timestamps import utcnow


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
            observed_at=observed_at or utcnow(),
            observed_views=aggregate.observed_views,
            dominant_entry_types=aggregate.dominant_entry_types,
            confidence=aggregate.confidence,
        )
