# tests/kernel_core/access/test_vfs_scope_adversarial_unit.py

"""Adversarial suite for the VFS resource_scope security property (0.1.0b3).

Lot 0 of the corrective campaign: these tests FREEZE the eight findings of
the external audit (A-01..A-06) as RED tests. Written before any fix, they
must fail on the post-lot state and pass one by one as the campaign closes
each finding. A green-from-the-start test would prove nothing; each test
here targets a concrete gap the passing gate did not see.

Test IDs map to audit findings:
  A-01  positional constructor drift of VFSItem
  A-02  scope lost after rename / after move
  A-03  fail-open resolver on lookup error
  A-04  leak through vfs.list / vfs.tree
  A-05  move across scopes accepted
  A-06  creation not inheriting the parent scope
"""

from types import SimpleNamespace

import pytest

from arvis.kernel_core.access.models import Principal
from arvis.kernel_core.access.policy import (
    CAPABILITY_READ,
    OrganizationScopedAuthorization,
)
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.kernel_core.vfs.models import VFSItem
from arvis.kernel_core.vfs.repositories.in_memory import InMemoryVFSRepository
from arvis.kernel_core.vfs.service import VFSService

# ---------------------------------------------------------------------------
# A-01: positional constructor drift
# ---------------------------------------------------------------------------


def test_a01_positional_constructor_is_backward_compatible():
    """An item built with the 0.1.0b2 positional signature (no scope) must
    produce exactly the object it did then: mime/file_size/created_at land
    in their own fields, and resource_scope stays None. With the field
    inserted mid-order, the positional mime value lands in resource_scope."""
    item = VFSItem(
        "id-1",  # item_id
        "probe.txt",  # display_name
        "file",  # item_type
        None,  # parent_id
        "alice",  # owner_id
        "acme",  # organization_id
        "text/plain",  # historically: mime
        123,  # historically: file_size
        456,  # historically: created_at
    )
    assert item.mime == "text/plain"
    assert item.file_size == 123
    assert item.created_at == 456
    assert item.resource_scope is None


# ---------------------------------------------------------------------------
# A-02: scope lost after mutation
# ---------------------------------------------------------------------------


def _repo_with_scoped_item() -> tuple[InMemoryVFSRepository, str]:
    repo = InMemoryVFSRepository()
    item_id = repo.create_file_item(
        user_id="alice", name="f.txt", parent_id=None, size=10, mime="text/plain"
    )
    # Stamp a scope on the stored item (the host will set it via the payload).
    bucket = repo._user_bucket("alice")
    stored = bucket[item_id]
    bucket[item_id] = VFSItem(
        item_id=stored.item_id,
        display_name=stored.display_name,
        item_type=stored.item_type,
        parent_id=stored.parent_id,
        owner_id=stored.owner_id,
        organization_id="acme",
        resource_scope="scope:A",
        mime=stored.mime,
        file_size=stored.file_size,
        created_at=stored.created_at,
    )
    return repo, item_id


def test_a02_rename_preserves_resource_scope():
    repo, item_id = _repo_with_scoped_item()
    repo.rename_item(user_id="alice", item_id=item_id, new_name="renamed.txt")
    after = repo._user_bucket("alice")[item_id]
    assert after.display_name == "renamed.txt"
    assert after.resource_scope == "scope:A"
    assert after.organization_id == "acme"


def test_a02_move_preserves_resource_scope():
    repo, item_id = _repo_with_scoped_item()
    parent = repo.create_folder(user_id="alice", name="dest", parent_id=None)
    repo.move_item(user_id="alice", item_id=item_id, parent_id=parent)
    after = repo._user_bucket("alice")[item_id]
    assert after.parent_id == parent
    assert after.resource_scope == "scope:A"
    assert after.organization_id == "acme"


# ---------------------------------------------------------------------------
# A-03: fail-open resolver on lookup error
# ---------------------------------------------------------------------------


class _FailingLookupVFS:
    """A VFS whose get_item raises: an unavailable or inconsistent store.

    The resolver must treat unresolvable metadata as a denial, never as a
    scopeless, caller-owned (covered) resource."""

    def get_item(self, *, user_id: str, item_id: str) -> VFSItem:
        raise RuntimeError("transient store failure")


