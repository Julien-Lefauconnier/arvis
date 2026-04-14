# arvis/kernel_core/syscalls/syscalls/vfs_syscalls.py

# arvis/kernel_core/syscalls/syscalls/vfs_syscalls.py

from __future__ import annotations

from typing import Any, Optional, Protocol

from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import register_syscall
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry

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

def _get_vfs(handler: SyscallHandlerLike) -> Optional[VFSService]:
    return handler.services.vfs_service


def _get_zip(handler: SyscallHandlerLike) -> Optional[ZipIngestService]:
    return handler.services.zip_ingest_service


def _missing_service_error(service_name: str) -> SyscallResult:
    return SyscallResult(success=False, error=service_name)


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
        "zip_root": _serialize_zip_node(decision.zip_root) if decision.zip_root else None,
        "collisions": (
            _serialize_zip_collision_report(decision.collisions)
            if decision.collisions
            else None
        ),
    }


# =====================================================
# ERROR MAPPING
# =====================================================

def _map_vfs_error(exc: Exception) -> str:
    if isinstance(exc, VFSItemNotFoundError):
        return "vfs_item_not_found"
    if isinstance(exc, VFSParentNotFoundError):
        return "vfs_parent_not_found"
    if isinstance(exc, VFSParentNotFolderError):
        return "vfs_parent_not_folder"
    if isinstance(exc, VFSNameConflictError):
        return "vfs_name_conflict"
    if isinstance(exc, VFSFolderNotEmptyError):
        return "vfs_folder_not_empty"
    if isinstance(exc, VFSCycleError):
        return "vfs_cycle_error"
    if isinstance(exc, VFSInvalidNameError):
        return "vfs_invalid_name"
    return f"{type(exc).__name__}:{str(exc)}"


def _map_zip_error(exc: Exception) -> str:
    if isinstance(exc, ZipRejectedError):
        return "zip_rejected"
    if isinstance(exc, ZipConflictError):
        return "zip_conflict"
    return f"{type(exc).__name__}:{str(exc)}"


# =====================================================
# VFS SYSCALLS
# =====================================================

@register_syscall("vfs.list")
def vfs_list(handler: SyscallHandlerLike, user_id: str, **_: Any) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    items = vfs.list_items(user_id)
    return SyscallResult(success=True, result=[_serialize_vfs_item(i) for i in items])


@register_syscall("vfs.get")
def vfs_get(handler: SyscallHandlerLike, user_id: str, item_id: str, **_: Any) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    try:
        item = vfs.get_item(user_id=user_id, item_id=item_id)
    except Exception as exc:
        return SyscallResult(success=False, error=_map_vfs_error(exc))

    return SyscallResult(success=True, result=_serialize_vfs_item(item))


@register_syscall("vfs.tree")
def vfs_tree(handler: SyscallHandlerLike, user_id: str, **_: Any) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    tree = build_vfs_tree(vfs.list_items(user_id))
    return SyscallResult(success=True, result=_serialize_tree(tree))


@register_syscall("vfs.create_folder")
def vfs_create_folder(
    handler: SyscallHandlerLike,
    user_id: str,
    name: str,
    parent_id: Optional[str] = None,
    **_: Any,
) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    try:
        item = vfs.create_folder(user_id=user_id, name=name, parent_id=parent_id)
    except Exception as exc:
        return SyscallResult(success=False, error=_map_vfs_error(exc))

    return SyscallResult(success=True, result=_serialize_vfs_item(item))


@register_syscall("vfs.create_file")
def vfs_create_file(
    handler: SyscallHandlerLike,
    user_id: str,
    name: str,
    parent_id: Optional[str] = None,
    size: Optional[int] = None,
    mime: Optional[str] = None,
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
    except Exception as exc:
        return SyscallResult(success=False, error=_map_vfs_error(exc))

    return SyscallResult(success=True, result=_serialize_vfs_item(item))


@register_syscall("vfs.delete_item")
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
    except Exception as exc:
        return SyscallResult(success=False, error=_map_vfs_error(exc))

    return SyscallResult(success=True, result={"deleted": True, "item_id": item_id})


@register_syscall("vfs.rename_item")
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
    except Exception as exc:
        return SyscallResult(success=False, error=_map_vfs_error(exc))

    return SyscallResult(success=True, result=_serialize_vfs_item(item))


@register_syscall("vfs.move_item")
def vfs_move_item(
    handler: SyscallHandlerLike,
    user_id: str,
    item_id: str,
    parent_id: Optional[str] = None,
    **_: Any,
) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    try:
        item = vfs.move_item(user_id=user_id, item_id=item_id, parent_id=parent_id)
    except Exception as exc:
        return SyscallResult(success=False, error=_map_vfs_error(exc))

    return SyscallResult(success=True, result=_serialize_vfs_item(item))


# =====================================================
# ZIP SYSCALLS
# =====================================================

@register_syscall("vfs.zip.analyze")
def vfs_zip_analyze(
    handler: SyscallHandlerLike,
    zip_path: str,
    user_id: str,
    target_parent_id: Optional[str] = None,
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


@register_syscall("vfs.zip.execute")
def vfs_zip_execute(
    handler: SyscallHandlerLike,
    zip_path: str,
    user_id: str,
    target_parent_id: Optional[str] = None,
    keep_zip: bool = False,
    plan: Optional[ZipImportPlan] = None,
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
    except Exception as exc:
        return SyscallResult(success=False, error=_map_zip_error(exc))

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
        children=[
            _deserialize_zip_node(child)
            for child in data.get("children", [])
        ],
    )


def _deserialize_zip_plan(data: dict[str, Any]) -> ZipImportPlan:
    return ZipImportPlan(
        entries=data.get("entries", [])
    )


# =====================================================
# ZIP PLAN SYSCALL
# =====================================================

@register_syscall("vfs.zip.plan")
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

    except Exception as exc:
        return SyscallResult(
            success=False,
            error=_map_zip_error(exc),
        )

    return SyscallResult(
        success=True,
        result=_serialize_zip_node(planned_root),
    )