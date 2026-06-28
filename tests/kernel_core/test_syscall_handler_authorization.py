# tests/kernel_core/test_syscall_handler_authorization.py

from types import SimpleNamespace

import pytest

from arvis.kernel_core.access.decision import AccessDecision, AccessVerdict
from arvis.kernel_core.access.models import AccessContext, Principal
from arvis.kernel_core.access.policy import AuthorizationPolicy
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.kernel_core.syscalls.syscall_registry import (
    SYSCALL_DESCRIPTORS,
    SYSCALL_REGISTRY,
    SyscallEffect,
    register_syscall,
)

PROBE = "test.authz.probe"
PROBE_NO_RESOLVER = "test.authz.no_resolver"


def _probe_fn(self, **kwargs):
    return SyscallResult(success=True, result={"ok": True})


def _probe_resolver(args, services):
    return AccessContext(
        principal=Principal(user_id=args["user_id"]),
        effect=SyscallEffect.READ,
        resource_owner_id=args["owner_id"],
        syscall_name=PROBE,
    )


class _DenyAll(AuthorizationPolicy):
    def decide(self, context):
        return AccessVerdict(AccessDecision.DENY, "access_denied")


@pytest.fixture
def probe_syscall():
    register_syscall(PROBE, effect=SyscallEffect.READ, access=_probe_resolver)(
        _probe_fn
    )
    try:
        yield PROBE
    finally:
        SYSCALL_REGISTRY.pop(PROBE, None)
        SYSCALL_DESCRIPTORS.pop(PROBE, None)


@pytest.fixture
def probe_syscall_no_resolver():
    register_syscall(PROBE_NO_RESOLVER, effect=SyscallEffect.READ)(_probe_fn)
    try:
        yield PROBE_NO_RESOLVER
    finally:
        SYSCALL_REGISTRY.pop(PROBE_NO_RESOLVER, None)
        SYSCALL_DESCRIPTORS.pop(PROBE_NO_RESOLVER, None)


def test_owner_match_is_allowed(probe_syscall):
    ctx = SimpleNamespace(extra={})
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(),
    )

    result = handler.handle(
        Syscall(
            name=probe_syscall,
            args={"ctx": ctx, "user_id": "alice", "owner_id": "alice"},
        )
    )

    assert result.success is True
    assert result.result["ok"] is True


def test_owner_mismatch_is_denied_and_journaled(probe_syscall):
    ctx = SimpleNamespace(extra={})
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(),
    )

    result = handler.handle(
        Syscall(
            name=probe_syscall,
            args={"ctx": ctx, "user_id": "alice", "owner_id": "bob"},
        )
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "security_error"

    entry = ctx.extra["syscall_results"][0]
    assert entry["syscall"] == probe_syscall
    assert entry["success"] is False
    assert entry["error"]["code"] == "security_error"
    assert entry["error"]["details"]["reason_code"] == "access_denied"


def test_syscall_without_resolver_is_not_checked(probe_syscall_no_resolver):
    ctx = SimpleNamespace(extra={})
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(authorization_service=_DenyAll()),
    )

    result = handler.handle(
        Syscall(
            name=probe_syscall_no_resolver,
            args={"ctx": ctx, "user_id": "alice", "owner_id": "bob"},
        )
    )

    assert result.success is True
    assert result.result["ok"] is True
