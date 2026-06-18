import dataclasses
from datetime import UTC, datetime

import pytest

from arvis.memory.governance import (
    Governance,
    GovernanceEncryption,
    GovernancePrincipal,
    GovernanceRetention,
    GovernanceSharing,
    GovernanceVisibility,
)
from arvis.memory.memory_long_entry import MemoryLongEntry, MemoryLongType


def test_governance_defaults_are_conservative() -> None:
    g = Governance()
    assert g.visibility is GovernanceVisibility.USABLE
    assert g.sharing is GovernanceSharing.PERSONAL
    assert g.retention is GovernanceRetention.PERSISTENT
    assert g.encryption is GovernanceEncryption.AT_REST
    assert g.principal is GovernancePrincipal.USER


def test_governance_is_frozen() -> None:
    g = Governance()
    with pytest.raises(dataclasses.FrozenInstanceError):
        g.visibility = GovernanceVisibility.SEALED


def test_entry_gets_default_governance() -> None:
    entry = MemoryLongEntry(
        memory_type=MemoryLongType.PREFERENCE,
        key="language",
        created_at=datetime.now(UTC),
        source="explicit_user",
    )
    assert entry.governance == Governance()
    assert entry.governance.principal is GovernancePrincipal.USER


def test_entry_accepts_custom_governance() -> None:
    gov = Governance(
        visibility=GovernanceVisibility.SEALED,
        sharing=GovernanceSharing.NEVER_SHARE,
        principal=GovernancePrincipal.ORGANIZATION,
    )
    entry = MemoryLongEntry(
        memory_type=MemoryLongType.CONTEXT,
        key="health_condition",
        created_at=datetime.now(UTC),
        source="explicit_user",
        governance=gov,
    )
    assert entry.governance.visibility is GovernanceVisibility.SEALED
    assert entry.governance.sharing is GovernanceSharing.NEVER_SHARE
    assert entry.governance.principal is GovernancePrincipal.ORGANIZATION
