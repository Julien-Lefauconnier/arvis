# arvis/host_api/access.py

"""Identity and organization-scoped authorization.

The principal a host builds for each governed call, the host-attested
stamp PRODUCTION effect syscalls require (``AuthenticatedPrincipal``,
passed to ``run_as``), and the organization-scoped authorization
policy (scoped grants).

Re-export layer only: every symbol is defined where it lives; this
module pins the import path (see VERSIONING.md, host integration
surface).
"""

from arvis.kernel_core.access.models import AuthenticatedPrincipal, Principal
from arvis.kernel_core.access.policy import OrganizationScopedAuthorization

__all__ = [
    "AuthenticatedPrincipal",
    "OrganizationScopedAuthorization",
    "Principal",
]
