# arvis/kernel_core/syscalls/syscalls/memory_syscalls.py

from __future__ import annotations

from typing import Any, Optional, Protocol

from arvis.kernel_core.memory.policy import (
    MemoryAccessRequest,
    MemoryPolicyService,
)
from arvis.kernel_core.memory.service import MemoryService
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import register_syscall
from arvis.kernel_core.memory.exceptions import MemoryRecordNotFoundError
from arvis.kernel_core.memory.snapshot import MemorySnapshot


class SyscallHandlerLike(Protocol):
    services: KernelServiceRegistry


def _get_memory_service(handler: SyscallHandlerLike) -> Optional[MemoryService]:
    return handler.services.memory_service


def _get_memory_policy_service(
    handler: SyscallHandlerLike,
) -> Optional[MemoryPolicyService]:
    return handler.services.memory_policy_service


def _missing_service_error(service_name: str) -> SyscallResult:
    return SyscallResult(success=False, error=service_name)


def _authorize(
    *,
    handler: SyscallHandlerLike,
    actor_user_id: str,
    owner_user_id: str,
    namespace: Optional[str],
    action: str,
    key: Optional[str] = None,
) -> Optional[SyscallResult]:
    policy = _get_memory_policy_service(handler)
    if policy is None:
        return _missing_service_error("no_memory_policy_service")

    decision = policy.evaluate(
        MemoryAccessRequest(
            actor_user_id=actor_user_id,
            owner_user_id=owner_user_id,
            namespace=namespace,
            action=action,
            key=key,
        )
    )

    if not decision.allowed:
        return SyscallResult(
            success=False,
            error=decision.reason or "memory_policy_violation",
        )

    return None


def _serialize_record(record: Any) -> dict[str, Any]:
    return {
        "user_id": record.user_id,
        "namespace": record.namespace,
        "key": record.key,
        "value": record.value,
        "version": record.version,
        "tags": list(getattr(record, "tags", [])),
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _serialize_snapshot(snapshot: MemorySnapshot) -> dict[str, Any]:
    return {
        "user_id": snapshot.user_id,
        "records": [_serialize_record(record) for record in snapshot.records],
        "total_records": snapshot.total_records,
        "active_records": snapshot.active_records,
        "deleted_records": snapshot.deleted_records,
        "last_updated_at": snapshot.last_updated_at,
        "is_empty": snapshot.is_empty,
    }

@register_syscall("memory.get")
def memory_get(
    handler: SyscallHandlerLike,
    user_id: str,
    namespace: str,
    key: str,
    actor_user_id: Optional[str] = None,
    **_: Any,
) -> SyscallResult:
    service = _get_memory_service(handler)
    if service is None:
        return _missing_service_error("no_memory_service")

    effective_actor = actor_user_id or user_id

    denial = _authorize(
        handler=handler,
        actor_user_id=effective_actor,
        owner_user_id=user_id,
        namespace=namespace,
        action="read",
        key=key,
    )
    if denial is not None:
        return denial

    try:
        record = service.get_record(
            user_id=user_id,
            namespace=namespace,
            key=key,
        )

        return SyscallResult(success=True, result=_serialize_record(record))

    except MemoryRecordNotFoundError:
        return SyscallResult(
            success=True,
            result=None,
        )

@register_syscall("memory.put")
def memory_put(
    handler: SyscallHandlerLike,
    user_id: str,
    namespace: str,
    key: str,
    value: Any,
    actor_user_id: Optional[str] = None,
    **_: Any,
) -> SyscallResult:
    service = _get_memory_service(handler)
    if service is None:
        return _missing_service_error("no_memory_service")

    effective_actor = actor_user_id or user_id

    denial = _authorize(
        handler=handler,
        actor_user_id=effective_actor,
        owner_user_id=user_id,
        namespace=namespace,
        action="write",
        key=key,
    )
    if denial is not None:
        return denial

    record = service.put_record(
        user_id=user_id,
        namespace=namespace,
        key=key,
        value=value,
        tags=_.get("tags", []),
    )

    return SyscallResult(success=True, result=_serialize_record(record))


@register_syscall("memory.delete")
def memory_delete(
    handler: SyscallHandlerLike,
    user_id: str,
    namespace: str,
    key: str,
    actor_user_id: Optional[str] = None,
    **_: Any,
) -> SyscallResult:
    service = _get_memory_service(handler)
    if service is None:
        return _missing_service_error("no_memory_service")

    effective_actor = actor_user_id or user_id

    denial = _authorize(
        handler=handler,
        actor_user_id=effective_actor,
        owner_user_id=user_id,
        namespace=namespace,
        action="delete",
        key=key,
    )
    if denial is not None:
        return denial

    try:
        service.delete_record(
            user_id=user_id,
            namespace=namespace,
            key=key,
        )

        return SyscallResult(
            success=True,
            result={
                "deleted": True,
                "user_id": user_id,
                "namespace": namespace,
                "key": key,
            },
         )

    except MemoryRecordNotFoundError:
        return SyscallResult(success=True, result=None)


@register_syscall("memory.list")
def memory_list(
    handler: SyscallHandlerLike,
    user_id: str,
    namespace: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    **_: Any,
) -> SyscallResult:
    service = _get_memory_service(handler)
    if service is None:
        return _missing_service_error("no_memory_service")

    effective_actor = actor_user_id or user_id

    denial = _authorize(
        handler=handler,
        actor_user_id=effective_actor,
        owner_user_id=user_id,
        namespace=namespace,
        action="list",
        key=None,
    )
    if denial is not None:
        return denial

    records = service.list_records(
        user_id=user_id,
        namespace=namespace,
    )

    return SyscallResult(
        success=True,
        result=[_serialize_record(record) for record in records],
    )


@register_syscall("memory.snapshot")
def memory_snapshot(
    handler: SyscallHandlerLike,
    user_id: str,
    namespace: Optional[str] = None,
    actor_user_id: Optional[str] = None,
    **_: Any,
) -> SyscallResult:
    service = _get_memory_service(handler)
    if service is None:
        return _missing_service_error("no_memory_service")

    effective_actor = actor_user_id or user_id

    denial = _authorize(
        handler=handler,
        actor_user_id=effective_actor,
        owner_user_id=user_id,
        namespace=namespace,
        action="read",
        key=None,
    )
    if denial is not None:
        return denial

    snapshot = service.get_snapshot(
        user_id=user_id,
        namespace=namespace,
    )

    return SyscallResult(
        success=True,
        result=_serialize_snapshot(snapshot),
    )