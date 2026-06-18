from dataclasses import dataclass
from enum import StrEnum


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
