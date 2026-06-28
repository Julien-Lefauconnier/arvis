# tests/kernel_core/access/test_access_policy.py

from __future__ import annotations

from arvis.kernel_core.access.decision import AccessDecision
from arvis.kernel_core.access.models import AccessContext, Principal
from arvis.kernel_core.access.policy import (
    ACCESS_DENIED_REASON_CODE,
    CAPABILITY_READ,
    CAPABILITY_WRITE,
    OrganizationScopedAuthorization,
    OwnerScopedAuthorization,
)
from arvis.kernel_core.syscalls.syscall_registry import SyscallEffect


def _context(*, principal_user: str, owner: str) -> AccessContext:
    return AccessContext(
        principal=Principal(user_id=principal_user),
        effect=SyscallEffect.READ,
        resource_owner_id=owner,
        resource_id="item-1",
        syscall_name="vfs.get",
    )


def test_owner_is_allowed() -> None:
    policy = OwnerScopedAuthorization()
    verdict = policy.decide(_context(principal_user="u1", owner="u1"))
    assert verdict.decision is AccessDecision.ALLOW
    assert verdict.allowed is True
    assert verdict.reason_code is None


def test_non_owner_is_denied_with_reason_code() -> None:
    policy = OwnerScopedAuthorization()
    verdict = policy.decide(_context(principal_user="u2", owner="u1"))
    assert verdict.decision is AccessDecision.DENY
    assert verdict.allowed is False
    assert verdict.reason_code == ACCESS_DENIED_REASON_CODE


def test_decision_is_deterministic() -> None:
    policy = OwnerScopedAuthorization()
    ctx = _context(principal_user="u2", owner="u1")
    assert policy.decide(ctx) == policy.decide(ctx)


def test_principal_defaults() -> None:
    principal = Principal(user_id="u1")
    assert principal.organization_id is None
    assert principal.grants == frozenset()


# ---------------------------------------------------------------------------
# OrganizationScopedAuthorization
# ---------------------------------------------------------------------------


def _org_context(
    *,
    principal: Principal,
    effect: SyscallEffect = SyscallEffect.READ,
    owner: str = "alice",
    organization: str | None = "acme",
) -> AccessContext:
    return AccessContext(
        principal=principal,
        effect=effect,
        resource_owner_id=owner,
        resource_organization_id=organization,
        resource_id="item-1",
        syscall_name="vfs.get",
    )


def test_org_policy_personal_resource_is_owner_scoped() -> None:
    policy = OrganizationScopedAuthorization()

    allowed = policy.decide(
        _org_context(principal=Principal(user_id="u1"), owner="u1", organization=None)
    )
    denied = policy.decide(
        _org_context(principal=Principal(user_id="u2"), owner="u1", organization=None)
    )

    assert allowed.allowed is True
    assert denied.allowed is False
    assert denied.reason_code == ACCESS_DENIED_REASON_CODE


def test_org_member_with_required_capability_is_allowed() -> None:
    policy = OrganizationScopedAuthorization()
    member = Principal(
        user_id="bob",
        organization_id="acme",
        grants=frozenset({CAPABILITY_READ}),
    )

    assert policy.decide(_org_context(principal=member)).allowed is True


def test_org_member_without_capability_is_denied() -> None:
    policy = OrganizationScopedAuthorization()
    member = Principal(user_id="bob", organization_id="acme", grants=frozenset())

    verdict = policy.decide(_org_context(principal=member))

    assert verdict.allowed is False
    assert verdict.reason_code == ACCESS_DENIED_REASON_CODE


def test_cross_organization_is_denied() -> None:
    policy = OrganizationScopedAuthorization()
    outsider = Principal(
        user_id="carol",
        organization_id="other",
        grants=frozenset({CAPABILITY_READ}),
    )

    assert policy.decide(_org_context(principal=outsider)).allowed is False


def test_bare_principal_is_denied_on_org_resource() -> None:
    policy = OrganizationScopedAuthorization()

    assert (
        policy.decide(_org_context(principal=Principal(user_id="bob"))).allowed is False
    )


def test_effect_requires_write_capability() -> None:
    policy = OrganizationScopedAuthorization()
    read_only = Principal(
        user_id="bob",
        organization_id="acme",
        grants=frozenset({CAPABILITY_READ}),
    )
    writer = Principal(
        user_id="bob",
        organization_id="acme",
        grants=frozenset({CAPABILITY_READ, CAPABILITY_WRITE}),
    )

    denied = policy.decide(
        _org_context(principal=read_only, effect=SyscallEffect.EFFECT)
    )
    allowed = policy.decide(_org_context(principal=writer, effect=SyscallEffect.EFFECT))

    assert denied.allowed is False
    assert allowed.allowed is True


def test_injected_capability_derivation_overrides_default() -> None:
    def domain_capability(context: AccessContext) -> str:
        return "matiere.lecture"

    policy = OrganizationScopedAuthorization(capability_for=domain_capability)

    with_domain_grant = Principal(
        user_id="bob",
        organization_id="acme",
        grants=frozenset({"matiere.lecture"}),
    )
    with_default_grant = Principal(
        user_id="bob",
        organization_id="acme",
        grants=frozenset({CAPABILITY_READ}),
    )

    assert policy.decide(_org_context(principal=with_domain_grant)).allowed is True
    assert policy.decide(_org_context(principal=with_default_grant)).allowed is False


def test_org_policy_is_deterministic() -> None:
    policy = OrganizationScopedAuthorization()
    member = Principal(
        user_id="bob",
        organization_id="acme",
        grants=frozenset({CAPABILITY_READ}),
    )
    ctx = _org_context(principal=member)

    assert policy.decide(ctx) == policy.decide(ctx)
