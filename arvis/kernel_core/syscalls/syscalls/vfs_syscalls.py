# arvis/kernel_core/syscalls/syscalls/vfs_syscalls.py

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol

from arvis.errors.base import (
    ArvisRuntimeError,
    ErrorDomain,
)
from arvis.errors.normalization import normalize_error
from arvis.errors.provenance import cause_from_exception
from arvis.errors.syscall import SyscallBoundaryViolationError
from arvis.kernel_core.access.identity import principal_from_context
from arvis.kernel_core.access.models import AccessContext, Principal
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import (
    SyscallEffect,
    register_syscall,
)
from arvis.kernel_core.vfs.exceptions import (
    VFSCycleError,
    VFSFolderNotEmptyError,
    VFSInvalidNameError,
    VFSItemNotFoundError,
    VFSNameConflictError,
    VFSParentNotFolderError,
    VFSParentNotFoundError,
)
from arvis.kernel_core.vfs.models import VFSItem
from arvis.kernel_core.vfs.service import VFSService
from arvis.kernel_core.vfs.tree import VFSTreeNode, build_vfs_tree
from arvis.kernel_core.vfs.zip.exceptions import ZipConflictError, ZipRejectedError
from arvis.kernel_core.vfs.zip.models import (
    ZipCollision,
    ZipCollisionReport,
    ZipImportPlan,
    ZipNode,
)
from arvis.kernel_core.vfs.zip.service import ZipIngestDecision, ZipIngestService

# =====================================================
# PROTOCOL
# =====================================================


class SyscallHandlerLike(Protocol):
    services: KernelServiceRegistry


# =====================================================
# HELPERS
# =====================================================


def _get_vfs(handler: SyscallHandlerLike) -> VFSService | None:
    return handler.services.vfs_service


def _get_zip(handler: SyscallHandlerLike) -> ZipIngestService | None:
    return handler.services.zip_ingest_service


# =====================================================
# ACCESS RESOLVERS
# =====================================================

_AccessResolver = Callable[[Mapping[str, Any], KernelServiceRegistry], AccessContext]


def _scope_owner_resolver(effect: SyscallEffect, syscall_name: str) -> _AccessResolver:
    """Resolve the resource owner as the calling user's own scope.

    Used by syscalls that act on the caller's whole VFS scope (list, tree)
    rather than a referenced item. Under the owner-scoped policy this is
    behaviour-neutral, since the caller is the owner of its own scope.
    """

    def _resolve(
        args: Mapping[str, Any], services: KernelServiceRegistry
    ) -> AccessContext:
        user_id: str = args["user_id"]
        principal = principal_from_context(args.get("ctx"))
        if principal is None:
            principal = Principal(user_id=user_id)
        return AccessContext(
            principal=principal,
            effect=effect,
            resource_owner_id=user_id,
            syscall_name=syscall_name,
        )

    return _resolve


def _item_owner_resolver(
    effect: SyscallEffect, syscall_name: str, *, id_arg: str
) -> _AccessResolver:
    """Resolve the resource owner as the owner of a referenced VFS item.

    ``id_arg`` names the syscall argument holding the target item or parent
    id (for example ``item_id`` or ``parent_id``). The real ``owner_id`` is
    read from the item through the VFS service, so a principal acting on a
    resource it does not own is denied by the owner-scoped policy.

    Owner resolution is best-effort. When the reference is absent (creation at
    the root) or the item cannot be read for any reason, ownership falls back
    to the caller and dispatch proceeds. The syscall body stays the single
    authority for executing the operation and mapping its errors: an
    unexpected VFS failure must surface as a boundary violation raised by the
    body, never be pre-empted or recast as an authorization denial here.
    """

    def _resolve(
        args: Mapping[str, Any], services: KernelServiceRegistry
    ) -> AccessContext:
        user_id: str = args["user_id"]
        principal = principal_from_context(args.get("ctx"))
        if principal is None:
            principal = Principal(user_id=user_id)
        reference = args.get(id_arg)
        owner_id = user_id
        organization_id: str | None = None

        vfs: VFSService | None = services.vfs_service
        if vfs is not None and isinstance(reference, str):
            try:
                item = vfs.get_item(user_id=user_id, item_id=reference)
                owner_id = item.owner_id
                organization_id = item.organization_id
            except Exception:
                owner_id = user_id
                organization_id = None

        return AccessContext(
            principal=principal,
            effect=effect,
            resource_owner_id=owner_id,
            resource_organization_id=organization_id,
            resource_id=reference if isinstance(reference, str) else None,
            syscall_name=syscall_name,
        )

    return _resolve


