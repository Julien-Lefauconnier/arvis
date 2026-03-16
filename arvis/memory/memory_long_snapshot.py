# arvis/memory/memory_long_snapshot.py

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from arvis.memory.memory_long_entry import MemoryLongEntry


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class MemoryLongSnapshot:
    """
    Read-only snapshot of active long-term memory.

    - no content
    - no reasoning
    - no personalization logic
    """

    active_entries: List[MemoryLongEntry] = field(default_factory=list)

    @property
    def entries(self) -> List[MemoryLongEntry]:
        return self.active_entries

    total_entries: int = 0
    revoked_entries: int = 0

    last_updated_at: Optional[datetime] = None

    notes: Optional[str] = None
    created_at: datetime = field(default_factory=utcnow)