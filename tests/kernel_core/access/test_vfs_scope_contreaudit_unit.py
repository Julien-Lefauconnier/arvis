# tests/kernel_core/access/test_vfs_scope_contreaudit_unit.py

"""Red reproductions for the 0.1.0b3 counter-audit (B3-VFS-01..03).

Three residual defects the counter-audit reproduced on the b3 candidate:

- B3-VFS-01 (A-03): the resolver swallows a lookup exception and hands the
  policy a caller-owned, unscoped context. Doctrine A assumed the body would
  fail on the same lookup, but the two reads are separate in time (TOCTOU): a
  transient first failure followed by a second success returning a foreign
  resource grants access on fabricated metadata. Fix: let the exception
  propagate; the handler turns it into an authorization_failure refusal and the
  body never runs.
- B3-VFS-02 (A-06): creation inheritance lives in the syscall body, so any
  creation path that bypasses the body (the ZIP importer calling the service
  directly) drops the parent's organization and scope. Fix: centralize
  inheritance in VFSService, the common boundary of every creation path.
- B3-VFS-03 (A-04): _visible_items hardcodes syscall_name="vfs.list", so a
  policy that distinguishes list from tree capabilities judges tree under the
  wrong name. Fix: pass the real syscall_name.
"""

from types import SimpleNamespace

import pytest

