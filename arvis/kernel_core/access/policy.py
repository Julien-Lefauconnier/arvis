# arvis/kernel_core/access/policy.py

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Final

from arvis.kernel_core.access.decision import AccessDecision, AccessVerdict
from arvis.kernel_core.access.models import AccessContext
from arvis.kernel_core.syscalls.syscall_registry import SyscallEffect

# Canonical access-layer reason code (ARVIS_ACCESS_SPEC_V1). The enforcement
# layer registers it in the ReasonCodeRegistry; the contract only references it.
ACCESS_DENIED_REASON_CODE: Final[str] = "access_denied"


class AuthorizationPolicy(ABC):
    """Contract for deciding whether a principal may perform a syscall.

    Policies MUST be deterministic and side-effect free: an identical context
    yields an identical verdict. They MUST fail closed, i.e. return DENY rather
    than raise when the answer is uncertain.
    """

    @abstractmethod
    def decide(self, context: AccessContext) -> AccessVerdict:
        """Return ALLOW or DENY for the given access context."""
        raise NotImplementedError


class OwnerScopedAuthorization(AuthorizationPolicy):
    """Default policy: a principal may act only on resources it owns.

    Ownership is ``principal.user_id == resource_owner_id``. This reproduces the
    pre-authorization behaviour (access scoped by ``user_id``) exactly, so
    wiring this policy as the default is behaviour-neutral.
    """

    def decide(self, context: AccessContext) -> AccessVerdict:
        if context.principal.user_id == context.resource_owner_id:
            return AccessVerdict(AccessDecision.ALLOW)
        return AccessVerdict(AccessDecision.DENY, ACCESS_DENIED_REASON_CODE)


CAPABILITY_READ: Final[str] = "read"
CAPABILITY_WRITE: Final[str] = "write"


def default_capability_for(context: AccessContext) -> str:
    """Reference capability derivation: READ needs read, EFFECT needs write.

    The returned token is opaque to ARVIS. A realization layer built on ARVIS
    MAY inject its own derivation to map effects or syscalls to a
    domain-specific capability vocabulary, without changing this contract.
    """
    if context.effect is SyscallEffect.READ:
        return CAPABILITY_READ
    return CAPABILITY_WRITE


class OrganizationScopedAuthorization(AuthorizationPolicy):
    """Reference organization-aware policy. Generic, not domain-specific.

    It subsumes the personal case: a resource with no organization
    (``resource_organization_id is None``) is owner-scoped, identical to
    ``OwnerScopedAuthorization``. A resource that belongs to an organization is
    accessible when the principal belongs to that same organization and holds
    the required capability.

    Grants are opaque tokens. ARVIS only tests membership of the required
    capability in ``principal.grants``. Assigning meaning to those tokens, and
    deciding which capability a given access requires, belongs to the
    realization layer, which MAY inject ``capability_for``.
    """

    def __init__(
        self, capability_for: Callable[[AccessContext], str] | None = None
    ) -> None:
        self._capability_for: Callable[[AccessContext], str] = (
            capability_for or default_capability_for
        )

    def decide(self, context: AccessContext) -> AccessVerdict:
        if context.resource_organization_id is None:
            if context.principal.user_id == context.resource_owner_id:
                return AccessVerdict(AccessDecision.ALLOW)
            return AccessVerdict(AccessDecision.DENY, ACCESS_DENIED_REASON_CODE)

        principal = context.principal
        if (
            principal.organization_id == context.resource_organization_id
            and self._capability_for(context) in principal.grants
        ):
            return AccessVerdict(AccessDecision.ALLOW)
        return AccessVerdict(AccessDecision.DENY, ACCESS_DENIED_REASON_CODE)
