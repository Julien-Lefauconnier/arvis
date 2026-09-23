# arvis/host_api/access.py

"""Identity and organization-scoped authorization.

The principal and generic access context a host builds for governed calls,
the host-attested stamp PRODUCTION effect syscalls require
(``AuthenticatedPrincipal``, passed to ``run_as``), the typed access verdict,
and the organization-scoped authorization policy (scoped grants). Resource
meaning and scope construction remain host responsibilities.

Re-export layer only: every symbol is defined where it lives; this
module pins the import path (see VERSIONING.md, host integration
surface).
"""

from arvis.kernel_core.access.decision import AccessDecision, AccessVerdict
from arvis.kernel_core.access.models import (
    AccessContext,
    AuthenticatedPrincipal,
    Principal,
    ResolvedAccess,
)
from arvis.kernel_core.access.policy import OrganizationScopedAuthorization

__all__ = [
    "AccessContext",
    "AccessDecision",
    "AccessVerdict",
    "AuthenticatedPrincipal",
    "OrganizationScopedAuthorization",
    "Principal",
    "ResolvedAccess",
]
