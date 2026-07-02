# tests/kernel_core/syscalls/test_vfs_access_resolvers.py

import inspect
from types import SimpleNamespace

from arvis.kernel_core.access.identity import principal_from_context
from arvis.kernel_core.access.models import Principal
from arvis.kernel_core.access.policy import (
    CAPABILITY_READ,
    OrganizationScopedAuthorization,
)
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.kernel_core.syscalls.syscall_registry import (
    SYSCALL_DESCRIPTORS,
    SyscallEffect,
)
from arvis.kernel_core.syscalls.syscalls.vfs_syscalls import _item_owner_resolver
from arvis.kernel_core.vfs.models import VFSItem


class _FakeVFS:
    """Minimal VFS service exposing an item owned by a fixed principal.

    It stands in for a future scope-crossing repository so the resolver can be
    shown to read the real owner and bite, which the current strictly scoped
    in-memory repository cannot reproduce on its own.
    """

    def __init__(self, owner_id: str, organization_id: str | None = None) -> None:
        self._owner_id = owner_id
        self._organization_id = organization_id

    def get_item(self, *, user_id: str, item_id: str) -> VFSItem:
        return VFSItem(
            item_id=item_id,
            display_name="probe.txt",
            item_type="file",
            parent_id=None,
            owner_id=self._owner_id,
            organization_id=self._organization_id,
        )


def test_user_scoped_vfs_syscalls_declare_access_resolver():
    for name, descriptor in SYSCALL_DESCRIPTORS.items():
        if not name.startswith("vfs."):
            continue
        params = inspect.signature(descriptor.fn).parameters
        if "user_id" not in params:
            continue
        assert descriptor.access is not None, (
            f"{name} operates in a user scope but declares no access resolver"
        )


def test_stateless_vfs_plan_is_exempt():
    descriptor = SYSCALL_DESCRIPTORS["vfs.zip.plan"]
    params = inspect.signature(descriptor.fn).parameters
    assert "user_id" not in params
    assert descriptor.access is None


def test_vfs_get_denies_cross_owner_item():
    services = KernelServiceRegistry(vfs_service=_FakeVFS(owner_id="alice"))
    handler = SyscallHandler(runtime_state=None, scheduler=None, services=services)
    ctx = SimpleNamespace(extra={})

    result = handler.handle(
        Syscall(
            name="vfs.get",
            args={"ctx": ctx, "user_id": "bob", "item_id": "i1"},
        )
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "security_error"

    entry = ctx.extra["syscall_results"][0]
    assert entry["error"]["details"]["reason_code"] == "access_denied"


def test_vfs_get_allows_owner():
    services = KernelServiceRegistry(vfs_service=_FakeVFS(owner_id="alice"))
    handler = SyscallHandler(runtime_state=None, scheduler=None, services=services)
    ctx = SimpleNamespace(extra={})

    result = handler.handle(
        Syscall(
            name="vfs.get",
            args={"ctx": ctx, "user_id": "alice", "item_id": "i1"},
        )
    )

    assert result.success is True
    assert result.result["item_id"] == "i1"


def test_item_resolver_populates_resource_organization_id():
    resolver = _item_owner_resolver(SyscallEffect.READ, "vfs.get", id_arg="item_id")
    services = KernelServiceRegistry(
        vfs_service=_FakeVFS(owner_id="alice", organization_id="acme"),
    )

    context = resolver({"user_id": "bob", "item_id": "i1"}, services)

    assert context.resource_owner_id == "alice"
    assert context.resource_organization_id == "acme"


def test_item_resolver_defaults_organization_to_none_when_unreadable():
    resolver = _item_owner_resolver(SyscallEffect.READ, "vfs.get", id_arg="item_id")
    services = KernelServiceRegistry(vfs_service=None)

    context = resolver({"user_id": "bob", "item_id": "i1"}, services)

    assert context.resource_owner_id == "bob"
    assert context.resource_organization_id is None


# ---------------------------------------------------------------------------
# Identity on the execution context (org-4)
# ---------------------------------------------------------------------------


def test_principal_from_context_reads_stamped_identity():
    member = Principal(user_id="bob", organization_id="acme")
    ctx = SimpleNamespace(extra={}, principal=member)

    assert principal_from_context(ctx) is member


def test_principal_from_context_returns_none_when_absent_or_invalid():
    assert principal_from_context(SimpleNamespace(extra={})) is None
    assert principal_from_context(SimpleNamespace(principal="not-a-principal")) is None
    assert principal_from_context(None) is None


def _org_handler():
    services = KernelServiceRegistry(
        vfs_service=_FakeVFS(owner_id="alice", organization_id="acme"),
        authorization_service=OrganizationScopedAuthorization(),
    )
    return SyscallHandler(runtime_state=None, scheduler=None, services=services)


def _get_as(principal: Principal):
    handler = _org_handler()
    ctx = SimpleNamespace(extra={}, principal=principal)
    result = handler.handle(
        Syscall(name="vfs.get", args={"ctx": ctx, "user_id": "caller", "item_id": "i1"})
    )
    return result, ctx


def test_org_member_with_grant_allowed_end_to_end():
    member = Principal(
        user_id="bob",
        organization_id="acme",
        grants=frozenset({CAPABILITY_READ}),
    )
    result, _ = _get_as(member)

    assert result.success is True
    assert result.result["item_id"] == "i1"


def test_org_member_without_grant_denied_end_to_end():
    member = Principal(user_id="bob", organization_id="acme", grants=frozenset())
    result, ctx = _get_as(member)

    assert result.success is False
    assert result.error.code == "security_error"
    assert ctx.extra["syscall_results"][0]["error"]["details"]["reason_code"] == (
        "access_denied"
    )


def test_org_outsider_denied_end_to_end():
    outsider = Principal(
        user_id="carol",
        organization_id="other",
        grants=frozenset({CAPABILITY_READ}),
    )
    result, _ = _get_as(outsider)

    assert result.success is False
    assert result.error.code == "security_error"


def test_personal_resource_still_owner_scoped_under_org_policy():
    services = KernelServiceRegistry(
        vfs_service=_FakeVFS(owner_id="alice", organization_id=None),
        authorization_service=OrganizationScopedAuthorization(),
    )
    handler = SyscallHandler(runtime_state=None, scheduler=None, services=services)

    owner_ctx = SimpleNamespace(extra={}, principal=Principal(user_id="alice"))
    other_ctx = SimpleNamespace(extra={}, principal=Principal(user_id="bob"))

    owner_result = handler.handle(
        Syscall(
            name="vfs.get",
            args={"ctx": owner_ctx, "user_id": "alice", "item_id": "i1"},
        )
    )
    other_result = handler.handle(
        Syscall(
            name="vfs.get",
            args={"ctx": other_ctx, "user_id": "bob", "item_id": "i1"},
        )
    )

    assert owner_result.success is True
    assert other_result.success is False
