# tests/kernel_core/test_governed_syscall_registration.py
"""Governed syscall registration (F-009-a5, closes the deferred B6).

An effect capability cannot exist without its governance: registering
an EFFECT syscall without an access resolver is refused at import time.
The reference resolvers express each syscall class's real rule under
the single owner-scoped policy: kernel-internal syscalls are owned by
the runtime itself (only the kernel principal on the trusted context
channel passes), turn-scoped syscalls are owned by the turn's user.
"""

from types import SimpleNamespace

import pytest

from arvis.errors.kernel_runtime import UngovernedSyscallRegistrationError
from arvis.kernel_core.access.decision import AccessDecision
from arvis.kernel_core.access.models import (
    KERNEL_OWNER_ID,
    KERNEL_PRINCIPAL,
    Principal,
)
from arvis.kernel_core.access.policy import OwnerScopedAuthorization
from arvis.kernel_core.access.resolvers import (
    kernel_internal_resolver,
    turn_owner_resolver,
)
from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import (
    SYSCALL_DESCRIPTORS,
    SYSCALL_REGISTRY,
    SyscallEffect,
    all_descriptors,
    register_syscall,
)

_PREFIX = "test.governed."


def _ok(handler, **_):
    return SyscallResult(success=True)


def _inert_access(args, services):  # pragma: no cover - never invoked
    raise AssertionError("inert resolver must not be invoked")


def _cleanup(name: str) -> None:
    SYSCALL_REGISTRY.pop(name, None)
    SYSCALL_DESCRIPTORS.pop(name, None)


# ---------------------------------------------------------------
# Registration invariant
# ---------------------------------------------------------------


def test_effect_registration_without_access_is_refused():
    name = _PREFIX + "effect_bare"
    with pytest.raises(UngovernedSyscallRegistrationError, match="governance"):
        register_syscall(name, effect=SyscallEffect.EFFECT)(_ok)
    assert name not in SYSCALL_REGISTRY
    assert name not in SYSCALL_DESCRIPTORS


def test_bootstrap_default_effect_without_access_is_refused():
    # An unknown name defaults to EFFECT (fail-closed bootstrap), so a
    # bare registration is refused too.
    name = _PREFIX + "default_bare"
    with pytest.raises(UngovernedSyscallRegistrationError):
        register_syscall(name)(_ok)
    assert name not in SYSCALL_REGISTRY


def test_read_registration_without_access_is_tolerated():
    name = _PREFIX + "read_bare"
    try:
        register_syscall(name, effect=SyscallEffect.READ)(_ok)
        assert name in SYSCALL_REGISTRY
    finally:
        _cleanup(name)


def test_effect_registration_with_access_is_accepted():
    name = _PREFIX + "effect_governed"
    try:
        register_syscall(name, effect=SyscallEffect.EFFECT, access=_inert_access)(_ok)
        assert name in SYSCALL_REGISTRY
    finally:
        _cleanup(name)


def test_live_registry_has_no_ungoverned_effect_syscall():
    # The migration lock: every EFFECT syscall registered at import
    # carries an access resolver. This is the structural form of the
    # invariant; the decorator makes any regression an import error.
    ungoverned = [
        d.name
        for d in all_descriptors()
        if d.effect is SyscallEffect.EFFECT and d.access is None
    ]
    assert ungoverned == []


# ---------------------------------------------------------------
# Kernel-internal resolver
# ---------------------------------------------------------------


def _decide(resolver, args):
    context = resolver(args, services=None)
    return OwnerScopedAuthorization().decide(context), context


def test_kernel_resolver_allows_kernel_principal_on_context():
    resolver = kernel_internal_resolver("process.spawn")
    ctx = SimpleNamespace(principal=KERNEL_PRINCIPAL)
    verdict, context = _decide(resolver, {"ctx": ctx})
    assert verdict.decision is AccessDecision.ALLOW
    assert context.resource_owner_id == KERNEL_OWNER_ID


def test_kernel_resolver_denies_without_principal():
    resolver = kernel_internal_resolver("interrupt.emit")
    verdict, _ = _decide(resolver, {"ctx": SimpleNamespace()})
    assert verdict.decision is AccessDecision.DENY
    verdict, _ = _decide(resolver, {})
    assert verdict.decision is AccessDecision.DENY


def test_kernel_resolver_denies_user_principal():
    resolver = kernel_internal_resolver("process.suspend")
    ctx = SimpleNamespace(principal=Principal(user_id="u1"))
    verdict, _ = _decide(resolver, {"ctx": ctx})
    assert verdict.decision is AccessDecision.DENY


def test_kernel_resolver_ignores_principal_in_args():
    # Identity travels on the trusted context channel only; a principal
    # smuggled through syscall args (cognition-influenced channel) is
    # never read.
    resolver = kernel_internal_resolver("process.resume")
    verdict, _ = _decide(
        resolver, {"principal": KERNEL_PRINCIPAL, "ctx": SimpleNamespace()}
    )
    assert verdict.decision is AccessDecision.DENY


# ---------------------------------------------------------------
# Turn-owner resolver
# ---------------------------------------------------------------


def test_turn_resolver_allows_bare_turn_owner():
    # Behaviour-neutral fallback: an unstamped call acts on its own turn.
    resolver = turn_owner_resolver(SyscallEffect.EFFECT, "tool.execute")
    ctx = SimpleNamespace(user_id="u1")
    verdict, context = _decide(resolver, {"ctx": ctx})
    assert verdict.decision is AccessDecision.ALLOW
    assert context.resource_owner_id == "u1"


def test_turn_resolver_allows_matching_stamped_principal():
    resolver = turn_owner_resolver(SyscallEffect.EFFECT, "llm.generate")
    ctx = SimpleNamespace(user_id="u1", principal=Principal(user_id="u1"))
    verdict, _ = _decide(resolver, {"ctx": ctx})
    assert verdict.decision is AccessDecision.ALLOW


def test_turn_resolver_denies_foreign_stamped_principal():
    resolver = turn_owner_resolver(SyscallEffect.EFFECT, "tool.execute")
    ctx = SimpleNamespace(user_id="u1", principal=Principal(user_id="u2"))
    verdict, _ = _decide(resolver, {"ctx": ctx})
    assert verdict.decision is AccessDecision.DENY


def test_turn_resolver_denies_without_identifiable_owner():
    resolver = turn_owner_resolver(SyscallEffect.EFFECT, "tool.execute")
    verdict, _ = _decide(resolver, {"ctx": SimpleNamespace()})
    assert verdict.decision is AccessDecision.DENY
    verdict, _ = _decide(resolver, {})
    assert verdict.decision is AccessDecision.DENY
