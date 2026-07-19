"""Immutable identity and provenance material authorized for one tool effect.

An effect context is deliberately data-only. It contains the minimum identity,
tenant and runtime bindings a tool may observe when selecting its effect. It
never transports the mutable pipeline context, service clients, credentials or
other host runtime objects.

The model is usable in local profiles as well as production. Production
requirements (a host-authenticated principal and a runtime run binding) remain
boundary policy: this value validates its shape and immutability, while the
syscall handler validates whether the current profile may use it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arvis.kernel_core.access.identity import (
    authenticated_principal_from_context,
    principal_from_context,
)
from arvis.kernel_core.access.models import UNAUTHENTICATED_PRINCIPAL_ID
from arvis.kernel_core.canonicalization import canonical_hash

EFFECT_CONTEXT_FORMAT_VERSION = 1


def _require_non_empty(field_name: str, value: object) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_optional_non_empty(field_name: str, value: object) -> None:
    if value is not None and (not isinstance(value, str) or not value):
        raise ValueError(f"{field_name} must be None or a non-empty string")


@dataclass(frozen=True, slots=True)
class AuthorizedEffectContext:
    """Sealed identity and provenance visible to one authorized effect.

    The authentication fields describe the provenance asserted by the host;
    they are not credentials and ARVIS does not authenticate them. A local
    profile may use explicit values such as ``"unattested"`` and ``"none"``.
    Production admission separately requires those values to match the exact
    :class:`~arvis.kernel_core.access.models.AuthenticatedPrincipal` on the
    trusted current context.
    """

    principal: str
    tenant: str | None
    authentication_source: str
    authentication_strength: str
    service_id: str | None
    session_id_hash: str | None
    process_id: str
    run_id: str | None
    host_binding_commitment: str | None = None
    format_version: int = EFFECT_CONTEXT_FORMAT_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "principal",
            "authentication_source",
            "authentication_strength",
            "process_id",
        ):
            _require_non_empty(field_name, getattr(self, field_name))
        for field_name in (
            "tenant",
            "service_id",
            "session_id_hash",
            "run_id",
            "host_binding_commitment",
        ):
            _require_optional_non_empty(field_name, getattr(self, field_name))
        if (
            type(self.format_version) is not int
            or self.format_version != EFFECT_CONTEXT_FORMAT_VERSION
        ):
            raise ValueError("unsupported effect context format version")

    def to_material(self) -> dict[str, Any]:
        """Return the complete canonical commitment material."""
        return {
            "effect_context_format_version": self.format_version,
            "principal": self.principal,
            "tenant": self.tenant,
            "authentication_source": self.authentication_source,
            "authentication_strength": self.authentication_strength,
            "service_id": self.service_id,
            "session_id_hash": self.session_id_hash,
            "process_id": self.process_id,
            "run_id": self.run_id,
            "host_binding_commitment": self.host_binding_commitment,
        }

    @property
    def commitment_sha256(self) -> str:
        """Canonical SHA-256 of every authorized effect-context field."""
        return canonical_hash(self.to_material())


def build_authorized_effect_context(
    ctx: Any,
    *,
    process_id: str,
    run_id: str | None,
    host_binding_commitment: str | None = None,
) -> AuthorizedEffectContext:
    """Snapshot the trusted identity channel into effect-only material.

    Authorization and the syscall boundary deliberately share this builder so
    that they cannot silently drift in how a current principal is projected.
    Runtime identifiers remain explicit inputs: they are resolved by the
    boundary that owns them, never inferred from cognition-controlled data.
    """
    principal = principal_from_context(ctx)
    authenticated = authenticated_principal_from_context(ctx)
    principal_id = (
        principal.user_id if principal is not None else getattr(ctx, "user_id", None)
    )
    if not isinstance(principal_id, str) or not principal_id:
        principal_id = UNAUTHENTICATED_PRINCIPAL_ID

    return AuthorizedEffectContext(
        principal=principal_id,
        tenant=principal.organization_id if principal is not None else None,
        authentication_source=(
            authenticated.authentication_source
            if authenticated is not None
            else "unattested"
        ),
        authentication_strength=(
            authenticated.authentication_strength
            if authenticated is not None
            else "none"
        ),
        service_id=authenticated.service_id if authenticated is not None else None,
        session_id_hash=(
            authenticated.session_id_hash if authenticated is not None else None
        ),
        process_id=process_id,
        run_id=run_id,
        host_binding_commitment=host_binding_commitment,
    )


__all__ = [
    "EFFECT_CONTEXT_FORMAT_VERSION",
    "AuthorizedEffectContext",
    "build_authorized_effect_context",
]
