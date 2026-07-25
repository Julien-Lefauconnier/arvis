# arvis/kernel_core/syscalls/syscalls/vfs_syscalls.py

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol

from arvis.errors.base import (
    ArvisRuntimeError,
    ArvisSecurityError,
    ErrorDomain,
)
from arvis.errors.normalization import normalize_error
from arvis.errors.provenance import ErrorOrigin, cause_from_exception
from arvis.errors.syscall import SyscallBoundaryViolationError
from arvis.kernel_core.access.decision import AccessDecision
from arvis.kernel_core.access.identity import principal_from_context
from arvis.kernel_core.access.models import AccessContext, Principal
from arvis.kernel_core.access.policy import (
    ACCESS_DENIED_REASON_CODE,
    AuthorizationPolicy,
)
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import (
    SyscallEffect,
    register_syscall,
)
from arvis.kernel_core.vfs.exceptions import (
    VFSCycleError,
    VFSFolderNotEmptyError,
    VFSInheritanceRollbackError,
    VFSInheritanceViolationError,
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
    authorization_service: AuthorizationPolicy


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

    Two cases are carefully distinguished (audit A-03, fail-closed doctrine):

    - the reference is ABSENT (creation at the root): not an error, the
      caller acts on its own scope, ownership is the caller and the resource
      is genuinely unscoped (resource_scope None, the historical behaviour);
    - the lookup FAILS for any reason: the metadata is INDETERMINATE. The
      exception propagates to ``SyscallHandler``, which emits an
      ``authorization_failure`` refusal and never dispatches the syscall body.
      This includes expected domain errors such as ``VFSItemNotFoundError``:
      absorbing one would allow a second, time-of-check/time-of-use lookup to
      return a different resource after authorization was granted on fabricated
      caller-owned metadata.
    """

    def _resolve(
        args: Mapping[str, Any], services: KernelServiceRegistry
    ) -> AccessContext:
        user_id: str = args["user_id"]
        principal = principal_from_context(args.get("ctx"))
        if principal is None:
            principal = Principal(user_id=user_id)
        reference = args.get(id_arg)
        # Absent reference: the caller acts on its own scope (root creation).
        owner_id = user_id
        organization_id: str | None = None
        resource_scope: str | None = None

        vfs: VFSService | None = services.vfs_service
        if vfs is not None and isinstance(reference, str):
            # Read the resource to authorize against its real owner,
            # organization and scope. NO lookup exception is absorbed here:
            # expected and unexpected failures both mean the authorization
            # metadata could not be resolved for this operation. The handler
            # converts the propagated exception into a fail-closed
            # authorization_failure, before the body can perform another read.
            item = vfs.get_item(user_id=user_id, item_id=reference)
            owner_id = item.owner_id
            organization_id = item.organization_id
            resource_scope = item.resource_scope

        return AccessContext(
            principal=principal,
            effect=effect,
            resource_owner_id=owner_id,
            resource_organization_id=organization_id,
            resource_id=reference if isinstance(reference, str) else None,
            resource_scope=resource_scope,
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


def _visible_items(
    handler: SyscallHandlerLike,
    args: Mapping[str, Any],
    items: list[VFSItem],
    *,
    syscall_name: str,
) -> list[VFSItem]:
    """Keep only the items the caller may access under the full policy.

    Collection syscalls (vfs.list, vfs.tree) authorize the caller's own scope
    at the syscall boundary, but the store may return items in scopes or
    organizations the principal is not cleared for. Each returned item must
    therefore satisfy the SAME policy vfs.get applies to a single item (audit
    A-04): its owner, organization and resource_scope are evaluated, and only
    ALLOW items survive. A metadata error on one item excludes that item, and
    never widens the result.

    ``syscall_name`` is the REAL calling syscall (vfs.list or vfs.tree), passed
    verbatim into each item's AccessContext (counter-audit B3-VFS-03). A host
    policy that derives a distinct capability per syscall, list_read versus
    tree_read, then judges each item under the operation actually performed;
    hardcoding one name would let one operation borrow the other's capability.
    The tree projection can reveal more structure than a flat list, so a host
    may legitimately govern them apart.

    The scopeless, owner-scoped items keep their historical behaviour: under
    the reference policies a caller acting on its own scope owns them, so they
    are covered.
    """
    policy = handler.authorization_service
    principal = principal_from_context(args.get("ctx"))
    if principal is None:
        principal = Principal(user_id=args["user_id"])

    visible: list[VFSItem] = []
    for item in items:
        context = AccessContext(
            principal=principal,
            effect=SyscallEffect.READ,
            resource_owner_id=item.owner_id,
            resource_organization_id=item.organization_id,
            resource_id=item.item_id,
            resource_scope=item.resource_scope,
            syscall_name=syscall_name,
        )
        try:
            verdict = policy.decide(context)
        except Exception:  # arvis-broad: an item that cannot be judged is hidden
            continue
        if verdict.decision is AccessDecision.ALLOW:
            visible.append(item)
    return visible


def _deny(syscall_name: str, reason_code: str, message: str) -> SyscallResult:
    """Build a governed access denial from a syscall body (audit A-05/A-06).

    Mirrors the handler's own access-denied failure so a refusal raised
    inside a body (a destination check, a parent mismatch) is reported like
    any authorization denial, with no partial mutation having occurred."""
    return SyscallResult.failure(
        ArvisSecurityError(
            message,
            origin=ErrorOrigin(
                component="vfs_syscall",
                subsystem="kernel.syscall.vfs",
                syscall=syscall_name,
            ),
            details={"syscall": syscall_name, "reason_code": reason_code},
        )
    )


def _may_write_to(
    handler: SyscallHandlerLike,
    args: Mapping[str, Any],
    parent: VFSItem,
) -> bool:
    """Whether the caller may WRITE into this parent, under the full policy.

    The move source is governed by the resolver (id_arg=item_id); the
    DESTINATION parent must be governed too (audit A-05). This asks the same
    policy the same question it answers for the source, for a write effect."""
    policy = handler.authorization_service
    principal = principal_from_context(args.get("ctx"))
    if principal is None:
        principal = Principal(user_id=args["user_id"])
    context = AccessContext(
        principal=principal,
        effect=SyscallEffect.EFFECT,
        resource_owner_id=parent.owner_id,
        resource_organization_id=parent.organization_id,
        resource_id=parent.item_id,
        resource_scope=parent.resource_scope,
        syscall_name="vfs.move_item",
    )
    try:
        verdict = policy.decide(context)
    except Exception:  # arvis-broad: an unjudgeable destination is refused
        return False
    return verdict.decision is AccessDecision.ALLOW


def _same_governed_area(source: VFSItem, parent: VFSItem) -> bool:
    """Whether source and destination parent share organization AND scope.

    Comparison is by OPAQUE EQUALITY of the tokens; arvis never parses a
    scope. A plain move stays inside one governed area (audit A-05): a
    cross-scope or cross-organization move is not an ordinary move and is
    refused here (a dedicated, explicitly governed transfer would be a
    separate future capability)."""
    return (
        source.organization_id == parent.organization_id
        and source.resource_scope == parent.resource_scope
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
def vfs_list(handler: SyscallHandlerLike, user_id: str, **kwargs: Any) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    items = _visible_items(
        handler,
        {"user_id": user_id, **kwargs},
        vfs.list_items(user_id),
        syscall_name="vfs.list",
    )
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
def vfs_tree(handler: SyscallHandlerLike, user_id: str, **kwargs: Any) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    # Filter the flat item list BEFORE building the tree, so no forbidden node
    # is ever materialized. A covered item whose parent is filtered out
    # surfaces as a root (its own coverage stands); the forbidden parent is
    # never revealed (audit A-04).
    visible = _visible_items(
        handler,
        {"user_id": user_id, **kwargs},
        vfs.list_items(user_id),
        syscall_name="vfs.tree",
    )
    tree = build_vfs_tree(visible)
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

    # Creation inheritance (the child carries the parent's organization and
    # scope) is derived, imposed and verified inside VFSService, the common
    # boundary of every creation path (audit A-06, counter-audit B3-VFS-02).
    # An inheritance violation surfaces as a fail-closed security refusal.
    try:
        item = vfs.create_folder(user_id=user_id, name=name, parent_id=parent_id)
    except VFSInheritanceRollbackError:
        return _deny(
            "vfs.create_folder",
            "inheritance_rollback_failed",
            "create refused: the repository persisted an item with invalid "
            "inheritance and could not prove its rollback",
        )
    except VFSInheritanceViolationError:
        return _deny(
            "vfs.create_folder",
            "inheritance_violation",
            "create refused: the created item does not carry the parent's "
            "organization and scope",
        )
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

    # Creation inheritance is derived, imposed and verified inside VFSService
    # (audit A-06, counter-audit B3-VFS-02). An inheritance violation surfaces
    # as a fail-closed security refusal.
    try:
        item = vfs.create_file_item(
            user_id=user_id,
            name=name,
            parent_id=parent_id,
            size=size,
            mime=mime,
        )
    except VFSInheritanceRollbackError:
        return _deny(
            "vfs.create_file",
            "inheritance_rollback_failed",
            "create refused: the repository persisted an item with invalid "
            "inheritance and could not prove its rollback",
        )
    except VFSInheritanceViolationError:
        return _deny(
            "vfs.create_file",
            "inheritance_violation",
            "create refused: the created item does not carry the parent's "
            "organization and scope",
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
    **kwargs: Any,
) -> SyscallResult:
    vfs = _get_vfs(handler)
    if vfs is None:
        return _missing_service_error("no_vfs_service")

    # Govern BOTH sides of the move (audit A-05). The resolver already
    # governed the source (id_arg=item_id). Here, before any mutation, read
    # the source and the destination parent and refuse a move that leaves the
    # source's governed area or writes into a parent the caller may not write.
    # All refusals happen BEFORE vfs.move_item, so no partial mutation occurs.
    args = {"user_id": user_id, "ctx": kwargs.get("ctx")}
    try:
        source = vfs.get_item(user_id=user_id, item_id=item_id)
    except VFS_EXPECTED_ERRORS as exc:
        return SyscallResult.failure(_map_vfs_error(exc))
    except Exception:  # arvis-broad: source indeterminate, refuse the move
        return _deny(
            "vfs.move_item",
            "move_source_unresolved",
            "move refused: the source item could not be resolved",
        )

    if parent_id is not None:
        try:
            parent = vfs.get_item(user_id=user_id, item_id=parent_id)
        except VFS_EXPECTED_ERRORS as exc:
            return SyscallResult.failure(_map_vfs_error(exc))
        except Exception:  # arvis-broad: destination indeterminate, refuse
            return _deny(
                "vfs.move_item",
                "move_destination_unresolved",
                "move refused: the destination parent could not be resolved",
            )
        if not _may_write_to(handler, args, parent):
            return _deny(
                "vfs.move_item",
                ACCESS_DENIED_REASON_CODE,
                "move refused: no write access to the destination parent",
            )
        if not _same_governed_area(source, parent):
            return _deny(
                "vfs.move_item",
                "cross_scope_move_refused",
                "move refused: source and destination differ in organization "
                "or scope; a cross-scope move is not an ordinary move",
            )
    else:
        # Move to the root: there is no parent to inherit from, so a SCOPED
        # source would silently lose its restriction at the root. Refuse it;
        # only an unscoped source may sit at the root (audit A-05, A-02).
        if source.resource_scope is not None or source.organization_id is not None:
            return _deny(
                "vfs.move_item",
                "cross_scope_move_refused",
                "move refused: a scoped item cannot be moved to the "
                "unscoped root by an ordinary move",
            )

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