def _missing_service_error(service_name: str) -> SyscallResult:
    return SyscallResult.failure(
        _vfs_error(
            code=service_name,
            message=service_name.replace("_", " "),
        )
    )


def _vfs_error(
    *,
    code: str,
    message: str,
    exc: Exception | None = None,
    retry_class: str = "permanent",
) -> ArvisRuntimeError:
    details: dict[str, str | int | float | bool | None] = {
        "retry_class": retry_class,
    }

    cause = None

    if exc is not None:
        normalized = normalize_error(exc)
        details.update(
            {
                "exception": type(exc).__name__,
            }
        )
        cause = normalized.cause
        message = normalized.message

    return ArvisRuntimeError(
        message,
        code=code,
        domain=ErrorDomain.VFS,
        details=details,
        cause=cause,
    )


# =====================================================
# SERIALIZATION
# =====================================================


def _serialize_vfs_item(item: VFSItem) -> dict[str, Any]:
    return {
        "item_id": item.item_id,
        "display_name": item.display_name,
        "item_type": item.item_type,
        "parent_id": item.parent_id,
        "mime": item.mime,
        "file_size": item.file_size,
        "created_at": item.created_at,
    }


def _serialize_tree_node(node: VFSTreeNode) -> dict[str, Any]:
    return {
        "item": _serialize_vfs_item(node.item),
        "children": [_serialize_tree_node(child) for child in node.children],
    }


def _serialize_tree(nodes: list[VFSTreeNode]) -> list[dict[str, Any]]:
    return [_serialize_tree_node(node) for node in nodes]


def _serialize_zip_node(node: ZipNode) -> dict[str, Any]:
    return {
        "name": node.name,
        "node_type": node.node_type,
        "size": node.size,
        "extension": node.extension,
        "supported": node.supported,
        "reason": node.reason,
        "zip_path": node.zip_path,
        "children": [_serialize_zip_node(child) for child in node.children],
    }


def _serialize_zip_collision(collision: ZipCollision) -> dict[str, Any]:
    return {
        "zip_node": {
            "name": collision.zip_node.name,
            "node_type": collision.zip_node.node_type,
            "zip_path": collision.zip_node.zip_path,
            "reason": collision.zip_node.reason,
            "supported": collision.zip_node.supported,
        },
        "vfs_item": _serialize_vfs_item(collision.vfs_item),
        "reason": collision.reason,
    }


def _serialize_zip_collision_report(report: ZipCollisionReport) -> dict[str, Any]:
    return {
        "has_conflicts": report.has_conflicts,
        "collisions": [_serialize_zip_collision(c) for c in report.collisions],
    }


def _serialize_zip_decision(decision: ZipIngestDecision) -> dict[str, Any]:
    return {
        "status": decision.status,
        "reason": decision.reason,
        "zip_root": _serialize_zip_node(decision.zip_root)
        if decision.zip_root
        else None,
        "collisions": (
            _serialize_zip_collision_report(decision.collisions)
            if decision.collisions
            else None
        ),
    }


# =====================================================
# ERROR MAPPING
# =====================================================


def _map_vfs_error(exc: Exception) -> ArvisRuntimeError:
    if isinstance(exc, VFSItemNotFoundError):
        return _vfs_error(code="vfs_item_not_found", message=str(exc), exc=exc)
    if isinstance(exc, VFSParentNotFoundError):
        return _vfs_error(code="vfs_parent_not_found", message=str(exc), exc=exc)
    if isinstance(exc, VFSParentNotFolderError):
        return _vfs_error(code="vfs_parent_not_folder", message=str(exc), exc=exc)
    if isinstance(exc, VFSNameConflictError):
        return _vfs_error(code="vfs_name_conflict", message=str(exc), exc=exc)
    if isinstance(exc, VFSFolderNotEmptyError):
        return _vfs_error(code="vfs_folder_not_empty", message=str(exc), exc=exc)
    if isinstance(exc, VFSCycleError):
        return _vfs_error(code="vfs_cycle_error", message=str(exc), exc=exc)
    if isinstance(exc, VFSInvalidNameError):
        return _vfs_error(code="vfs_invalid_name", message=str(exc), exc=exc)
    return _vfs_error(code="vfs_unknown_error", message=str(exc), exc=exc)


