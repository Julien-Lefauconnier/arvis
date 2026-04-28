# arvis/reflexive/timeline/aggregation/irg_timeline_temporal_diff.py

from collections.abc import Sequence
from dataclasses import dataclass

from arvis.timeline.timeline_types import TimelineEntryType


@dataclass(frozen=True)
class IRGTimelineTemporalDiff:
    """
    Declarative comparison between two temporal IRG snapshots.

    - No interpretation
    - No decision
    - No recommendation
    """

    from_timestamp: str
    to_timestamp: str

    views_added: Sequence[str]
    views_removed: Sequence[str]

    entry_types_added: Sequence[TimelineEntryType]
    entry_types_removed: Sequence[TimelineEntryType]

    confidence_delta: float

    is_stable: bool
