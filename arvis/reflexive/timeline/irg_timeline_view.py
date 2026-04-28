# arvis/reflexive/timeline/irg_timeline_view.py

from dataclasses import dataclass
from datetime import datetime
from arvis.timeline.timeline_view_types import TimelineViewRole


@dataclass(frozen=True)
class IRGTimelineView:
    total_events: int
    first_timestamp: datetime | None
    last_timestamp: datetime | None

    has_conflicts: bool
    has_uncertainty: bool
    has_gaps: bool
    has_linguistic_constraints: bool

    role: TimelineViewRole = TimelineViewRole.TRACE_FACTUAL

    def to_dict(self) -> dict[str, object]:
        return {
            "total_events": self.total_events,
            "first_timestamp": self.first_timestamp.isoformat()
            if self.first_timestamp
            else None,
            "last_timestamp": self.last_timestamp.isoformat()
            if self.last_timestamp
            else None,
            "has_conflicts": self.has_conflicts,
            "has_uncertainty": self.has_uncertainty,
            "has_gaps": self.has_gaps,
            "has_linguistic_constraints": self.has_linguistic_constraints,
        }
