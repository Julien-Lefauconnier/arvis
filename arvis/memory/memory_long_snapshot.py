# arvis/memory/memory_long_snapshot.py

from dataclasses import dataclass, field
from datetime import UTC, datetime

from arvis.memory.memory_long_entry import MemoryLongEntry


def utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class MemoryLongSnapshot:
    """
    Read-only snapshot of active long-term memory.

    - no content
    - no reasoning
    - no personalization logic
    """

    active_entries: list[MemoryLongEntry] = field(default_factory=list)

    @property
    def entries(self) -> list[MemoryLongEntry]:
        return self.active_entries

    total_entries: int = 0
    revoked_entries: int = 0

    last_updated_at: datetime | None = None

    notes: str | None = None
    created_at: datetime = field(default_factory=utcnow)
