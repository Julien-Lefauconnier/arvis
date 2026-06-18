from dataclasses import dataclass
from enum import StrEnum
from typing import TypeVar


class GovernanceVisibility(StrEnum):
    """How a declared value may surface, least to most restrictive."""

    DISPLAYABLE = "displayable"
    USABLE = "usable"
    SEALED = "sealed"


class GovernanceSharing(StrEnum):
    """Sharing scope, least to most restrictive."""

    SHAREABLE = "shareable"
    PERSONAL = "personal"
    NEVER_SHARE = "never_share"


class GovernanceRetention(StrEnum):
    """Retention intent, least to most restrictive."""

    PERSISTENT = "persistent"
    BOUNDED = "bounded"
    EPHEMERAL = "ephemeral"


class GovernanceEncryption(StrEnum):
    """Encryption mode, least to most restrictive."""

    AT_REST = "at_rest"
    ZERO_KNOWLEDGE = "zero_knowledge"


class GovernancePrincipal(StrEnum):
    """Authority that authored the governance regime."""

    USER = "user"
    ORGANIZATION = "organization"
    GOVERNANCE = "governance"


@dataclass(frozen=True)
class Governance:
    """Governance regime attached to a long-term memory fact.

    The four levers -- visibility, sharing, retention, encryption -- are the
    substrate. The personal-facing N0-N3 presets live in the surface layer.
    Composition (personal vs organization) takes the strictest value
    lever-by-lever and is handled by the PolicyGate.

    Defaults are backward-compatible and conservative: the value grounds
    answers without being echoed, personal scope only, kept until revoked,
    server-side encryption at rest, authored by the user.
    """

    visibility: GovernanceVisibility = GovernanceVisibility.USABLE
    sharing: GovernanceSharing = GovernanceSharing.PERSONAL
    retention: GovernanceRetention = GovernanceRetention.PERSISTENT
    encryption: GovernanceEncryption = GovernanceEncryption.AT_REST
    principal: GovernancePrincipal = GovernancePrincipal.USER


_StrEnumT = TypeVar("_StrEnumT", bound=StrEnum)


def _stricter(a: _StrEnumT, b: _StrEnumT) -> _StrEnumT:
    """Return the stricter of two members, by declaration order.

    Each lever enum is declared least to most restrictive, so a higher
    index means a stricter value.
    """
    order = list(type(a))
    return a if order.index(a) >= order.index(b) else b


def compose_strictest(
    personal: Governance,
    organization: Governance,
) -> Governance:
    """Compose a personal regime with an organization policy lever-by-lever,
    keeping the stricter value of each lever.

    Used when a personal fact enters an organization scope: the organization
    acts as a non-negotiable floor. The composed regime is bound by the
    organization principal.
    """
    return Governance(
        visibility=_stricter(personal.visibility, organization.visibility),
        sharing=_stricter(personal.sharing, organization.sharing),
        retention=_stricter(personal.retention, organization.retention),
        encryption=_stricter(personal.encryption, organization.encryption),
        principal=GovernancePrincipal.ORGANIZATION,
    )