def test_a03_resolver_lookup_error_denies_end_to_end():
    """A lookup failure must NOT authorize. The end-to-end invariant (audit
    A-03: verify the final syscall result, not the resolver in isolation):
    when the metadata cannot be resolved, vfs.get must deny, never return the
    resource as if it were caller-owned and unscoped. Today the resolver
    swallows the error, pins ownership to the caller and the scope to None,
    which grants; this asserts the denial."""
    services = KernelServiceRegistry(
        vfs_service=_FailingLookupVFS(),
        authorization_service=OrganizationScopedAuthorization(),
    )
    handler = SyscallHandler(runtime_state=None, scheduler=None, services=services)
    # A principal that is NOT the resource owner under any correct resolution.
    ctx = SimpleNamespace(extra={}, principal=Principal(user_id="bob"))

    result = handler.handle(
        Syscall(name="vfs.get", args={"ctx": ctx, "user_id": "bob", "item_id": "i1"})
    )

    assert result.success is False, (
        "a lookup failure was turned into a granted, unrestricted access"
    )


class _ExplodingVFS:
    """Every VFS access raises an UNEXPECTED error (store unavailable).

    Used to lock the doctrine-A invariant: the resolver stays neutral on an
    indeterminate lookup and the syscall BODY, calling the same failing VFS,
    returns a failure. No item-referencing syscall may report success."""

    def get_item(self, *, user_id: str, item_id: str) -> VFSItem:
        raise RuntimeError("store unavailable")

    def list_items(self, user_id: str) -> list[VFSItem]:
        raise RuntimeError("store unavailable")

    def create_folder(self, *, user_id, name, parent_id):
        raise RuntimeError("store unavailable")

    def create_file_item(self, *, user_id, name, parent_id, size, mime=None):
        raise RuntimeError("store unavailable")

    def rename_item(self, *, user_id, item_id, new_name):
        raise RuntimeError("store unavailable")

    def move_item(self, *, user_id, item_id, parent_id):
        raise RuntimeError("store unavailable")

    def delete_item(self, *, user_id, item_id):
        raise RuntimeError("store unavailable")


@pytest.mark.parametrize(
    ("syscall_name", "extra_args"),
    [
        ("vfs.get", {"item_id": "i1"}),
        ("vfs.create_folder", {"name": "f", "parent_id": "p1"}),
        ("vfs.create_file", {"name": "f.txt", "parent_id": "p1", "size": 1}),
        ("vfs.rename_item", {"item_id": "i1", "new_name": "x"}),
        ("vfs.move_item", {"item_id": "i1", "parent_id": "p1"}),
        ("vfs.delete_item", {"item_id": "i1"}),
    ],
)
def test_a03_no_vfs_syscall_grants_on_indeterminate_lookup(syscall_name, extra_args):
    """Doctrine-A lock (audit A-03): when the resolver's metadata lookup is
    indeterminate, NO item-referencing VFS syscall may return success. The
    resolver never fabricates a grantable resolution from an error, and the
    body fails on the same unavailable store. A future syscall that authorized
    without re-reading, and so could succeed here, would break this and be
    caught."""
    services = KernelServiceRegistry(
        vfs_service=_ExplodingVFS(),
        authorization_service=OrganizationScopedAuthorization(),
    )
    handler = SyscallHandler(runtime_state=None, scheduler=None, services=services)
    ctx = SimpleNamespace(extra={}, principal=Principal(user_id="bob"))

    result = handler.handle(
        Syscall(
            name=syscall_name,
            args={"ctx": ctx, "user_id": "bob", **extra_args},
        )
    )

    assert result.success is False, f"{syscall_name} granted on an indeterminate lookup"


# ---------------------------------------------------------------------------
# A-04: leak through vfs.list / vfs.tree
# ---------------------------------------------------------------------------


class _TwoScopeVFS:
    """A VFS holding one item in scope:A and one in scope:B for the caller.

    Stands in for a store whose listing returns items the principal is not
    cleared for; the syscall must filter them out."""

    def __init__(self) -> None:
        self._items = [
            VFSItem(
                item_id="a1",
                display_name="covered.txt",
                item_type="file",
                parent_id=None,
                owner_id="caller",
                organization_id="acme",
                resource_scope="scope:A",
            ),
            VFSItem(
                item_id="b1",
                display_name="secret.txt",
                item_type="file",
                parent_id=None,
                owner_id="caller",
                organization_id="acme",
                resource_scope="scope:B",
            ),
        ]

    def list_items(self, user_id: str) -> list[VFSItem]:
        return list(self._items)

    def get_item(self, *, user_id: str, item_id: str) -> VFSItem:
        for it in self._items:
            if it.item_id == item_id:
                return it
        raise KeyError(item_id)


def _covers_scope_A(principal: Principal, resource_scope: str | None) -> bool:
    """Host rule for the test: the caller is cleared for scope:A only."""
    if resource_scope is None:
        return True
    return resource_scope == "scope:A"


