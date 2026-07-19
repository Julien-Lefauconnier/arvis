# arvis/kernel_core/access/models.py

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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


@dataclass(slots=True, frozen=True, kw_only=True)
class AuthenticatedPrincipal(Principal):
    """Host-attested identity accepted for production effects.

    ARVIS does not authenticate credentials itself. The host authenticates the
    subject and constructs this explicit stamp on the trusted context channel.
    The additional fields are governance material, not secrets or credentials.
    """

    authentication_source: str
    authentication_strength: str
    service_id: str | None = None
    session_id_hash: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.user_id, str) or not self.user_id:
            raise ValueError("user_id must be a non-empty string")
        if (
            not isinstance(self.authentication_source, str)
            or not self.authentication_source
        ):
            raise ValueError("authentication_source must be a non-empty string")
        if (
            not isinstance(self.authentication_strength, str)
            or not self.authentication_strength
        ):
            raise ValueError("authentication_strength must be a non-empty string")
        for field_name in ("service_id", "session_id_hash"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value):
                raise ValueError(f"{field_name} must be None or a non-empty string")


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
