# arvis/memory/memory_long_repository.py

from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime

from arvis.memory.memory_long_entry import (
    MemoryLongEntry,
)
from arvis.memory.memory_long_record import (
    MemoryLongRecord,
)


class MemoryLongRepository(ABC):
    """
    Abstract repository for long-term memory entries.

    Read-only from the cognition perspective.
    No inference, no validation, no write policy.
    """

    @abstractmethod
    def list_entries(self, *, user_id: str) -> list[MemoryLongRecord]:
        """
        Return all entries (raw).

        Includes:
        - active
        - revoked
        - expired

        No filtering here (low-level access).

        - no ordering guarantees
        - no filtering logic here
        """
        raise NotImplementedError

    @abstractmethod
    def list_active_entries(self, *, user_id: str) -> list[MemoryLongEntry]:
        """
        Return ACTIVE entries only.

        Filtering rules (implementation side):
        - revoked_at is None
        - expires_at is None or in the future

        This is the DEFAULT method used by cognition layer.
        """
        raise NotImplementedError

    @abstractmethod
    def list_active_entries_batch(
        self,
        *,
        user_ids: Iterable[str],
    ) -> dict[str, list[MemoryLongEntry]]:
        """
        Batch read for scalability (multi-user inference / async pipelines).

        Returns:
            {
                user_id: [MemoryLongEntry, ...],
                ...
            }
        """
        raise NotImplementedError

    # ---------------------------------------------------------
    # WRITE / MUTATION (CONTROLLED)
    # ---------------------------------------------------------

    @abstractmethod
    def revoke(
        self,
        *,
        user_id: str,
        key: str,
        revoked_at: datetime,
    ) -> None:
        raise NotImplementedError