def _map_zip_error(exc: Exception) -> ArvisRuntimeError:
    if isinstance(exc, ZipRejectedError):
        return _vfs_error(code="zip_rejected", message=str(exc), exc=exc)

    if isinstance(exc, ZipConflictError):
        return _vfs_error(code="zip_conflict", message=str(exc), exc=exc)

    return _vfs_error(code="zip_unknown_error", message=str(exc), exc=exc)


VFS_EXPECTED_ERRORS = (
    VFSItemNotFoundError,
    VFSParentNotFoundError,
    VFSParentNotFolderError,
    VFSNameConflictError,
    VFSFolderNotEmptyError,
    VFSCycleError,
    VFSInvalidNameError,
)


ZIP_EXPECTED_ERRORS = (
    ZipRejectedError,
    ZipConflictError,
)


# =====================================================
# VFS SYSCALLS
# =====================================================


@register_syscall(
    "vfs.list",
    effect=SyscallEffect.READ,
    summary="List the items in the user's governed VFS scope.",
    access=_scope_owner_resolver(SyscallEffect.READ, "vfs.list"),
)
def vfs_list(handler: SyscallHandlerLike, user_id: str, **_: Any) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    items = vfs.list_items(user_id)
    return SyscallResult(success=True, result=[_serialize_vfs_item(i) for i in items])


@register_syscall(
    "vfs.get",
    effect=SyscallEffect.READ,
    summary="Read metadata for a single VFS item.",
    access=_item_owner_resolver(SyscallEffect.READ, "vfs.get", id_arg="item_id"),
)
def vfs_get(
    handler: SyscallHandlerLike, user_id: str, item_id: str, **_: Any
) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    try:
        item = vfs.get_item(user_id=user_id, item_id=item_id)
    except VFS_EXPECTED_ERRORS as exc:
        return SyscallResult.failure(_map_vfs_error(exc))
    except Exception as exc:
        return SyscallResult.failure(
            SyscallBoundaryViolationError(
                "Unexpected VFS syscall boundary error",
                details={
                    "syscall": "vfs.get",
                    "subsystem": "kernel.syscall.vfs",
                    "retry_class": "unknown",
                    "exception_type": type(exc).__name__,
                },
                cause=cause_from_exception(exc),
            )
        )

    return SyscallResult(success=True, result=_serialize_vfs_item(item))


@register_syscall(
    "vfs.tree",
    effect=SyscallEffect.READ,
    summary="Return the user's VFS as a tree projection.",
    access=_scope_owner_resolver(SyscallEffect.READ, "vfs.tree"),
)
def vfs_tree(handler: SyscallHandlerLike, user_id: str, **_: Any) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    tree = build_vfs_tree(vfs.list_items(user_id))
    return SyscallResult(success=True, result=_serialize_tree(tree))


@register_syscall(
    "vfs.create_folder",
    effect=SyscallEffect.EFFECT,
    summary="Create a folder in the governed VFS.",
    access=_item_owner_resolver(
        SyscallEffect.EFFECT, "vfs.create_folder", id_arg="parent_id"
    ),
)
def vfs_create_folder(
    handler: SyscallHandlerLike,
    user_id: str,
    name: str,
    parent_id: str | None = None,
    **_: Any,
) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    try:
        item = vfs.create_folder(user_id=user_id, name=name, parent_id=parent_id)
    except VFS_EXPECTED_ERRORS as exc:
        return SyscallResult.failure(_map_vfs_error(exc))
    except Exception as exc:
        return SyscallResult.failure(
            SyscallBoundaryViolationError(
                "Unexpected VFS syscall boundary error",
                details={
                    "syscall": "vfs.create.folder",
                    "subsystem": "kernel.syscall.vfs",
                    "retry_class": "unknown",
                    "exception_type": type(exc).__name__,
                },
                cause=cause_from_exception(exc),
            )
        )

    return SyscallResult(success=True, result=_serialize_vfs_item(item))


