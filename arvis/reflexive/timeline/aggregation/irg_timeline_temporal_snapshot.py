# arvis/reflexive/timeline/aggregation/irg_timeline_temporal_snapshot.py

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from arvis.timeline.timeline_types import TimelineEntryType


@dataclass(frozen=True)
class IRGTimelineTemporalSnapshot:
    """
    Temporal snapshot of aggregated reflexive timeline insights.

    - Read-only
    - Declarative
    - Time-bound
    - ZKCS compliant
    """

    observed_at: datetime
    observed_views: Sequence[str]
    dominant_entry_types: Sequence[TimelineEntryType]
    confidence: float
