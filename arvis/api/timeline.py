# arvis/api/timeline.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from veramem_kernel.api.timeline import TimelineSnapshot, TimelineEntry

# -----------------------------------------------------
# Entry View
# -----------------------------------------------------

@dataclass(frozen=True)
class TimelineEntryView:
    entry_id: str
    timestamp: str
    type: str
    title: str
    description: Optional[str]
    action_id: Optional[str]
    place_id: Optional[str]
    nature: str

    @staticmethod
    def from_entry(entry: TimelineEntry) -> "TimelineEntryView":
        return TimelineEntryView(
            entry_id=entry.entry_id,
            timestamp=entry.timestamp.isoformat(),
            type=str(entry.type),
            title=entry.title,
            description=entry.description,
            action_id=entry.action_id,
            place_id=entry.place_id,
            nature=str(entry.nature),
        )


# -----------------------------------------------------
# Timeline View
# -----------------------------------------------------

@dataclass(frozen=True)
class TimelineView:
    """
    Public projection of a TimelineSnapshot.
    """

    entries: List[TimelineEntryView]
    head: Optional[str]
    total_entries: int

    @staticmethod
    def from_snapshot(snapshot: TimelineSnapshot) -> "TimelineView":
        entries = [
            TimelineEntryView.from_entry(e)
            for e in snapshot.entries
        ]

        return TimelineView(
            entries=entries,
            head=snapshot.head,
            total_entries=len(snapshot.entries),
        )

    # -----------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "head": self.head,
            "total_entries": self.total_entries,
            "entries": [
                {
                    "entry_id": e.entry_id,
                    "timestamp": e.timestamp,
                    "type": e.type,
                    "title": e.title,
                    "description": e.description,
                    "action_id": e.action_id,
                    "place_id": e.place_id,
                    "nature": e.nature,
                }
                for e in self.entries
            ],
        }

    def summary(self) -> str:
        return f"Timeline(entries={self.total_entries}, head={self.head})"