# arvis/timeline/timeline_snapshot.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Tuple
from datetime import datetime, timezone

from .timeline_entry import TimelineEntry
from .timeline_hashchain import TimelineHashChain
from .timeline_cursor import TimelineCursor



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

    entries: Tuple[TimelineEntry, ...]
    hashchain: TimelineHashChain

    @property
    def head(self) -> str | None:
        return self.hashchain.head

    @classmethod
    def build(
        cls,
        entries: Iterable[TimelineEntry],
    ) -> "TimelineSnapshot":
        entries_tuple = tuple(entries)
        chain = TimelineHashChain.build(entries_tuple)
        return cls(entries_tuple, chain)

    def verify(self) -> None:
        self.hashchain.verify(self.entries)

    def append(self, entry: TimelineEntry) -> "TimelineSnapshot":
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
    