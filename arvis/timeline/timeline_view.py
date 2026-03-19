# arvis/timeline/timeline_view.py

from dataclasses import dataclass
from typing import Tuple, Iterator

from .timeline_entry import TimelineEntry


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

    role: str
    entries: Tuple[TimelineEntry, ...]

    def __post_init__(self) -> None:

        if not isinstance(self.role, str):
            raise ValueError("TimelineView.role must be str")

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