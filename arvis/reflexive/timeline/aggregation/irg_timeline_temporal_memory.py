# arvis/reflexive/timeline/aggregation/irg_timeline_temporal_memory.py

from collections import deque
from typing import Deque, Iterable, Optional

from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_snapshot import (
    IRGTimelineTemporalSnapshot,
)
from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_comparator import (
    IRGTimelineTemporalComparator,
)
from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_diff import (
    IRGTimelineTemporalDiff,
)


class IRGTimelineTemporalMemory:
    """
    Passive in-memory storage for IRG temporal snapshots.

    - Bounded
    - Read-only access
    - No persistence
    - No authority
    """

    def __init__(self, *, maxlen: int = 10):
        self._snapshots: Deque[IRGTimelineTemporalSnapshot] = deque(maxlen=maxlen)

    def append(self, snapshot: IRGTimelineTemporalSnapshot) -> None:
        self._snapshots.append(snapshot)

    def latest(self) -> Optional[IRGTimelineTemporalSnapshot]:
        if not self._snapshots:
            return None
        return self._snapshots[-1]

    def previous(self) -> Optional[IRGTimelineTemporalSnapshot]:
        if len(self._snapshots) < 2:
            return None
        return self._snapshots[-2]

    def iter_diffs(self) -> Iterable[IRGTimelineTemporalDiff]:
        """
        Iterate over temporal diffs between consecutive snapshots.
        """
        for i in range(1, len(self._snapshots)):
            yield IRGTimelineTemporalComparator.compare(
                self._snapshots[i - 1],
                self._snapshots[i],
            )

    def __len__(self) -> int:
        return len(self._snapshots)
