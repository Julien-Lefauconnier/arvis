# tests/kernel_core/memory/test_memory_repository_in_memory.py

from __future__ import annotations

from arvis.kernel_core.memory.models import MemoryRecord
from arvis.kernel_core.memory.repositories.in_memory import (
    InMemoryMemoryRepository,
)

USER_ID = "user-1"


def _make_record(
    *,
    namespace: str,
    key: str,
    value: str = "v",
    record_id: str = "id-1",
    created_at: int = 1,
    updated_at: int = 1,
) -> MemoryRecord:
    return MemoryRecord(
        record_id=record_id,
        user_id=USER_ID,
        namespace=namespace,
        key=key,
        value=value,
        created_at=created_at,
        updated_at=updated_at,
    )


def test_upsert_and_get_record() -> None:
    repo = InMemoryMemoryRepository()

    record = _make_record(namespace="ns", key="k")
    repo.upsert_record(record=record)

    retrieved = repo.get_record(
        user_id=USER_ID,
        namespace="ns",
        key="k",
    )

    assert retrieved == record


def test_get_record_returns_none_if_missing() -> None:
    repo = InMemoryMemoryRepository()

    result = repo.get_record(
        user_id=USER_ID,
        namespace="ns",
        key="missing",
    )

    assert result is None


def test_list_records_filters_by_namespace() -> None:
    repo = InMemoryMemoryRepository()

    repo.upsert_record(record=_make_record(namespace="a", key="k1"))
    repo.upsert_record(record=_make_record(namespace="b", key="k2"))

    records = repo.list_records(user_id=USER_ID, namespace="a")

    assert len(records) == 1
    assert records[0].namespace == "a"


def test_list_records_returns_all_if_no_namespace() -> None:
    repo = InMemoryMemoryRepository()

    repo.upsert_record(record=_make_record(namespace="a", key="k1"))
    repo.upsert_record(record=_make_record(namespace="b", key="k2"))

    records = repo.list_records(user_id=USER_ID)

    assert len(records) == 2


def test_list_records_is_deterministically_sorted() -> None:
    repo = InMemoryMemoryRepository()

    repo.upsert_record(record=_make_record(namespace="b", key="k2"))
    repo.upsert_record(record=_make_record(namespace="a", key="k1"))

    records = repo.list_records(user_id=USER_ID)

    assert [(r.namespace, r.key) for r in records] == [
        ("a", "k1"),
        ("b", "k2"),
    ]


def test_delete_record_removes_entry() -> None:
    repo = InMemoryMemoryRepository()

    repo.upsert_record(record=_make_record(namespace="ns", key="k"))

    repo.delete_record(
        user_id=USER_ID,
        namespace="ns",
        key="k",
    )

    record = repo.get_record(
        user_id=USER_ID,
        namespace="ns",
        key="k",
    )
    assert record is not None
    assert record.status == "deleted"


def test_delete_record_is_idempotent() -> None:
    repo = InMemoryMemoryRepository()

    repo.delete_record(
        user_id=USER_ID,
        namespace="ns",
        key="k",
    )

    # no exception
