# tests/kernel_core/memory/test_memory_service.py

from __future__ import annotations

import time

import pytest

from arvis.kernel_core.memory.exceptions import (
    MemoryInvalidKeyError,
    MemoryInvalidNamespaceError,
    MemoryInvalidTagsError,
    MemoryRecordNotFoundError,
)
from arvis.kernel_core.memory.repositories.in_memory import (
    InMemoryMemoryRepository,
)
from arvis.kernel_core.memory.service import MemoryService

USER_ID = "user-1"


def _make_service() -> MemoryService:
    repo = InMemoryMemoryRepository()
    return MemoryService(repo)


def test_put_record_creates_new_record() -> None:
    service = _make_service()

    record = service.put_record(
        user_id=USER_ID,
        namespace="ns",
        key="k",
        value="value",
    )

    assert record.namespace == "ns"
    assert record.key == "k"
    assert record.value == "value"
    assert record.version == 1


def test_put_record_updates_existing_record() -> None:
    service = _make_service()

    first = service.put_record(
        user_id=USER_ID,
        namespace="ns",
        key="k",
        value="v1",
    )

    time.sleep(0.01)  # ensure updated_at differs

    second = service.put_record(
        user_id=USER_ID,
        namespace="ns",
        key="k",
        value="v2",
    )

    assert second.record_id == first.record_id
    assert second.version == 2
    assert second.value == "v2"
    assert second.updated_at >= first.updated_at


def test_get_record_returns_record() -> None:
    service = _make_service()

    service.put_record(
        user_id=USER_ID,
        namespace="ns",
        key="k",
        value="v",
    )

    record = service.get_record(
        user_id=USER_ID,
        namespace="ns",
        key="k",
    )

    assert record.key == "k"


def test_get_record_raises_if_missing() -> None:
    service = _make_service()

    with pytest.raises(MemoryRecordNotFoundError):
        service.get_record(
            user_id=USER_ID,
            namespace="ns",
            key="missing",
        )


def test_delete_record_removes_record() -> None:
    service = _make_service()

    service.put_record(
        user_id=USER_ID,
        namespace="ns",
        key="k",
        value="v",
    )

    service.delete_record(
        user_id=USER_ID,
        namespace="ns",
        key="k",
    )

    with pytest.raises(MemoryRecordNotFoundError):
        service.get_record(
            user_id=USER_ID,
            namespace="ns",
            key="k",
        )


def test_delete_record_raises_if_missing() -> None:
    service = _make_service()

    with pytest.raises(MemoryRecordNotFoundError):
        service.delete_record(
            user_id=USER_ID,
            namespace="ns",
            key="k",
        )


def test_list_records_returns_all() -> None:
    service = _make_service()

    service.put_record(user_id=USER_ID, namespace="a", key="k1", value="v")
    service.put_record(user_id=USER_ID, namespace="b", key="k2", value="v")

    records = service.list_records(user_id=USER_ID)

    assert len(records) == 2


def test_list_records_filters_namespace() -> None:
    service = _make_service()

    service.put_record(user_id=USER_ID, namespace="a", key="k1", value="v")
    service.put_record(user_id=USER_ID, namespace="b", key="k2", value="v")

    records = service.list_records(user_id=USER_ID, namespace="a")

    assert len(records) == 1
    assert records[0].namespace == "a"


def test_namespace_is_normalized() -> None:
    service = _make_service()

    record = service.put_record(
        user_id=USER_ID,
        namespace="  ns  ",
        key="k",
        value="v",
    )

    assert record.namespace == "ns"


def test_key_is_normalized() -> None:
    service = _make_service()

    record = service.put_record(
        user_id=USER_ID,
        namespace="ns",
        key="  k  ",
        value="v",
    )

    assert record.key == "k"


def test_invalid_namespace_raises() -> None:
    service = _make_service()

    with pytest.raises(MemoryInvalidNamespaceError):
        service.put_record(
            user_id=USER_ID,
            namespace="   ",
            key="k",
            value="v",
        )


def test_invalid_key_raises() -> None:
    service = _make_service()

    with pytest.raises(MemoryInvalidKeyError):
        service.put_record(
            user_id=USER_ID,
            namespace="ns",
            key="   ",
            value="v",
        )


def test_tags_are_normalized_and_sorted() -> None:
    service = _make_service()

    record = service.put_record(
        user_id=USER_ID,
        namespace="ns",
        key="k",
        value="v",
        tags=["b", "a", "a"],
    )

    assert record.tags == ("a", "b")


def test_invalid_tags_raise() -> None:
    service = _make_service()

    with pytest.raises(MemoryInvalidTagsError):
        service.put_record(
            user_id=USER_ID,
            namespace="ns",
            key="k",
            value="v",
            tags=["valid", "   "],
        )
