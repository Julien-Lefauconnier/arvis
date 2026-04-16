# arvis/kernel_core/memory/repository.py

from __future__ import annotations

from typing import Optional, Protocol

from arvis.kernel_core.memory.models import MemoryRecord


class MemoryRepository(Protocol):
    def list_records(
        self,
        *,
        user_id: str,
        namespace: Optional[str] = None,
    ) -> list[MemoryRecord]:
        ...

    def get_record(
        self,
        *,
        user_id: str,
        namespace: str,
        key: str,
    ) -> Optional[MemoryRecord]:
        ...

    def upsert_record(
        self,
        *,
        record: MemoryRecord,
    ) -> None:
        ...

    def delete_record(
        self,
        *,
        user_id: str,
        namespace: str,
        key: str,
    ) -> None:
        ...