@register_syscall(
    "vfs.create_file",
    effect=SyscallEffect.EFFECT,
    summary="Create a logical file entry in the governed VFS.",
    access=_item_owner_resolver(
        SyscallEffect.EFFECT, "vfs.create_file", id_arg="parent_id"
    ),
)
def vfs_create_file(
    handler: SyscallHandlerLike,
    user_id: str,
    name: str,
    parent_id: str | None = None,
    size: int | None = None,
    mime: str | None = None,
    **_: Any,
) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    try:
        item = vfs.create_file_item(
            user_id=user_id,
            name=name,
            parent_id=parent_id,
            size=size,
            mime=mime,
        )
    except VFS_EXPECTED_ERRORS as exc:
        return SyscallResult.failure(_map_vfs_error(exc))
    except Exception as exc:
        return SyscallResult.failure(
            SyscallBoundaryViolationError(
                "Unexpected VFS syscall boundary error",
                details={
                    "syscall": "vfs.create.file",
                    "subsystem": "kernel.syscall.vfs",
                    "retry_class": "unknown",
                    "exception_type": type(exc).__name__,
                },
                cause=cause_from_exception(exc),
            )
        )

    return SyscallResult(success=True, result=_serialize_vfs_item(item))


@register_syscall(
    "vfs.delete_item",
    effect=SyscallEffect.EFFECT,
    summary="Delete a VFS item.",
    access=_item_owner_resolver(
        SyscallEffect.EFFECT, "vfs.delete_item", id_arg="item_id"
    ),
)
def vfs_delete_item(
    handler: SyscallHandlerLike,
    user_id: str,
    item_id: str,
    **_: Any,
) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    try:
        vfs.delete_item(user_id=user_id, item_id=item_id)
    except VFS_EXPECTED_ERRORS as exc:
        return SyscallResult.failure(_map_vfs_error(exc))
    except Exception as exc:
        return SyscallResult.failure(
            SyscallBoundaryViolationError(
                "Unexpected VFS syscall boundary error",
                details={
                    "syscall": "vfs.delete.item",
                    "subsystem": "kernel.syscall.vfs",
                    "retry_class": "unknown",
                    "exception_type": type(exc).__name__,
                },
                cause=cause_from_exception(exc),
            )
        )

    return SyscallResult(success=True, result={"deleted": True, "item_id": item_id})


@register_syscall(
    "vfs.rename_item",
    effect=SyscallEffect.EFFECT,
    summary="Rename a VFS item.",
    access=_item_owner_resolver(
        SyscallEffect.EFFECT, "vfs.rename_item", id_arg="item_id"
    ),
)
def vfs_rename_item(
    handler: SyscallHandlerLike,
    user_id: str,
    item_id: str,
    new_name: str,
    **_: Any,
) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    try:
        item = vfs.rename_item(user_id=user_id, item_id=item_id, new_name=new_name)
    except VFS_EXPECTED_ERRORS as exc:
        return SyscallResult.failure(_map_vfs_error(exc))
    except Exception as exc:
        return SyscallResult.failure(
            SyscallBoundaryViolationError(
                "Unexpected VFS syscall boundary error",
                details={
                    "syscall": "vfs.rename.item",
                    "subsystem": "kernel.syscall.vfs",
                    "retry_class": "unknown",
                    "exception_type": type(exc).__name__,
                },
                cause=cause_from_exception(exc),
            )
        )

    return SyscallResult(success=True, result=_serialize_vfs_item(item))


@register_syscall(
    "vfs.move_item",
    effect=SyscallEffect.EFFECT,
    summary="Move a VFS item to another parent.",
    access=_item_owner_resolver(
        SyscallEffect.EFFECT, "vfs.move_item", id_arg="item_id"
    ),
)
def vfs_move_item(
    handler: SyscallHandlerLike,
    user_id: str,
    item_id: str,
    parent_id: str | None = None,
    **_: Any,
) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    try:
        item = vfs.move_item(user_id=user_id, item_id=item_id, parent_id=parent_id)
    except VFS_EXPECTED_ERRORS as exc:
        return SyscallResult.failure(_map_vfs_error(exc))
    except Exception as exc:
        return SyscallResult.failure(
            SyscallBoundaryViolationError(
                "Unexpected VFS syscall boundary error",
                details={
                    "syscall": "vfs.move.item",
                    "subsystem": "kernel.syscall.vfs",
                    "retry_class": "unknown",
                    "exception_type": type(exc).__name__,
                },
                cause=cause_from_exception(exc),
            )
        )

    return SyscallResult(success=True, result=_serialize_vfs_item(item))


