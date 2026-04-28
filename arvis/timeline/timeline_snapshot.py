# arvis/timeline/timeline_snapshot.py

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

from .timeline_cursor import TimelineCursor
from .timeline_entry import TimelineEntry
from .timeline_hashchain import TimelineHashChain


@dataclass(frozen=True)
class TimelineSnapshot:
    """
    Immutable, verifiable view of a timeline.

    This is the canonical kernel boundary for:
    - sync
    - audit
    - zero-knowledge proofs
    - distributed systems
    """

    entries: tuple[TimelineEntry, ...]
    hashchain: TimelineHashChain

    @property
    def head(self) -> str | None:
        return self.hashchain.head

    @classmethod
    def build(
        cls,
        entries: Iterable[TimelineEntry],
    ) -> TimelineSnapshot:
        entries_tuple = tuple(entries)
        chain = TimelineHashChain.build(entries_tuple)
        return cls(entries_tuple, chain)

    def verify(self) -> None:
        self.hashchain.verify(self.entries)

    def cursor(self) -> TimelineCursor:
        """
        Deterministic cursor representing the current snapshot state.
        """

        if not self.entries:
            return TimelineCursor(
                timestamp=datetime.fromtimestamp(0, UTC),
                head=None,
                total_entries=0,
            )

        last = self.entries[-1]

        return TimelineCursor(
            timestamp=last.created_at,
            head=self.hashchain.head,
            total_entries=len(self.entries),
        )

    def append(self, entry: TimelineEntry) -> TimelineSnapshot:
        """
        Incremental deterministic extension of the snapshot.

        This allows:
        - streaming projection
        - distributed sync
        - O(1) append
        """

        new_entries = self.entries + (entry,)
        new_hashchain = self.hashchain.append(entry)

        return TimelineSnapshot(
            entries=new_entries,
            hashchain=new_hashchain,
        )