from arvis.kernel_core.access.decision import AccessDecision, AccessVerdict
from arvis.kernel_core.access.models import AccessContext, Principal
from arvis.kernel_core.access.policy import (
    ACCESS_DENIED_REASON_CODE,
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
# B3-VFS-01: A-03 TOCTOU, first lookup fails then a second would succeed
# ---------------------------------------------------------------------------


class _FlakyThenForeignVFS:
    """First get_item raises (transient), the second returns a FOREIGN scoped
    resource. Models a proxy/cache/injected-fault store where authorization and
    execution are two reads separated in time."""

    def __init__(self) -> None:
        self.calls = 0

    def get_item(self, *, user_id: str, item_id: str) -> VFSItem:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("transient lookup failure")
        return VFSItem(
            item_id=item_id,
            display_name="secret.txt",
            item_type="file",
            parent_id=None,
            owner_id="someone_else",
            organization_id="acme",
            resource_scope="scope:A",
        )


def test_b3_vfs_01_transient_resolver_failure_denies_before_execution():
    """A lookup failure during authorization must deny definitively; the body
    must not run a second lookup that could succeed and return the resource.
    RED on the b3 candidate: doctrine A swallows the first exception, the body
    reads again, gets the foreign resource and returns it."""
    vfs = _FlakyThenForeignVFS()
    services = KernelServiceRegistry(
        vfs_service=vfs,
        authorization_service=OrganizationScopedAuthorization(),
    )
    handler = SyscallHandler(runtime_state=None, scheduler=None, services=services)
    ctx = SimpleNamespace(extra={}, principal=Principal(user_id="bob"))

    result = handler.handle(
        Syscall(name="vfs.get", args={"ctx": ctx, "user_id": "bob", "item_id": "i1"})
    )

    assert result.success is False, "access granted after an indeterminate lookup"
    assert vfs.calls == 1, "the body performed a second lookup after auth failure"
    assert result.error is not None
    assert result.error.details.get("reason_code") == "authorization_failure"


class _AlwaysFlakyVFS:
    """Every call raises: the transient failure never clears within the
    operation. Used to check the multi-syscall denial and the single-lookup
    property across item-referencing syscalls."""

    def __init__(self) -> None:
        self.calls = 0

    def get_item(self, *, user_id: str, item_id: str) -> VFSItem:
        self.calls += 1
        raise RuntimeError("transient lookup failure")

    def list_items(self, user_id: str) -> list[VFSItem]:
        self.calls += 1
        raise RuntimeError("transient lookup failure")

    def create_folder(self, **kwargs: object) -> VFSItem:
        raise AssertionError("body must not run after an auth failure")

    def create_file_item(self, **kwargs: object) -> VFSItem:
        raise AssertionError("body must not run after an auth failure")

    def rename_item(self, **kwargs: object) -> VFSItem:
        raise AssertionError("body must not run after an auth failure")

    def move_item(self, **kwargs: object) -> VFSItem:
        raise AssertionError("body must not run after an auth failure")

    def delete_item(self, **kwargs: object) -> None:
        raise AssertionError("body must not run after an auth failure")


@pytest.mark.parametrize(
    ("syscall_name", "extra_args"),
    [
        ("vfs.get", {"item_id": "i1"}),
        ("vfs.rename_item", {"item_id": "i1", "new_name": "x"}),
        ("vfs.move_item", {"item_id": "i1", "parent_id": "p1"}),
        ("vfs.delete_item", {"item_id": "i1"}),
    ],
)
def test_b3_vfs_01_indeterminate_lookup_denies_across_syscalls(
    syscall_name, extra_args
):
    """An indeterminate lookup denies for every item-referencing syscall, and
    the resolver's failure means the body never runs (the create/rename/move/
    delete methods assert if called)."""
    vfs = _AlwaysFlakyVFS()
    services = KernelServiceRegistry(
        vfs_service=vfs,
        authorization_service=OrganizationScopedAuthorization(),
    )
    handler = SyscallHandler(runtime_state=None, scheduler=None, services=services)
    ctx = SimpleNamespace(extra={}, principal=Principal(user_id="bob"))

    result = handler.handle(
        Syscall(name=syscall_name, args={"ctx": ctx, "user_id": "bob", **extra_args})
    )

    assert result.success is False, f"{syscall_name} granted on indeterminate lookup"
    assert result.error is not None
    assert result.error.details.get("reason_code") == "authorization_failure"


class _GenuinelyUnscopedVFS:
    """A store that successfully returns a real, owner-owned, unscoped item."""

    def get_item(self, *, user_id: str, item_id: str) -> VFSItem:
        return VFSItem(
            item_id=item_id,
            display_name="own.txt",
            item_type="file",
            parent_id=None,
            owner_id=user_id,
        )


def test_b3_vfs_01_genuinely_unscoped_resource_stays_compatible():
    """A resource actually read with resource_scope=None is NOT an
    indeterminate lookup: it keeps the historical behaviour and the owner may
    read it. The doctrine-B change must not conflate a real None with a lookup
    failure (audit A-03 acceptance)."""
    services = KernelServiceRegistry(
        vfs_service=_GenuinelyUnscopedVFS(),
        authorization_service=OrganizationScopedAuthorization(),
    )
    handler = SyscallHandler(runtime_state=None, scheduler=None, services=services)
    ctx = SimpleNamespace(extra={}, principal=Principal(user_id="owner"))

    result = handler.handle(
        Syscall(name="vfs.get", args={"ctx": ctx, "user_id": "owner", "item_id": "i1"})
    )

    assert result.success is True, "a genuinely unscoped owned resource was denied"


# ---------------------------------------------------------------------------
# B3-VFS-02: A-06 ZIP path (service-level) bypasses inheritance
# ---------------------------------------------------------------------------


def test_b3_vfs_02_service_creation_under_scoped_parent_inherits():
    """Creating through VFSService directly (the path the ZIP importer uses)
    under a scoped parent MUST inherit the parent's organization and scope.
    RED on the b3 candidate: inheritance lives in the syscall body, so a direct
    service call stamps neither."""
    repo = InMemoryVFSRepository()
    parent = repo.create_folder(user_id="alice", name="matter", parent_id=None)
    b = repo._user_bucket("alice")
    b[parent] = VFSItem(
        item_id=parent,
        display_name="matter",
        item_type="folder",
        parent_id=None,
        owner_id="alice",
        organization_id="acme",
        resource_scope="scope:A",
    )
    service = VFSService(repo)

    child = service.create_file_item(
        user_id="alice", name="doc.pdf", parent_id=parent, size=1
    )

    assert child.organization_id == "acme", "child did not inherit parent organization"
    assert child.resource_scope == "scope:A", "child did not inherit parent scope"


# ---------------------------------------------------------------------------
# B3-VFS-03: A-04 tree judged under vfs.list capability
# ---------------------------------------------------------------------------


class _TreeReadOnlyPolicy:
    """Grants only when the context carries the tree capability, derived here
    from syscall_name. A resource judged under the wrong syscall_name is
    refused. Proves _visible_items must pass the real name."""

    def decide(self, context: AccessContext) -> AccessVerdict:
        if context.syscall_name == "vfs.tree":
            return AccessVerdict(AccessDecision.ALLOW)
        return AccessVerdict(AccessDecision.DENY, ACCESS_DENIED_REASON_CODE)


class _OneItemVFS:
    def list_items(self, user_id: str) -> list[VFSItem]:
        return [
            VFSItem(
                item_id="t1",
                display_name="f.txt",
                item_type="file",
                parent_id=None,
                owner_id=user_id,
                organization_id="acme",
                resource_scope="scope:A",
            )
        ]

    def get_item(self, *, user_id: str, item_id: str) -> VFSItem:
        return self.list_items(user_id)[0]


def test_b3_vfs_03_tree_is_judged_under_its_own_syscall_name():
    """vfs.tree must present its own syscall_name to the policy, so a policy
    that distinguishes list from tree judges it correctly. RED on the b3
    candidate: _visible_items hardcodes vfs.list, so a tree-granting policy
    denies the item and the tree comes back empty."""
    services = KernelServiceRegistry(
        vfs_service=_OneItemVFS(),
        authorization_service=_TreeReadOnlyPolicy(),
    )
    handler = SyscallHandler(runtime_state=None, scheduler=None, services=services)
    ctx = SimpleNamespace(
        extra={},
        principal=Principal(
            user_id="u", organization_id="acme", grants=frozenset({CAPABILITY_READ})
        ),
    )

    result = handler.handle(Syscall(name="vfs.tree", args={"ctx": ctx, "user_id": "u"}))

    assert result.success is True
    flat = str(result.result)
    assert "t1" in flat, "tree was judged under the wrong syscall_name and hid the item"


# ---------------------------------------------------------------------------
# B3-VFS-02 acceptance: real ZIP import inherits scope on every descendant
# ---------------------------------------------------------------------------


def test_b3_vfs_02_zip_import_descendants_inherit_scope(tmp_path, monkeypatch):
    """A real ZIP imported under a scoped parent stamps the parent's
    organization and scope on EVERY descendant, nested folders and files
    alike. The ZipExecutor calls VFSService, which centralizes inheritance, so
    the fix needs no ZIP-specific code (counter-audit B3-VFS-02)."""
    import zipfile

    from arvis.kernel_core.vfs.zip.analyzer import ZipAnalyzer
    from arvis.kernel_core.vfs.zip.collision import ZipCollisionService
    from arvis.kernel_core.vfs.zip.executor import ZipExecutor
    from arvis.kernel_core.vfs.zip.plan import ZipImportPlanService
    from arvis.kernel_core.vfs.zip.service import ZipIngestService

    monkeypatch.setenv("ENV", "test")

    repo = InMemoryVFSRepository()
    vfs = VFSService(repo)
    parent = repo.create_folder(user_id="u1", name="matter", parent_id=None)
    b = repo._user_bucket("u1")
    b[parent] = VFSItem(
        item_id=parent,
        display_name="matter",
        item_type="folder",
        parent_id=None,
        owner_id="u1",
        organization_id="acme",
        resource_scope="scope:A",
    )

    service = ZipIngestService(
        analyzer=ZipAnalyzer(),
        collision_service=ZipCollisionService(vfs),
        executor=ZipExecutor(vfs_service=vfs),
        planner=ZipImportPlanService(),
        vfs_service=vfs,
    )
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("docs/sub/deep.txt", b"deep")

    decision = service.analyze_and_validate(
        zip_path=str(zip_path), user_id="u1", target_parent_id=parent
    )
    assert decision.status == "ready"
    assert decision.zip_root is not None

    service.execute_import(
        zip_root=decision.zip_root,
        zip_path=str(zip_path),
        user_id="u1",
        target_parent_id=parent,
        keep_zip=True,
    )

    # Every item created under the scoped parent (docs, sub, deep.txt) must
    # carry the parent's organization and scope; none may sit unscoped.
    created = [i for i in vfs.list_items("u1") if i.item_id != parent]
    assert created, "the ZIP import created nothing"
    for item in created:
        assert item.organization_id == "acme", (
            f"{item.display_name} did not inherit the organization"
        )
        assert item.resource_scope == "scope:A", (
            f"{item.display_name} did not inherit the scope"
        )
