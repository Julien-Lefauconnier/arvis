"""A grant may cover the whole organization, or a narrower scope inside it.

Belonging to an organization and holding a capability is not always enough. A
resource may name a scope, and the principal's grants must then cover it. That
is what lets a realization layer say "this member may read matter 7, not matter
9" without ARVIS ever learning what a matter is.

The scope token is opaque here. The kernel does not parse it, derive a
hierarchy from it, or treat one scope as containing another. A layer whose
scopes have structure injects its own rule; these tests pin both the default
and the injection point.
"""

from __future__ import annotations

from arvis.kernel_core.access.decision import AccessDecision
from arvis.kernel_core.access.models import AccessContext, Principal
from arvis.kernel_core.access.policy import (
    OrganizationScopedAuthorization,
    exact_scope_grant,
)
from arvis.kernel_core.syscalls.syscall_registry import SyscallEffect

_ORG = "org-7"


def _member(*grants: str) -> Principal:
    return Principal(user_id="u1", organization_id=_ORG, grants=frozenset(grants))


def _context(principal: Principal, scope: str | None) -> AccessContext:
    return AccessContext(
        principal=principal,
        effect=SyscallEffect.READ,
        resource_owner_id="someone-else",
        resource_organization_id=_ORG,
        resource_scope=scope,
    )


def _decide(policy, principal, scope):
    return policy.decide(_context(principal, scope)).decision


def test_an_unscoped_resource_behaves_as_before():
    """Retro-compatibility: organization-wide grants keep working untouched."""
    policy = OrganizationScopedAuthorization()

    assert _decide(policy, _member("read"), None) is AccessDecision.ALLOW


def test_a_scoped_resource_needs_that_scope_granted():
    policy = OrganizationScopedAuthorization()

    granted = _member("read", "matter:7")
    assert _decide(policy, granted, "matter:7") is AccessDecision.ALLOW


def test_a_scoped_resource_is_denied_without_the_scope():
    """Holding the capability organization-wide does not reach into a scope."""
    policy = OrganizationScopedAuthorization()

    assert _decide(policy, _member("read"), "matter:7") is AccessDecision.DENY


def test_one_scope_does_not_grant_another():
    policy = OrganizationScopedAuthorization()

    holder = _member("read", "matter:7")
    assert _decide(policy, holder, "matter:9") is AccessDecision.DENY


def test_the_scope_is_opaque_to_the_kernel():
    """No hierarchy is inferred: a nested-looking token is still just a token."""
    policy = OrganizationScopedAuthorization()

    holder = _member("read", "client:3")
    assert _decide(policy, holder, "client:3/matter:7") is AccessDecision.DENY


def test_a_realization_layer_can_inject_its_own_scope_rule():
    """Structure belongs to the layer that knows what its scopes mean."""

    def prefix_covers(principal: Principal, resource_scope: str | None) -> bool:
        if resource_scope is None:
            return True
        return any(resource_scope.startswith(g) for g in principal.grants)

    policy = OrganizationScopedAuthorization(scope_covers=prefix_covers)

    holder = _member("read", "client:3")
    assert _decide(policy, holder, "client:3/matter:7") is AccessDecision.ALLOW


def test_the_scope_rule_cannot_rescue_a_missing_capability():
    """Coverage is an additional condition, never a replacement."""
    policy = OrganizationScopedAuthorization(scope_covers=lambda p, s: True)

    assert _decide(policy, _member("matter:7"), "matter:7") is AccessDecision.DENY


def test_the_scope_rule_cannot_rescue_a_foreign_organization():
    policy = OrganizationScopedAuthorization(scope_covers=lambda p, s: True)
    outsider = Principal(
        user_id="u2", organization_id="org-other", grants=frozenset({"read"})
    )

    assert _decide(policy, outsider, "matter:7") is AccessDecision.DENY


def test_the_default_rule_in_isolation():
    holder = _member("read", "matter:7")

    assert exact_scope_grant(holder, None) is True
    assert exact_scope_grant(holder, "matter:7") is True
    assert exact_scope_grant(holder, "matter:9") is False
