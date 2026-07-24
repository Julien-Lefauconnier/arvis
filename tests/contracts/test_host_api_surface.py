# tests/contracts/test_host_api_surface.py

"""Contract test: the host integration surface is exact.

arvis.host_api is the versioned surface a host integrates through
(NOTE_DECISION 2026-07-24, campaign lot 3). This file freezes it both
ways: every pinned symbol must resolve, and every module must expose
exactly its pinned symbols, nothing more. An accidental addition is a
contract change and must fail here, just like a removal.

The literal below is the contract. Changing it is changing the
supported host surface: bump HOST_API_VERSION deliberately.
"""

from types import ModuleType

import pytest

import arvis.host_api
from arvis.host_api import (
    access,
    cognition,
    control,
    conversation,
    engine,
    knowledge,
    llm,
    memory,
    services,
    telemetry,
    tools,
    vfs,
)

HOST_API_SURFACE: dict[str, list[str]] = {
    "engine": [
        "ArvisEngine",
        "CognitiveOSConfig",
        "ContractionMonitorCore",
        "MonitorConfig",
    ],
    "access": [
        "OrganizationScopedAuthorization",
        "Principal",
    ],
    "services": [
        "KernelServiceRegistry",
        "Syscall",
        "SyscallHandler",
    ],
    "vfs": [
        "VFSCycleError",
        "VFSError",
        "VFSFolderNotEmptyError",
        "VFSInvalidNameError",
        "VFSItem",
        "VFSItemNotFoundError",
        "VFSNameConflictError",
        "VFSParentNotFolderError",
        "VFSParentNotFoundError",
    ],
    "tools": [
        "BaseTool",
        "ToolExecutor",
        "ToolManager",
        "ToolRegistry",
        "ToolSpec",
    ],
    "memory": [
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
    ],
    "knowledge": [
        "KnowledgeEvent",
        "KnowledgeSignal",
        "KnowledgeSnapshot",
        "KnowledgeState",
    ],
    "conversation": [
        "PendingTurn",
        "PendingTurnStatus",
        "resolve_continuation",
    ],
    "cognition": [
        "CognitiveRetrievalSnapshot",
    ],
    "control": [
        "CognitiveControlDeps",
        "CognitiveControlEngine",
        "CognitiveRegimePolicy",
        "ExplorationController",
        "ModeHysteresis",
    ],
    "llm": [
        "LLMResponse",
    ],
    "telemetry": [
        "InMemoryTelemetrySink",
        "TelemetryKind",
    ],
}

_MODULES: dict[str, ModuleType] = {
    "engine": engine,
    "access": access,
    "services": services,
    "vfs": vfs,
    "tools": tools,
    "memory": memory,
    "knowledge": knowledge,
    "conversation": conversation,
    "cognition": cognition,
    "control": control,
    "llm": llm,
    "telemetry": telemetry,
}

_PAIRS: list[tuple[str, str]] = [
    (module, symbol)
    for module, symbols in HOST_API_SURFACE.items()
    for symbol in symbols
]


def test_surface_size_is_pinned() -> None:
    assert len(HOST_API_SURFACE) == 12
    assert sorted(HOST_API_SURFACE) == sorted(_MODULES)
    assert len(_PAIRS) == 51


@pytest.mark.parametrize(
    ("module", "symbol"),
    _PAIRS,
    ids=[f"{module}:{symbol}" for module, symbol in _PAIRS],
)
def test_host_api_symbol_resolves(module: str, symbol: str) -> None:
    assert hasattr(_MODULES[module], symbol), (
        f"host_api.{module} must expose {symbol}; the host surface is broken"
    )


@pytest.mark.parametrize("module", sorted(_MODULES), ids=sorted(_MODULES))
def test_host_api_module_surface_is_exact(module: str) -> None:
    """__all__ equals the pinned surface: no removal, no silent addition."""
    assert sorted(_MODULES[module].__all__) == sorted(HOST_API_SURFACE[module])


def test_host_api_version_policy_is_pinned() -> None:
    assert arvis.host_api.HOST_API_VERSION == "1.0"
    assert arvis.host_api.PROVISIONAL_MODULES == frozenset({"control"})
    assert arvis.host_api.PROVISIONAL_MODULES < set(HOST_API_SURFACE)
