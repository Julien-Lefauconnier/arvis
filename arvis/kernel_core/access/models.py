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
    """The (principal, effect, resource) triple evaluated by a policy.

    ``resource_scope`` names a narrower area than the whole organization: a
    matter, a project, a folder, whatever the layer above calls it. The token
    is OPAQUE to ARVIS, which never parses it, never derives a hierarchy from
    it, and never treats one scope as containing another. It only hands it to
    the scope rule the policy was given.

    Leaving it None means the resource is not sub-scoped, which is how every
    resource behaved before scoped grants existed.
    """

    principal: Principal
    effect: SyscallEffect
    resource_owner_id: str
    resource_organization_id: str | None = None
    resource_id: str | None = None
    resource_scope: str | None = None
    syscall_name: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedAccess:
    """An access decision context plus the resource the resolver already read.

    A resolver that must READ a resource to authorize (owner, organization and
    scope live on the resource) can return this instead of a bare
    ``AccessContext``, carrying the resource it read so the syscall body reuses
    it INSTEAD OF reading a second time. For a pure-READ syscall this collapses
    the two lookups into one and closes the time-of-check/time-of-use gap at its
    root: what was authorized is exactly what is returned, with no live store
    between the two (counter-audit B3-VFS-01, b4).

    ``resource`` is opaque to the kernel authorization path, which only reads
    ``context``; it is handed to the body verbatim. Resolvers that do not read a
    resource keep returning a bare ``AccessContext``; the handler treats that as
    ``resource=None``, so this is additive and backward-compatible.

    The three lookup outcomes a reading resolver can report:

    - it READ the resource: ``resource`` holds it, ``lookup_error`` is None. A
      pure-READ body returns it directly (single-read).
    - the lookup raised an EXPECTED condition (not-found, ...): ``resource`` is
      None and ``lookup_error`` holds that exception. Every receiving body maps
      it to its precise code WITHOUT a second lookup or effect, so a live store
      cannot answer the retry with a different resource (the TOCTOU that an
      absorbed expected failure would reopen). This gives finesse AND safety
      at once.
    - it read NOTHING (absent reference, root creation): both are None and the
      body proceeds as before."""

    context: AccessContext
    resource: object | None = None
    lookup_error: Exception | None = None

    def __post_init__(self) -> None:
        """Keep the carried lookup outcome unambiguous.

        A resolver may report a resource, an expected lookup error, or neither.
        Reporting both would let a body choose whichever branch was more
        permissive and would make the authorization handoff ambiguous.
        """
        if not isinstance(self.context, AccessContext):
            raise TypeError("context must be an AccessContext")
        if self.lookup_error is not None and not isinstance(
            self.lookup_error, Exception
        ):
            raise TypeError("lookup_error must be an Exception or None")
        if self.resource is not None and self.lookup_error is not None:
            raise ValueError("resource and lookup_error are mutually exclusive")
