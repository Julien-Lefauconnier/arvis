# arvis/host_api/access.py

"""Identity and organization-scoped authorization.

The principal a host builds for each governed call, and the
organization-scoped authorization policy (scoped grants).

Re-export layer only: every symbol is defined where it lives; this
module pins the import path (see VERSIONING.md, host integration
surface).
"""

from arvis.kernel_core.access.models import Principal
from arvis.kernel_core.access.policy import OrganizationScopedAuthorization

__all__ = [
    "OrganizationScopedAuthorization",
    "Principal",
]
