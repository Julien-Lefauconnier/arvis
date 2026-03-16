# arvis//timeline/timeline_cursor.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Optional


@dataclass(frozen=True)
class TimelineCursor:
    """
    Immutable cursor representing a position in a timeline.

    Kernel guarantees:
    - deterministic
    - distributed-safe
    - equality-based identity
    """

    timestamp: Optional[datetime]
    head: Optional[str] = None
    total_entries: int = 0

    def __post_init__(self):

        if self.timestamp is None:
            raise ValueError("TimelineCursor.timestamp must not be None")

        if self.timestamp.tzinfo is None:
            raise ValueError("TimelineCursor.timestamp must be timezone-aware")

        off = self.timestamp.tzinfo.utcoffset(self.timestamp)
        if off is None or off != timedelta(0):
            raise ValueError("TimelineCursor.timestamp must be UTC")

        if self.total_entries < 0:
            raise ValueError("TimelineCursor.total_entries must be >= 0")

        if self.head is None:
            if self.total_entries != 0:
                raise ValueError("Empty cursor must have total_entries=0")
        else:
            if len(self.head) != 64:
                raise ValueError("TimelineCursor.head must be sha256 hex")

            if any(c not in "0123456789abcdef" for c in self.head):
                raise ValueError("TimelineCursor.head must be lowercase hex")

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TimelineCursor):
            return False

        return (self.head, self.total_entries) == (
            other.head,
            other.total_entries,
        )

    def __hash__(self) -> int:
        return hash((self.head, self.total_entries))

    def to_dict(self) -> dict:
        payload = {
            "timestamp": self.timestamp.isoformat(),
        }

        if self.head is not None:
            payload["head"] = self.head
            payload["total_entries"] = self.total_entries

        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> "TimelineCursor":

        ts = datetime.fromisoformat(payload["timestamp"])

        if ts.tzinfo is None or ts.tzinfo.utcoffset(ts) != timedelta(0):
            raise ValueError("TimelineCursor timestamp must be UTC")

        return cls(
            timestamp=ts,
            head=payload.get("head"),
            total_entries=payload.get("total_entries", 0),
        )

    @classmethod
    def now(cls) -> "TimelineCursor":
        return cls(timestamp=datetime.now(timezone.utc))