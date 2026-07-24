# arvis/host_api/memory.py

"""Governed long-term memory.

The repository protocol a host implements for persistence, the entry
and record types, the policy gate, and the governance vocabulary
(visibility, sharing, retention, encryption, principal).

Re-export layer only: every symbol is defined where it lives; this
module pins the import path (see VERSIONING.md, host integration
surface).
"""

from arvis.memory.governance import (
    Governance,
    GovernanceEncryption,
    GovernancePrincipal,
    GovernanceRetention,
    GovernanceSharing,
    GovernanceVisibility,
)
from arvis.memory.memory_long_entry import (
    MemoryLongEntry,
    MemoryLongType,
)
from arvis.memory.memory_long_policy_gate import MemoryLongPolicyGate
from arvis.memory.memory_long_record import MemoryLongRecord
from arvis.memory.memory_long_repository import MemoryLongRepository
from arvis.memory.memory_long_snapshot import MemoryLongSnapshot

__all__ = [
    "Governance",
    "GovernanceEncryption",
    "GovernancePrincipal",
    "GovernanceRetention",
    "GovernanceSharing",
    "GovernanceVisibility",
    "MemoryLongEntry",
    "MemoryLongPolicyGate",
    "MemoryLongRecord",
    "MemoryLongRepository",
    "MemoryLongSnapshot",
    "MemoryLongType",
]
