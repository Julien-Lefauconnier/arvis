# arvis/timeline/timeline_view.py

from dataclasses import dataclass
from typing import Tuple

from .timeline_entry import TimelineEntry


@dataclass(frozen=True)
class TimelineView:
    """
    Read-only projection of a canonical timeline.

    - Immutable
    - Declarative
    - Zero-knowledge compliant
    """

    role: str
    entries: Tuple[TimelineEntry, ...]
