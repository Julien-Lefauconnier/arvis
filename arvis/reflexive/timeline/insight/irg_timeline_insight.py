# arvis/reflexive/timeline/insight/irg_timeline_insight.py

from dataclasses import dataclass
from typing import Sequence

from arvis.timeline.timeline_types import TimelineEntryType
from arvis.timeline.timeline_view_types import TimelineViewRole


@dataclass(frozen=True)
class IRGTimelineInsight:
    """
    Passive reflexive insight about a timeline view.

    - Read-only
    - Declarative
    - Non-prescriptive
    - ZKCS compliant

    An insight NEVER grants or denies access.
    """

    view_role: TimelineViewRole
    dominant_entry_types: Sequence[TimelineEntryType]
    confidence: float            # 0.0 → 1.0
    message: str                 # human-readable, non-sensitive

    def to_dict(self) -> dict[str, object]:
        return {
            "view_role": self.view_role.value,
            "dominant_entry_types": [t.value for t in self.dominant_entry_types],
            "confidence": self.confidence,
            "message": self.message,
        }