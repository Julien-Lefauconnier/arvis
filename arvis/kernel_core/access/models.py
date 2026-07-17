# arvis/kernel_core/access/models.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.kernel_core.syscalls.syscall_registry import SyscallEffect

# Reserved owner id for resources that belong to the runtime itself
# (kernel-internal syscalls: interrupts, process lifecycle). Only calls
# carrying the kernel principal on the trusted context channel may act
# on them; the id is never a valid user id.
KERNEL_OWNER_ID = "__kernel__"

# Placeholder principal id for calls reaching an effect syscall without
# any identity on the trusted channel. It matches no resource owner, so
# the owner-scoped policy denies (fail-closed by construction).
UNAUTHENTICATED_PRINCIPAL_ID = "__unauthenticated__"


@dataclass(slots=True, frozen=True)
class Principal:
    """Identity on whose behalf a syscall is executed.

    A bare principal (``user_id`` only, no organization, no grants) denotes the
    resource owner. This reproduces the pre-authorization behaviour, where
    access was scoped solely by ``user_id``.
    """

    user_id: str
    organization_id: str | None = None
    grants: frozenset[str] = frozenset()


# The runtime's own identity, stamped on the context by internal call
# sites of kernel-internal syscalls. Frozen and grant-less: the kernel
# principal owns exactly the kernel-owned resources, nothing else.
KERNEL_PRINCIPAL = Principal(user_id=KERNEL_OWNER_ID)


@dataclass(slots=True, frozen=True)
class AccessContext:
    """The (principal, effect, resource) triple evaluated by a policy."""

    principal: Principal
    effect: SyscallEffect
    resource_owner_id: str
    resource_organization_id: str | None = None
    resource_id: str | None = None
    syscall_name: str | None = None
