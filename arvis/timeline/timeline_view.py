# arvis/timeline/timeline_view.py

from collections.abc import Iterator
from dataclasses import dataclass

from .timeline_entry import TimelineEntry
from .timeline_view_types import TimelineViewRole


@dataclass(frozen=True)
class TimelineView:
    """
    Read-only projection of a canonical timeline.

    Guarantees:
    - Immutable
    - Declarative
    - Zero-knowledge compliant
    - Deterministic ordering
    """

    role: TimelineViewRole
    entries: tuple[TimelineEntry, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.role, TimelineViewRole):
            raise ValueError("TimelineView.role must be TimelineViewRole")

        if not self.role:
            raise ValueError("TimelineView.role must not be empty")

        if self.entries is None:
            raise ValueError("TimelineView.entries must not be None")

        for e in self.entries:
            if not isinstance(e, TimelineEntry):
                raise ValueError("TimelineView.entries must contain TimelineEntry")

    # --------------------------------------------------
    # Basic container API
    # --------------------------------------------------

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self) -> Iterator[TimelineEntry]:
        return iter(self.entries)

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    @property
    def head(self) -> TimelineEntry | None:
        if not self.entries:
            return None
        return self.entries[-1]
