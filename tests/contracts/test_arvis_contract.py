# backend/tests/contract/test_arvis_contract.py
"""
Compatibility contract between veramem and the arvis public surface.

This test freezes the exact (module, symbol) surface that veramem imports from
arvis, measured on the repository. It is a migration scaffold, not a permanent
freeze: when arvis is intentionally refactored, this test breaks on purpose,
veramem is migrated in lockstep, and the frozen surface below is updated to the
new reality in the same change.

It exists to guarantee that internal arvis cleanups (e.g. removing the unused
kernel key-value memory substrate) do NOT silently break what veramem consumes.

Note on the LLM contract: veramem currently imports LLMResponse defensively from
two paths, one of which (arvis.adapters.llm.contracts.request) does not define
the symbol. Only the real path is frozen here. Once arvis re-exports LLMResponse
from arvis.adapters.llm.contracts, migrate veramem to that single canonical path
and update this surface.
"""

from __future__ import annotations

import dataclasses
import importlib

import pytest

# ---------------------------------------------------------------------------
# Frozen surface: exactly what veramem imports from arvis (symbols).
# ---------------------------------------------------------------------------
FROZEN_ARVIS_SURFACE: dict[str, tuple[str, ...]] = {
    "arvis": ("ArvisEngine", "CognitiveOSConfig"),
    "arvis.adapters.llm.contracts.response": ("LLMResponse",),
    "arvis.cognition.control": (
        "exploration_controller",
        "mode_hysteresis",
        "regime_policy",
    ),
    "arvis.cognition.control.cognitive_control_engine": (
        "CognitiveControlDeps",
        "CognitiveControlEngine",
        "CognitiveControlSnapshot",
    ),
    "arvis.cognition.control.cognitive_control_runtime": ("CognitiveControlRuntime",),
    "arvis.cognition.control.exploration_controller": ("ExplorationController",),
    "arvis.cognition.control.mode_hysteresis": ("ModeHysteresis",),
    "arvis.cognition.control.regime_policy": ("CognitiveRegimePolicy",),
    "arvis.cognition.retrieval.cognitive_retrieval_snapshot": (
        "CognitiveRetrievalSnapshot",
    ),
    "arvis.conversation.continuation": ("ContinuationResolver", "resolve_continuation"),
    "arvis.conversation.pending_turn": ("PendingTurn", "PendingTurnStatus"),
    "arvis.kernel_core.access.models": ("Principal",),
    "arvis.kernel_core.access.policy": ("OrganizationScopedAuthorization",),
    "arvis.kernel_core.syscalls": ("Syscall", "SyscallHandler"),
    "arvis.kernel_core.syscalls.service_registry": ("KernelServiceRegistry",),
    "arvis.kernel_core.vfs.exceptions": (
        "VFSCycleError",
        "VFSError",
        "VFSFolderNotEmptyError",
        "VFSInvalidNameError",
        "VFSItemNotFoundError",
        "VFSNameConflictError",
        "VFSParentNotFolderError",
        "VFSParentNotFoundError",
    ),
    "arvis.kernel_core.vfs.models": ("VFSItem",),
    "arvis.knowledge.knowledge_event": ("KnowledgeEvent",),
    "arvis.knowledge.knowledge_signal": ("KnowledgeSignal",),
    "arvis.knowledge.knowledge_snapshot": ("KnowledgeSnapshot",),
    "arvis.knowledge.knowledge_state": ("KnowledgeState",),
    "arvis.math.core.contraction_monitor_core": (
        "ContractionMonitorCore",
        "MonitorConfig",
    ),
    "arvis.math.lyapunov.lyapunov_gate": ("lyapunov_gate",),
    "arvis.memory.governance": (
        "Governance",
        "GovernanceEncryption",
        "GovernancePrincipal",
        "GovernanceRetention",
        "GovernanceSharing",
        "GovernanceVisibility",
    ),
    "arvis.memory.memory_long_entry": ("MemoryLongEntry", "MemoryLongType"),
    "arvis.memory.memory_long_policy_gate": ("MemoryLongPolicyGate",),
    "arvis.memory.memory_long_projector": ("MemoryLongContextProjector",),
    "arvis.memory.memory_long_record": ("MemoryLongRecord",),
    "arvis.memory.memory_long_registry": ("DEFAULT_MEMORY_LONG_REGISTRY",),
    "arvis.memory.memory_long_repository": ("MemoryLongRepository",),
    "arvis.memory.memory_long_snapshot": ("MemoryLongSnapshot",),
    "arvis.telemetry": ("InMemoryTelemetrySink", "TelemetryKind"),
    "arvis.tools.base": ("BaseTool",),
    "arvis.tools.executor": ("ToolExecutor",),
    "arvis.tools.manager": ("ToolManager",),
    "arvis.tools.registry": ("ToolRegistry",),
    "arvis.tools.spec": ("ToolSpec",),
}