# =====================================================
# ZIP SYSCALLS
# =====================================================


@register_syscall(
    "vfs.zip.analyze",
    effect=SyscallEffect.READ,
    summary="Analyze a zip archive without modifying the VFS.",
    access=_item_owner_resolver(
        SyscallEffect.READ, "vfs.zip.analyze", id_arg="target_parent_id"
    ),
)
def vfs_zip_analyze(
    handler: SyscallHandlerLike,
    zip_path: str,
    user_id: str,
    target_parent_id: str | None = None,
    **_: Any,
) -> SyscallResult:
    zip_service = _get_zip(handler)
    if zip_service is None:
        return _missing_service_error("no_zip_ingest_service")

    decision = zip_service.analyze_and_validate(
        zip_path=zip_path,
        user_id=user_id,
        target_parent_id=target_parent_id,
    )

    return SyscallResult(success=True, result=_serialize_zip_decision(decision))


@register_syscall(
    "vfs.zip.execute",
    effect=SyscallEffect.EFFECT,
    summary="Execute a planned zip import into the VFS.",
    access=_item_owner_resolver(
        SyscallEffect.EFFECT, "vfs.zip.execute", id_arg="target_parent_id"
    ),
)
def vfs_zip_execute(
    handler: SyscallHandlerLike,
    zip_path: str,
    user_id: str,
    target_parent_id: str | None = None,
    keep_zip: bool = False,
    plan: ZipImportPlan | None = None,
    **_: Any,
) -> SyscallResult:
    zip_service = _get_zip(handler)
    if zip_service is None:
        return _missing_service_error("no_zip_ingest_service")

    try:
        result = zip_service.execute_from_path(
            zip_path=zip_path,
            user_id=user_id,
            target_parent_id=target_parent_id,
            keep_zip=keep_zip,
            plan=plan,
        )
    except ZIP_EXPECTED_ERRORS as exc:
        return SyscallResult.failure(_map_zip_error(exc))
    except Exception as exc:
        return SyscallResult.failure(
            SyscallBoundaryViolationError(
                "Unexpected ZIP syscall boundary error",
                details={
                    "syscall": "vfs.zip.execute",
                    "subsystem": "kernel.syscall.vfs.zip",
                    "retry_class": "unknown",
                    "exception_type": type(exc).__name__,
                },
                cause=cause_from_exception(exc),
            )
        )

    return SyscallResult(success=True, result=result)


def _deserialize_zip_node(data: dict[str, Any]) -> ZipNode:
    return ZipNode(
        name=data["name"],
        node_type=data["node_type"],
        size=data.get("size"),
        extension=data.get("extension"),
        supported=data.get("supported", True),
        reason=data.get("reason"),
        zip_path=data.get("zip_path"),
        children=[_deserialize_zip_node(child) for child in data.get("children", [])],
    )


def _deserialize_zip_plan(data: dict[str, Any]) -> ZipImportPlan:
    return ZipImportPlan(entries=data.get("entries", []))


# =====================================================
# ZIP PLAN SYSCALL
# =====================================================


@register_syscall(
    "vfs.zip.plan",
    effect=SyscallEffect.READ,
    summary="Compute a zip import plan without modifying the VFS.",
)
def vfs_zip_plan(
    handler: SyscallHandlerLike,
    zip_root: dict[str, Any],
    plan: dict[str, Any],
    **_: Any,
) -> SyscallResult:
    zip_service = _get_zip(handler)
    if zip_service is None:
        return _missing_service_error("no_zip_ingest_service")

    try:
        root = _deserialize_zip_node(zip_root)
        plan_obj = _deserialize_zip_plan(plan)

        planned_root = zip_service.planner.apply_plan(
            zip_root=root,
            plan=plan_obj,
        )

    except ZIP_EXPECTED_ERRORS as exc:
        return SyscallResult.failure(_map_zip_error(exc))
    except Exception as exc:
        return SyscallResult.failure(
            SyscallBoundaryViolationError(
                "Unexpected ZIP syscall boundary error",
                details={
                    "syscall": "vfs.zip.plan",
                    "subsystem": "kernel.syscall.vfs.zip",
                    "retry_class": "unknown",
                    "exception_type": type(exc).__name__,
                },
                cause=cause_from_exception(exc),
            )
        )

    return SyscallResult(
        success=True,
        result=_serialize_zip_node(planned_root),
    )
