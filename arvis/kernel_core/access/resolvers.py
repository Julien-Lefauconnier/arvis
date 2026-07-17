# arvis/kernel_core/access/resolvers.py
"""Reference access resolvers for governed syscalls (F-009-a5).

Two resolver families cover the syscalls that are not bound to a VFS
resource (those have their own resolvers next to the VFS syscalls):

- ``kernel_internal_resolver``: syscalls whose resource is the runtime
  itself (interrupts, process lifecycle). The resource owner is the
  reserved ``KERNEL_OWNER_ID``; only a call carrying ``KERNEL_PRINCIPAL``
  on the trusted context channel is allowed by the owner-scoped policy.
  There is deliberately no fallback: identity comes from the context
  (ambient trusted channel), never from syscall arguments, which may be
  influenced by cognition downstream of the Gate. A call without the
  kernel principal is denied fail-closed.

- ``turn_owner_resolver``: syscalls executed on behalf of the current
  turn's user (tool execution, LLM realization). The resource owner is
  the turn's ``ctx.user_id``. A stamped principal from another user is
  denied; an unstamped call falls back to the bare user principal,
  which is behaviour-neutral (same doctrine as the VFS scope
  resolvers). A call without an identifiable turn owner is denied
  fail-closed.

Policies stay the single deciding mechanism: resolvers only build the
(principal, effect, resource) triple. This keeps one authorization
boundary for every syscall class (no dedicated kernel policy), and the
kernel case evolves without mechanism change: the day a process becomes
a user-owned resource, its resolver returns the process owner instead
of ``KERNEL_OWNER_ID``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from arvis.kernel_core.access.identity import principal_from_context
from arvis.kernel_core.access.models import (
    KERNEL_OWNER_ID,
    UNAUTHENTICATED_PRINCIPAL_ID,
    AccessContext,
    Principal,
)
from arvis.kernel_core.syscalls.syscall_registry import SyscallEffect

if TYPE_CHECKING:
    from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry

_AccessResolver = Callable[[Mapping[str, Any], "KernelServiceRegistry"], AccessContext]

# Owner placeholder when the turn carries no identifiable user. It never
# matches a principal, so the owner-scoped policy denies (fail-closed).
_UNDETERMINED_OWNER_ID = "__undetermined_owner__"


def kernel_internal_resolver(syscall_name: str) -> _AccessResolver:
    """Resolver for syscalls owned by the runtime itself."""

    def _resolve(
        args: Mapping[str, Any], services: KernelServiceRegistry
    ) -> AccessContext:
        principal = principal_from_context(args.get("ctx"))
        if principal is None:
            principal = Principal(user_id=UNAUTHENTICATED_PRINCIPAL_ID)
        return AccessContext(
            principal=principal,
            effect=SyscallEffect.EFFECT,
            resource_owner_id=KERNEL_OWNER_ID,
            syscall_name=syscall_name,
        )

    return _resolve


def turn_owner_resolver(effect: SyscallEffect, syscall_name: str) -> _AccessResolver:
    """Resolver for syscalls acting on behalf of the current turn's user."""

    def _resolve(
        args: Mapping[str, Any], services: KernelServiceRegistry
    ) -> AccessContext:
        ctx = args.get("ctx")
        user_id = getattr(ctx, "user_id", None)
        owner = user_id if isinstance(user_id, str) else _UNDETERMINED_OWNER_ID

        principal = principal_from_context(ctx)
        if principal is None:
            if isinstance(user_id, str):
                # Behaviour-neutral fallback: the caller acts on its own
                # turn (same doctrine as the VFS scope resolvers).
                principal = Principal(user_id=user_id)
            else:
                principal = Principal(user_id=UNAUTHENTICATED_PRINCIPAL_ID)

        return AccessContext(
            principal=principal,
            effect=effect,
            resource_owner_id=owner,
            syscall_name=syscall_name,
        )

    return _resolve


__all__ = ["kernel_internal_resolver", "turn_owner_resolver"]