# Modules that veramem imports as whole modules (not for a specific symbol).
FROZEN_ARVIS_MODULES: tuple[str, ...] = (
    "arvis.kernel_core.syscalls.syscalls.tool_syscalls",
)


def _surface_ids() -> list[str]:
    ids: list[str] = []
    for module, symbols in FROZEN_ARVIS_SURFACE.items():
        for symbol in symbols:
            ids.append(f"{module}:{symbol}")
    return ids


@pytest.mark.parametrize("binding", _surface_ids())
def test_frozen_symbol_resolves(binding: str) -> None:
    module_name, _, symbol = binding.partition(":")
    module = importlib.import_module(module_name)
    assert hasattr(module, symbol), f"arvis moved/removed {module_name}.{symbol}"


@pytest.mark.parametrize("module_name", FROZEN_ARVIS_MODULES)
def test_frozen_module_importable(module_name: str) -> None:
    importlib.import_module(module_name)


# ---------------------------------------------------------------------------
# Targeted shape checks on the contracts most prone to silent signature drift.
# ---------------------------------------------------------------------------


def test_memory_long_entry_zkcs_shape() -> None:
    """veramem depends on the content-agnostic (ZKCS) shape: a value_ref, not a
    value, plus type, key, source, governance."""
    from arvis.memory.memory_long_entry import MemoryLongEntry

    field_names = {f.name for f in dataclasses.fields(MemoryLongEntry)}
    for required in (
        "memory_type",
        "key",
        "created_at",
        "source",
        "governance",
        "value_ref",
    ):
        assert required in field_names, f"MemoryLongEntry lost field: {required}"
    assert "value" not in field_names, (
        "MemoryLongEntry must stay content-agnostic (no inline value)"
    )


def test_governance_default_constructible() -> None:
    """MemoryLongEntry uses Governance() as a default factory."""
    from arvis.memory.governance import Governance

    Governance()


def test_memory_long_repository_is_abstract_interface() -> None:
    """veramem provides the concrete SQL implementation of this interface."""
    from arvis.memory.memory_long_repository import MemoryLongRepository

    abstract = getattr(MemoryLongRepository, "__abstractmethods__", frozenset())
    for method in ("list_entries", "list_active_entries", "revoke"):
        assert hasattr(MemoryLongRepository, method), f"repo interface lost: {method}"
    assert abstract, "MemoryLongRepository must remain abstract (veramem implements it)"


def test_principal_fields() -> None:
    from arvis.kernel_core.access.models import Principal

    field_names = {f.name for f in dataclasses.fields(Principal)}
    for required in ("user_id", "organization_id", "grants"):
        assert required in field_names, f"Principal lost field: {required}"


def test_kernel_service_registry_accepts_veramem_kwargs() -> None:
    """Direct guard for the kernel key-value memory removal.

    veramem constructs KernelServiceRegistry with only these keyword arguments.
    Removing the (unused) memory_service / memory_policy_service fields must keep
    these constructions valid. This test passes today and must stay green after
    the substrate is deleted.
    """
    from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry

    KernelServiceRegistry(tool_manager=None)
    KernelServiceRegistry(vfs_service=None, authorization_service=None)
    # And no memory_* keyword is required to build it.
    KernelServiceRegistry()


def test_pending_turn_status_enum_present() -> None:
    from arvis.conversation.pending_turn import PendingTurn, PendingTurnStatus

    assert PendingTurn is not None
    assert PendingTurnStatus is not None
