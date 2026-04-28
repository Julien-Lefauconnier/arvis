# tests/kernel_core/memory/test_memory_syscalls.py

from __future__ import annotations


from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler

from arvis.kernel_core.memory.repositories.in_memory import InMemoryMemoryRepository
from arvis.kernel_core.memory.service import MemoryService
from arvis.kernel_core.memory.policy import MemoryPolicyService

# Important: force syscall registration
from arvis.kernel_core.syscalls.syscalls import memory_syscalls  # noqa: F401


USER_ID = "user-1"


# ============================================================
# Helpers
# ============================================================


def _make_handler(
    memory_service: MemoryService | None = None,
    memory_policy_service: MemoryPolicyService | None = None,
) -> SyscallHandler:
    services = KernelServiceRegistry(
        memory_service=memory_service,
        memory_policy_service=memory_policy_service,
    )
    return SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=services,
    )


# ============================================================
# memory.get
# ============================================================


def test_memory_get_returns_record() -> None:
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo)

    service.put_record(
        user_id=USER_ID,
        namespace="default",
        key="k1",
        value={"a": 1},
    )

    policy = MemoryPolicyService()
    handler = _make_handler(service, policy)

    result = handler.handle(
        Syscall(
            name="memory.get",
            args={
                "user_id": USER_ID,
                "namespace": "default",
                "key": "k1",
            },
        )
    )

    assert result.success is True
    assert result.result["key"] == "k1"
    assert result.result["value"] == {"a": 1}


def test_memory_get_not_found() -> None:
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo)

    policy = MemoryPolicyService()
    handler = _make_handler(service, policy)

    result = handler.handle(
        Syscall(
            name="memory.get",
            args={
                "user_id": USER_ID,
                "namespace": "default",
                "key": "missing",
            },
        )
    )

    assert result.success is True
    assert result.result is None


# ============================================================
# memory.put
# ============================================================


def test_memory_put_creates_record() -> None:
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo)

    policy = MemoryPolicyService()
    handler = _make_handler(service, policy)

    result = handler.handle(
        Syscall(
            name="memory.put",
            args={
                "user_id": USER_ID,
                "namespace": "default",
                "key": "k1",
                "value": {"x": 42},
                "tags": ["test"],
            },
        )
    )

    assert result.success is True
    assert result.result["key"] == "k1"
    assert result.result["value"] == {"x": 42}
    assert result.result["version"] == 1
    assert result.result["tags"] == ["test"]


def test_memory_put_updates_record() -> None:
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo)

    service.put_record(
        user_id=USER_ID,
        namespace="default",
        key="k1",
        value=1,
        tags=[],
    )

    policy = MemoryPolicyService()
    handler = _make_handler(service, policy)

    result = handler.handle(
        Syscall(
            name="memory.put",
            args={
                "user_id": USER_ID,
                "namespace": "default",
                "key": "k1",
                "value": 2,
                "tags": [],
            },
        )
    )

    assert result.success is True
    assert result.result["value"] == 2
    assert result.result["version"] == 2


# ============================================================
# memory.delete
# ============================================================


def test_memory_delete_removes_record() -> None:
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo)

    service.put_record(
        user_id=USER_ID,
        namespace="default",
        key="k1",
        value=123,
    )

    policy = MemoryPolicyService()
    handler = _make_handler(service, policy)

    result = handler.handle(
        Syscall(
            name="memory.delete",
            args={
                "user_id": USER_ID,
                "namespace": "default",
                "key": "k1",
            },
        )
    )

    assert result.success is True
    assert result.result["deleted"] is True

    # verify gone
    result2 = handler.handle(
        Syscall(
            name="memory.get",
            args={
                "user_id": USER_ID,
                "namespace": "default",
                "key": "k1",
            },
        )
    )

    assert result2.success is True
    assert result2.result is None


def test_memory_delete_not_found() -> None:
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo)

    policy = MemoryPolicyService()
    handler = _make_handler(service, policy)

    result = handler.handle(
        Syscall(
            name="memory.delete",
            args={
                "user_id": USER_ID,
                "namespace": "default",
                "key": "missing",
            },
        )
    )

    assert result.success is True
    assert result.result is None


# ============================================================
# memory.list
# ============================================================


def test_memory_list_all() -> None:
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo)

    service.put_record(
        user_id=USER_ID,
        namespace="ns1",
        key="a",
        value=1,
        tags=[],
    )
    service.put_record(
        user_id=USER_ID,
        namespace="ns2",
        key="b",
        value=2,
        tags=[],
    )

    policy = MemoryPolicyService()
    handler = _make_handler(service, policy)

    result = handler.handle(
        Syscall(
            name="memory.list",
            args={
                "user_id": USER_ID,
            },
        )
    )

    assert result.success is True
    assert len(result.result) == 2


