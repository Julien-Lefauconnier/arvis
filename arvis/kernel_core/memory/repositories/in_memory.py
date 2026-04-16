# arvis/kernel_core/memory/repositories/in_memory.py

from __future__ import annotations

from typing import Optional
import time

from arvis.kernel_core.memory.models import MemoryRecord
from arvis.kernel_core.memory.repository import MemoryRepository


class InMemoryMemoryRepository(MemoryRepository):
    """
    Deterministic in-memory repository for kernel memory records.

    Storage shape:
        user_id -> namespace -> key -> MemoryRecord
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, dict[str, MemoryRecord]]] = {}

    def _user_bucket(self, user_id: str) -> dict[str, dict[str, MemoryRecord]]:
        return self._store.setdefault(user_id, {})

    def list_records(
        self,
        *,
        user_id: str,
        namespace: Optional[str] = None,
    ) -> list[MemoryRecord]:
        user_bucket = self._user_bucket(user_id)

        if namespace is not None:
            namespace_bucket = user_bucket.get(namespace, {})
            records = list(namespace_bucket.values())
        else:
            records = []
            for namespace_bucket in user_bucket.values():
                records.extend(namespace_bucket.values())

        records = [r for r in records if getattr(r, "status", "active") == "active"]

        records.sort(
            key=lambda record: (
                record.namespace,
                record.key,
                record.record_id,
            )
        )
        return records

    def get_record(
        self,
        *,
        user_id: str,
        namespace: str,
        key: str,
    ) -> Optional[MemoryRecord]:
        user_bucket = self._user_bucket(user_id)
        namespace_bucket = user_bucket.get(namespace)
        if namespace_bucket is None:
            return None
        return namespace_bucket.get(key)

    def upsert_record(
        self,
        *,
        record: MemoryRecord,
    ) -> None:
        user_bucket = self._user_bucket(record.user_id)
        namespace_bucket = user_bucket.setdefault(record.namespace, {})
        namespace_bucket[record.key] = record

    def delete_record(
        self,
        *,
        user_id: str,
        namespace: str,
        key: str,
    ) -> None:
        user_bucket = self._user_bucket(user_id)
        namespace_bucket = user_bucket.get(namespace)
        if namespace_bucket is None:
            return

        record = namespace_bucket.get(key)
        if record is None:
            return

        deleted_record = MemoryRecord(
            record_id=record.record_id,
            user_id=record.user_id,
            namespace=record.namespace,
            key=record.key,
            value=record.value,
            created_at=record.created_at,
            updated_at=int(time.time()),
            version=record.version,
            tags=record.tags,
            status="deleted",
        )

        namespace_bucket[key] = deleted_record