from datetime import UTC, datetime

import pytest

from arvis.memory.governance import (
    Governance,
    GovernanceEncryption,
    GovernancePrincipal,
    GovernanceRetention,
    GovernanceSharing,
    GovernanceVisibility,
    compose_strictest,
)
from arvis.memory.memory_long_entry import MemoryLongEntry, MemoryLongType
from arvis.memory.memory_long_policy_gate import MemoryLongPolicyGate


def _now() -> datetime:
    return datetime.now(UTC)


def test_compose_takes_strictest_lever_by_lever() -> None:
    personal = Governance(
        visibility=GovernanceVisibility.DISPLAYABLE,
        sharing=GovernanceSharing.SHAREABLE,
        retention=GovernanceRetention.PERSISTENT,
        encryption=GovernanceEncryption.AT_REST,
        principal=GovernancePrincipal.USER,
    )
    org = Governance(
        visibility=GovernanceVisibility.SEALED,
        sharing=GovernanceSharing.PERSONAL,
        retention=GovernanceRetention.BOUNDED,
        encryption=GovernanceEncryption.AT_REST,
        principal=GovernancePrincipal.ORGANIZATION,
    )
    eff = compose_strictest(personal, org)
    assert eff.visibility is GovernanceVisibility.SEALED
    assert eff.sharing is GovernanceSharing.PERSONAL
    assert eff.retention is GovernanceRetention.BOUNDED
    assert eff.encryption is GovernanceEncryption.AT_REST
    assert eff.principal is GovernancePrincipal.ORGANIZATION


def test_compose_is_idempotent_on_equal_regimes() -> None:
    g = Governance(visibility=GovernanceVisibility.DISPLAYABLE)
    eff = compose_strictest(g, g)
    assert eff.visibility is GovernanceVisibility.DISPLAYABLE
    assert eff.sharing is g.sharing
    assert eff.retention is g.retention


def test_compose_user_can_be_stricter_than_org_floor() -> None:
    personal = Governance(sharing=GovernanceSharing.NEVER_SHARE)
    org = Governance(sharing=GovernanceSharing.SHAREABLE)
    eff = compose_strictest(personal, org)
    assert eff.sharing is GovernanceSharing.NEVER_SHARE


def test_gate_accepts_arbitrary_key_for_user_authored_sources() -> None:
    gate = MemoryLongPolicyGate()
    for source in ("explicit_user", "onboarding"):
        gate.validate_append(
            MemoryLongEntry(
                memory_type=MemoryLongType.CONTEXT,
                key="profession",
                source=source,
                created_at=_now(),
            )
        )


def test_gate_enforces_whitelist_for_system_source() -> None:
    gate = MemoryLongPolicyGate()
    with pytest.raises(ValueError):
        gate.validate_append(
            MemoryLongEntry(
                memory_type=MemoryLongType.CONTEXT,
                key="profession",
                source="governance",
                created_at=_now(),
            )
        )


def test_gate_compose_delegates_to_strictest() -> None:
    gate = MemoryLongPolicyGate()
    eff = gate.compose(
        personal=Governance(visibility=GovernanceVisibility.DISPLAYABLE),
        organization=Governance(visibility=GovernanceVisibility.SEALED),
    )
    assert eff.visibility is GovernanceVisibility.SEALED