def test_memory_list_namespace_filter() -> None:
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo)

    service.put_record(
        user_id=USER_ID,
        namespace="ns1",
        key="a",
        value=1,
        tags=[],
    )
    service.put_record(
        user_id=USER_ID,
        namespace="ns2",
        key="b",
        value=2,
        tags=[],
    )

    policy = MemoryPolicyService()
    handler = _make_handler(service, policy)

    result = handler.handle(
        Syscall(
            name="memory.list",
            args={
                "user_id": USER_ID,
                "namespace": "ns1",
            },
        )
    )

    assert result.success is True
    assert len(result.result) == 1
    assert result.result[0]["namespace"] == "ns1"


# ============================================================
# service missing
# ============================================================


def test_memory_syscalls_fail_without_service() -> None:
    handler = _make_handler(None)

    result = handler.handle(
        Syscall(
            name="memory.get",
            args={
                "user_id": USER_ID,
                "namespace": "default",
                "key": "k1",
            },
        )
    )

    assert result.success is False
    assert result.error == "no_memory_service"


def test_memory_put_and_get_roundtrip() -> None:
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo)
    policy = MemoryPolicyService()
    handler = _make_handler(service, policy)

    put_result = handler.handle(
        Syscall(
            name="memory.put",
            args={
                "user_id": USER_ID,
                "namespace": "default",
                "key": "k1",
                "value": {"x": 1},
            },
        )
    )

    assert put_result.success is True
    assert put_result.result["key"] == "k1"
    assert put_result.result["value"] == {"x": 1}

    get_result = handler.handle(
        Syscall(
            name="memory.get",
            args={
                "user_id": USER_ID,
                "namespace": "default",
                "key": "k1",
            },
        )
    )

    assert get_result.success is True
    assert get_result.result is not None
    assert get_result.result["value"] == {"x": 1}


def test_memory_get_denies_cross_user_access() -> None:
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo)
    policy = MemoryPolicyService()

    service.put_record(
        user_id=USER_ID,
        namespace="default",
        key="secret",
        value="value",
    )

    handler = _make_handler(service, policy)

    result = handler.handle(
        Syscall(
            name="memory.get",
            args={
                "user_id": USER_ID,
                "actor_user_id": "user-2",
                "namespace": "default",
                "key": "secret",
            },
        )
    )

    assert result.success is False
    assert result.error == "memory_access_denied"


def test_memory_put_fails_without_policy_service() -> None:
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo)
    handler = _make_handler(service, None)

    result = handler.handle(
        Syscall(
            name="memory.put",
            args={
                "user_id": USER_ID,
                "namespace": "default",
                "key": "k1",
                "value": 1,
            },
        )
    )

    assert result.success is False
    assert result.error == "no_memory_policy_service"


def test_memory_get_fails_without_memory_service() -> None:
    policy = MemoryPolicyService()
    handler = _make_handler(None, policy)

    result = handler.handle(
        Syscall(
            name="memory.get",
            args={
                "user_id": USER_ID,
                "namespace": "default",
                "key": "k1",
            },
        )
    )

    assert result.success is False
    assert result.error == "no_memory_service"


def test_memory_list_filters_namespace() -> None:
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo)
    policy = MemoryPolicyService()

    service.put_record(user_id=USER_ID, namespace="ns1", key="a", value=1)
    service.put_record(user_id=USER_ID, namespace="ns2", key="b", value=2)

    handler = _make_handler(service, policy)

    result = handler.handle(
        Syscall(
            name="memory.list",
            args={
                "user_id": USER_ID,
                "namespace": "ns1",
            },
        )
    )

    assert result.success is True
    assert len(result.result) == 1
    assert result.result[0]["namespace"] == "ns1"
    assert result.result[0]["key"] == "a"


def test_memory_delete_removes_record_syscall() -> None:
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo)
    policy = MemoryPolicyService()

    service.put_record(
        user_id=USER_ID,
        namespace="default",
        key="k1",
        value=1,
    )

    handler = _make_handler(service, policy)

    result = handler.handle(
        Syscall(
            name="memory.delete",
            args={
                "user_id": USER_ID,
                "namespace": "default",
                "key": "k1",
            },
        )
    )

    assert result.success is True
    assert result.result["deleted"] is True

    check = handler.handle(
        Syscall(
            name="memory.get",
            args={
                "user_id": USER_ID,
                "namespace": "default",
                "key": "k1",
            },
        )
    )

    assert check.success is True
    assert check.result is None


def test_memory_snapshot_syscall_returns_snapshot():
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo=repo)
    policy = MemoryPolicyService()

    service.put_record(user_id="u1", namespace="prefs", key="language", value="fr")

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            memory_service=service,
            memory_policy_service=policy,
        ),
    )

    result = handler.handle(
        Syscall(
            name="memory.snapshot",
            args={"user_id": "u1"},
        )
    )

    assert result.success is True
    assert result.result is not None
    assert result.result["user_id"] == "u1"
    assert result.result["total_records"] == 1
    assert result.result["active_records"] == 1
    assert result.result["is_empty"] is False
    assert len(result.result["records"]) == 1
    assert result.result["records"][0]["key"] == "language"