def _list_handler() -> tuple[SyscallHandler, SimpleNamespace]:
    services = KernelServiceRegistry(
        vfs_service=_TwoScopeVFS(),
        authorization_service=OrganizationScopedAuthorization(
            scope_covers=_covers_scope_A
        ),
    )
    handler = SyscallHandler(runtime_state=None, scheduler=None, services=services)
    member = Principal(
        user_id="caller",
        organization_id="acme",
        grants=frozenset({CAPABILITY_READ}),
    )
    ctx = SimpleNamespace(extra={}, principal=member)
    return handler, ctx


def test_a04_list_does_not_leak_uncovered_item():
    handler, ctx = _list_handler()
    result = handler.handle(
        Syscall(name="vfs.list", args={"ctx": ctx, "user_id": "caller"})
    )
    assert result.success is True
    ids = {entry["item_id"] for entry in result.result}
    assert "a1" in ids
    assert "b1" not in ids, "vfs.list leaked an item in an uncovered scope"


def test_a04_tree_does_not_leak_uncovered_item():
    handler, ctx = _list_handler()
    result = handler.handle(
        Syscall(name="vfs.tree", args={"ctx": ctx, "user_id": "caller"})
    )
    assert result.success is True
    flat = str(result.result)
    assert "b1" not in flat, "vfs.tree leaked an item in an uncovered scope"


# ---------------------------------------------------------------------------
# A-05: move across scopes accepted
# ---------------------------------------------------------------------------


def test_a05_move_across_scopes_is_denied():
    """Moving an item from scope:A into a scope:B parent, with a principal
    cleared for scope:A only, must be denied without mutation. Today move
    governs only the source, so the cross-scope move is accepted."""
    repo = InMemoryVFSRepository()
    src_id = repo.create_file_item(
        user_id="caller", name="f.txt", parent_id=None, size=1, mime="text/plain"
    )
    dest_parent = repo.create_folder(user_id="caller", name="dest", parent_id=None)
    b = repo._user_bucket("caller")
    b[src_id] = VFSItem(
        item_id=src_id,
        display_name="f.txt",
        item_type="file",
        parent_id=None,
        owner_id="caller",
        organization_id="acme",
        resource_scope="scope:A",
    )
    b[dest_parent] = VFSItem(
        item_id=dest_parent,
        display_name="dest",
        item_type="folder",
        parent_id=None,
        owner_id="caller",
        organization_id="acme",
        resource_scope="scope:B",
    )

    services = KernelServiceRegistry(
        vfs_service=VFSService(repo),
        authorization_service=OrganizationScopedAuthorization(
            scope_covers=_covers_scope_A
        ),
    )
    handler = SyscallHandler(runtime_state=None, scheduler=None, services=services)
    member = Principal(
        user_id="caller",
        organization_id="acme",
        grants=frozenset({CAPABILITY_READ, "write"}),
    )
    ctx = SimpleNamespace(extra={}, principal=member)

    result = handler.handle(
        Syscall(
            name="vfs.move_item",
            args={
                "ctx": ctx,
                "user_id": "caller",
                "item_id": src_id,
                "parent_id": dest_parent,
            },
        )
    )
    assert result.success is False, "cross-scope move was accepted"
    # And no partial mutation: the item stayed under its original parent.
    assert repo._user_bucket("caller")[src_id].parent_id is None


# ---------------------------------------------------------------------------
# A-06: creation does not inherit the parent scope
# ---------------------------------------------------------------------------


def test_a06_child_inherits_parent_scope():
    """A file created under a scope:A folder must inherit scope:A (and the
    parent's organization). Today creation stamps neither, so the child is
    unscoped and more widely accessible than its parent."""
    repo = InMemoryVFSRepository()
    parent = repo.create_folder(user_id="alice", name="matter7", parent_id=None)
    b = repo._user_bucket("alice")
    b[parent] = VFSItem(
        item_id=parent,
        display_name="matter7",
        item_type="folder",
        parent_id=None,
        owner_id="alice",
        organization_id="acme",
        resource_scope="scope:A",
    )

    services = KernelServiceRegistry(vfs_service=VFSService(repo))
    handler = SyscallHandler(runtime_state=None, scheduler=None, services=services)
    ctx = SimpleNamespace(extra={}, principal=Principal(user_id="alice"))

    result = handler.handle(
        Syscall(
            name="vfs.create_file",
            args={
                "ctx": ctx,
                "user_id": "alice",
                "name": "invoice.pdf",
                "parent_id": parent,
                "size": 10,
                "mime": "application/pdf",
            },
        )
    )
    assert result.success is True
    child_id = result.result["item_id"]
    child = repo._user_bucket("alice")[child_id]
    assert child.resource_scope == "scope:A", "child did not inherit parent scope"
    assert child.organization_id == "acme"
