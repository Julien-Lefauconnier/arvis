# arvis/kernel_core/memory/snapshot.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from arvis.kernel_core.memory.models import MemoryRecord


@dataclass(frozen=True)
class MemorySnapshot:
    """
    Immutable kernel snapshot of visible memory state for one user.

    Guarantees:
    - deterministic ordering
    - read-only execution view
    - no hidden inference
    """

    user_id: str
    records: Tuple[MemoryRecord, ...]
    total_records: int
    active_records: int
    deleted_records: int
    last_updated_at: int | None = None

    @property
    def is_empty(self) -> bool:
        return self.total_records == 0