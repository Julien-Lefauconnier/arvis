# tests/kernel_core/access/test_vfs_expected_errors_finesse_unit.py

"""Red reproductions for the b4 finesse restoration.

The 0.1.0b3 resolver absorbs NO lookup exception: an expected VFS condition
(item or parent not found, ...) propagates and the handler turns it into a
fail-closed authorization_failure. That erases a legitimate distinction: an
item that genuinely does NOT exist is not an authorization failure, and a
caller entitled to the scope deserves the precise not-found code, not an
opaque access denial.

fail-closed does not mean fail-opaque. The resolver must still deny an
INDETERMINATE lookup (a transient, unexpected failure) with
authorization_failure, closing the time-of-check/time-of-use gap (B3-VFS-01),
but an EXPECTED VFS condition must flow to its proper error code, resolved by
the syscall body exactly as it does when no scope is involved.

Anti-enumeration is preserved by the DENIED case, not by erasing not-found: a
principal WITHOUT access to an existing item receives access_denied, so it can
never tell "exists but forbidden" from "does not exist". not-found is only ever
returned to a caller whose authorization would have succeeded had the item
existed, i.e. a caller legitimately entitled to that scope, for whom knowing
the item is absent is not a leak.

Each test names the syscall and the expected precise code.
"""

from types import SimpleNamespace

from arvis.kernel_core.access.models import Principal
from arvis.kernel_core.access.policy import OrganizationScopedAuthorization
from arvis.kernel_core.syscalls import Syscall, SyscallHandler
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.vfs.repositories.in_memory import InMemoryVFSRepository
from arvis.kernel_core.vfs.service import VFSService


def _handler() -> SyscallHandler:
    return SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            vfs_service=VFSService(InMemoryVFSRepository()),
            authorization_service=OrganizationScopedAuthorization(),
        ),
    )


def _ctx() -> SimpleNamespace:
    return SimpleNamespace(extra={}, principal=Principal(user_id="u"))


def _code(result) -> str | None:
    return result.error.code if result.error else None


def _reason(result) -> str | None:
    if result.error is None:
        return None
    details = getattr(result.error, "details", None)
    return details.get("reason_code") if isinstance(details, dict) else None


def test_vfs_get_missing_item_is_not_found_not_authorization_failure():
    """vfs.get on an absent item resolves to vfs_item_not_found, not
    authorization_failure. RED on b3: the resolver propagates the not-found and
    the handler emits authorization_failure."""
    result = _handler().handle(
        Syscall(
            name="vfs.get", args={"ctx": _ctx(), "user_id": "u", "item_id": "missing"}
        )
    )
    assert result.success is False
    assert _code(result) == "vfs_item_not_found", (
        f"expected vfs_item_not_found, got code={_code(result)} "
        f"reason={_reason(result)}"
    )


def test_vfs_delete_missing_item_is_not_found():
    """vfs.delete_item on an absent item resolves to vfs_item_not_found."""
    result = _handler().handle(
        Syscall(
            name="vfs.delete_item",
            args={"ctx": _ctx(), "user_id": "u", "item_id": "missing"},
        )
    )
    assert result.success is False
    assert _code(result) == "vfs_item_not_found", (
        f"got code={_code(result)} reason={_reason(result)}"
    )


def test_vfs_rename_missing_item_is_not_found():
    """vfs.rename_item on an absent item resolves to vfs_item_not_found."""
    result = _handler().handle(
        Syscall(
            name="vfs.rename_item",
            args={
                "ctx": _ctx(),
                "user_id": "u",
                "item_id": "missing",
                "new_name": "x",
            },
        )
    )
    assert result.success is False
    assert _code(result) == "vfs_item_not_found", (
        f"got code={_code(result)} reason={_reason(result)}"
    )


def test_vfs_create_folder_missing_parent_is_parent_not_found():
    """vfs.create_folder under an absent parent resolves to
    vfs_parent_not_found, not authorization_failure."""
    result = _handler().handle(
        Syscall(
            name="vfs.create_folder",
            args={
                "ctx": _ctx(),
                "user_id": "u",
                "name": "docs",
                "parent_id": "missing-parent",
            },
        )
    )
    assert result.success is False
    assert _code(result) == "vfs_parent_not_found", (
        f"got code={_code(result)} reason={_reason(result)}"
    )


def test_indeterminate_lookup_still_denies_with_authorization_failure():
    """An UNEXPECTED lookup failure still denies with authorization_failure:
    fail-closed on the indeterminate case is preserved (B3-VFS-01 stays
    closed). This is the property that must NOT regress while restoring
    finesse."""

    class _FlakyVFS:
        def get_item(self, *, user_id: str, item_id: str):
            raise RuntimeError("transient outage")

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            vfs_service=_FlakyVFS(),
            authorization_service=OrganizationScopedAuthorization(),
        ),
    )
    result = handler.handle(
        Syscall(name="vfs.get", args={"ctx": _ctx(), "user_id": "u", "item_id": "i1"})
    )
    assert result.success is False
    assert _reason(result) == "authorization_failure", (
        "an indeterminate lookup must still deny fail-closed"
    )


def test_denied_existing_item_is_access_denied_preserving_anti_enumeration():
    """A principal without access to an EXISTING item receives access_denied,
    NOT not-found: anti-enumeration holds. This is why restoring not-found for
    genuinely absent items is safe: the forbidden-existing case is a distinct,
    indistinguishable denial."""
    repo = InMemoryVFSRepository()
    # Seed an item owned by someone else, in an organization the caller is not
    # a member of.
    from arvis.kernel_core.vfs.models import VFSItem

    bucket = repo._user_bucket("owner")
    bucket["secret"] = VFSItem(
        item_id="secret",
        display_name="s.txt",
        item_type="file",
        parent_id=None,
        owner_id="owner",
        organization_id="acme",
    )
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            vfs_service=VFSService(repo),
            authorization_service=OrganizationScopedAuthorization(),
        ),
    )
    # The caller looks up an item it does not own and whose org it is not in.
    result = handler.handle(
        Syscall(
            name="vfs.get",
            args={
                "ctx": SimpleNamespace(
                    extra={}, principal=Principal(user_id="intruder")
                ),
                "user_id": "owner",
                "item_id": "secret",
            },
        )
    )
    assert result.success is False
    # Denied, not not-found: the intruder cannot tell the item exists.
    assert _reason(result) == "access_denied", (
        f"expected access_denied, got code={_code(result)} reason={_reason(result)}"
    )
