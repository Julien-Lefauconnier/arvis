# arvis/reflexive/timeline/aggregation/irg_timeline_insight_aggregate.py

from dataclasses import dataclass
from typing import Sequence

from arvis.timeline.timeline_types import TimelineEntryType


@dataclass(frozen=True)
class IRGTimelineInsightAggregate:
    """
    Aggregated reflexive insight over multiple timeline views.

    Characteristics:
    - Read-only
    - Declarative
    - Non-prescriptive
    - ZKCS compliant

    This object represents a *synthetic observation*,
    not a decision or recommendation.
    """

    observed_views: Sequence[str]
    dominant_entry_types: Sequence[TimelineEntryType]
    confidence: float
    message: str
