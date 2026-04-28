# arvis/memory/memory_long_service.py

from typing import List, Dict, Iterable, Optional
from datetime import datetime

from arvis.memory.memory_long_repository import MemoryLongRepository
from arvis.memory.memory_long_snapshot import MemoryLongSnapshot
from arvis.memory.memory_long_entry import MemoryLongEntry


class MemoryLongService:
    """
    Cognitive-safe facade over long-term memory.

    Responsibilities:
    - retrieve active memory entries
    - build ZKCS-compliant snapshots
    - provide batch access for scalable pipelines

    Constraints:
    - no payload access
    - no interpretation
    - no inference
    """

    def __init__(self, repository: MemoryLongRepository):
        self.repository = repository

    # ---------------------------------------------------------
    # SINGLE USER
    # ---------------------------------------------------------

    def get_snapshot(
        self,
        *,
        user_id: str,
        now: Optional[datetime] = None,
    ) -> MemoryLongSnapshot:
        """
        Build a snapshot of active long-term memory for a user.
        """

        entries = self.repository.list_active_entries(user_id=user_id)

        return self._build_snapshot(entries)

    # ---------------------------------------------------------
    # BATCH MODE (SCALABILITY)
    # ---------------------------------------------------------

    def get_snapshots_batch(
        self,
        *,
        user_ids: Iterable[str],
        now: Optional[datetime] = None,
    ) -> Dict[str, MemoryLongSnapshot]:
        """
        Batch snapshot generation.

        Critical for:
        - async pipelines
        - multi-user inference
        - simulation
        """

        raw = self.repository.list_active_entries_batch(user_ids=user_ids)

        snapshots: Dict[str, MemoryLongSnapshot] = {}

        for user_id, entries in raw.items():
            snapshots[user_id] = self._build_snapshot(entries)

        return snapshots

    # ---------------------------------------------------------
    # INTERNAL
    # ---------------------------------------------------------

    def _build_snapshot(
        self,
        entries: List[MemoryLongEntry],
    ) -> MemoryLongSnapshot:
        """
        ZKCS-safe snapshot builder.
        """

        return MemoryLongSnapshot(
            active_entries=entries,
            total_entries=len(entries),
            revoked_entries=0,  # not tracked at this layer
            last_updated_at=None,
        )
