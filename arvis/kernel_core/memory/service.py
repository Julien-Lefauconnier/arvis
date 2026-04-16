# arvis/kernel_core/memory/service.py

from __future__ import annotations

from typing import Iterable, Optional
from datetime import datetime
from arvis.kernel_core.memory.snapshot import MemorySnapshot

from arvis.kernel_core.memory.exceptions import (
    MemoryInvalidKeyError,
    MemoryInvalidNamespaceError,
    MemoryInvalidTagsError,
    MemoryRecordNotFoundError,
)
from arvis.kernel_core.memory.models import MemoryRecord, MemoryValue
from arvis.kernel_core.memory.repository import MemoryRepository

from veramem_kernel.journals.observation_long.observation_long_writer import (
    ObservationLongWriter,
)
from veramem_kernel.journals.observation_long.observation_long_event import (
    ObservationLongEvent,
)


class MemoryService:
    """
    Kernel memory service.

    Responsibilities:
    - validate namespace and key invariants
    - normalize tags deterministically
    - provide deterministic CRUD semantics over MemoryRepository
    """

    def __init__(
        self,
        repo: MemoryRepository,
        writer: Optional[ObservationLongWriter] = None,
    ) -> None:
        self.repo = repo
        self.writer = writer

    def list_records(
        self,
        *,
        user_id: str,
        namespace: Optional[str] = None,
    ) -> list[MemoryRecord]:
        normalized_namespace = None
        if namespace is not None:
            normalized_namespace = self._normalize_namespace(namespace)

        return self.repo.list_records(
            user_id=user_id,
            namespace=normalized_namespace,
        )

    def get_record(
        self,
        *,
        user_id: str,
        namespace: str,
        key: str,
    ) -> MemoryRecord:
        normalized_namespace = self._normalize_namespace(namespace)
        normalized_key = self._normalize_key(key)

        record = self.repo.get_record(
            user_id=user_id,
            namespace=normalized_namespace,
            key=normalized_key,
        )

        if record is None:
            raise MemoryRecordNotFoundError(
                f"memory record not found: {normalized_namespace}/{normalized_key}"
            )
        
        if record.status == "deleted":
            raise MemoryRecordNotFoundError(
                f"memory record deleted: {normalized_namespace}/{normalized_key}"
            )

        return record

    def put_record(
        self,
        *,
        user_id: str,
        namespace: str,
        key: str,
        value: MemoryValue,
        tags: Iterable[str] = (),
    ) -> MemoryRecord:
        normalized_namespace = self._normalize_namespace(namespace)
        normalized_key = self._normalize_key(key)
        normalized_tags = self._normalize_tags(tags)

        existing = self.repo.get_record(
            user_id=user_id,
            namespace=normalized_namespace,
            key=normalized_key,
        )

        is_deleted = (
            existing is not None
            and getattr(existing, "status", "active") == "deleted"
        )
 
        observed_at = datetime.utcnow()
        ts = int(observed_at.timestamp())


        if existing is None or is_deleted:
            record_id = (
                existing.record_id
                if existing is not None
                else f"mem:{user_id}:{normalized_namespace}:{normalized_key}"
            )
            record = MemoryRecord(
                record_id=record_id,
                user_id=user_id,
                namespace=normalized_namespace,
                key=normalized_key,
                value=value,
                created_at=ts,
                updated_at=ts,
                version=1,
                tags=normalized_tags,
                status="active",
            )
        else:
            record = MemoryRecord(
                record_id=existing.record_id,
                user_id=existing.user_id,
                namespace=existing.namespace,
                key=existing.key,
                value=value,
                created_at=existing.created_at,
                updated_at=ts,
                version=existing.version + 1,
                tags=normalized_tags,
                status="active",
            )

        if self.writer is not None:
            event = ObservationLongEvent(
                user_id=user_id,
                source_type="memory",
                payload={
                    "op": "put",
                    "namespace": normalized_namespace,
                    "key": normalized_key,
                    "value": value,
                    "tags": normalized_tags,
                    "version": record.version,
                },
                observed_at=observed_at,
            )
            self.writer.append(event)

        self.repo.upsert_record(record=record)
        return record

    def delete_record(
        self,
        *,
        user_id: str,
        namespace: str,
        key: str,
    ) -> None:
        normalized_namespace = self._normalize_namespace(namespace)
        normalized_key = self._normalize_key(key)

        existing = self.repo.get_record(
            user_id=user_id,
            namespace=normalized_namespace,
            key=normalized_key,
        )
        if existing is None:
            raise MemoryRecordNotFoundError(
                f"memory record not found: {normalized_namespace}/{normalized_key}"
            )
        
        if existing.status == "deleted":
            raise MemoryRecordNotFoundError(
                f"memory record deleted: {normalized_namespace}/{normalized_key}"
            )
        
        observed_at = datetime.utcnow()
        ts = int(observed_at.timestamp())

        # 2. projection
        deleted_record = MemoryRecord(
            record_id=existing.record_id,
            user_id=existing.user_id,
            namespace=existing.namespace,
            key=existing.key,
            value=existing.value,
            created_at=existing.created_at,
            updated_at=ts,
            version=existing.version,
            tags=existing.tags,
            status="deleted",
        )

        if self.writer is not None:
            event = ObservationLongEvent(
                user_id=user_id,
                source_type="memory",
                payload={
                    "op": "delete",
                    "namespace": normalized_namespace,
                    "key": normalized_key,
                },
                observed_at=observed_at,
            )
            self.writer.append(event)

        self.repo.upsert_record(record=deleted_record)


    def _normalize_namespace(self, namespace: str) -> str:
        normalized = namespace.strip()
        if not normalized:
            raise MemoryInvalidNamespaceError("namespace cannot be empty")
        return normalized

    def _normalize_key(self, key: str) -> str:
        normalized = key.strip()
        if not normalized:
            raise MemoryInvalidKeyError("key cannot be empty")
        return normalized

    def _normalize_tags(self, tags: Iterable[str]) -> tuple[str, ...]:
        normalized_tags: list[str] = []

        for raw_tag in tags:
            tag = raw_tag.strip()
            if not tag:
                raise MemoryInvalidTagsError("tags cannot contain empty values")
            normalized_tags.append(tag)

        return tuple(sorted(set(normalized_tags)))
    

    def get_snapshot(
        self,
        *,
        user_id: str,
        namespace: Optional[str] = None,
    ) -> MemorySnapshot:
        normalized_namespace = None
        if namespace is not None:
            normalized_namespace = self._normalize_namespace(namespace)

        records = self.repo.list_records(
            user_id=user_id,
            namespace=normalized_namespace,
        )

        ordered_records = tuple(records)

        deleted_records = 0
        active_records = 0
        last_updated_at: int | None = None

        for record in ordered_records:
            if record.status == "deleted":
                deleted_records += 1
            else:
                active_records += 1

            if last_updated_at is None or record.updated_at > last_updated_at:
                last_updated_at = record.updated_at

        return MemorySnapshot(
            user_id=user_id,
            records=ordered_records,
            total_records=len(ordered_records),
            active_records=active_records,
            deleted_records=deleted_records,
            last_updated_at=last_updated_at,
        )