# arvis/reflexive/timeline/aggregation/irg_timeline_temporal_memory_view.py

from dataclasses import dataclass
from typing import Sequence

from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_diff import (
    IRGTimelineTemporalDiff,
)


@dataclass(frozen=True)
class IRGTimelineTemporalMemoryView:
    """
    Read-only view over temporal IRG memory.

    Suitable for explanation or introspection layers.
    """

    diffs: Sequence[IRGTimelineTemporalDiff]
    is_stable_over_time: bool
