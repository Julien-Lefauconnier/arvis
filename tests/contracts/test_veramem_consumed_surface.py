"""Contract test: the arvis surface consumed by veramem must keep resolving.

veramem (the proprietary product) imports arvis through ~60 deep-path
`from <module> import <symbol>` bindings. This file freezes that exact
surface so the 0.1-alpha consolidation (removal, memory rework,
gate/projection changes) cannot silently break veramem in production.

Source of truth: the 2026-07-02 cartography of veramem's imports,
reconciled against the current veramem repomix. Notably `LLMResponse` is
now imported from the `arvis.adapters.llm.contracts` package (the earlier
split request/response import paths no longer exist in veramem).

If arvis is refactored and one of these bindings stops resolving, this
test fails fail-closed and names the exact broken (module, symbol). It is
a pure arvis-side test: it does not import veramem, only asserts that
arvis still exposes what veramem relies on.
"""

import importlib

import pytest

# THE CONTRACT. Any change here is a change to veramem's supported surface.
CONSUMED_SURFACE: dict[str, list[str]] = {
    "arvis": [
        "ArvisEngine",
        "CognitiveOSConfig",
    ],
    "arvis.adapters.llm.contracts": [
        "LLMResponse",
    ],
    "arvis.cognition.control": [
        "exploration_controller",
        "mode_hysteresis",
        "regime_policy",
    ],
    "arvis.cognition.control.cognitive_control_engine": [
        "CognitiveControlDeps",
        "CognitiveControlEngine",
        "CognitiveControlSnapshot",
    ],
    "arvis.cognition.control.cognitive_control_runtime": [
        "CognitiveControlRuntime",
    ],
    "arvis.cognition.control.exploration_controller": [
        "ExplorationController",
    ],
    "arvis.cognition.control.mode_hysteresis": [
        "ModeHysteresis",
    ],
    "arvis.cognition.control.regime_policy": [
        "CognitiveRegimePolicy",
    ],
    "arvis.cognition.retrieval.cognitive_retrieval_snapshot": [
        "CognitiveRetrievalSnapshot",
    ],
    "arvis.conversation.continuation": [
        "ContinuationResolver",
        "resolve_continuation",
    ],
    "arvis.conversation.pending_turn": [
        "PendingTurn",
        "PendingTurnStatus",
    ],
    "arvis.kernel_core.access.models": [
        "Principal",
    ],
    "arvis.kernel_core.access.policy": [
        "OrganizationScopedAuthorization",
    ],
    "arvis.kernel_core.syscalls": [
        "Syscall",
        "SyscallHandler",
    ],
    "arvis.kernel_core.syscalls.service_registry": [
        "KernelServiceRegistry",
    ],
    "arvis.kernel_core.vfs.exceptions": [
        "VFSCycleError",
        "VFSError",
        "VFSFolderNotEmptyError",
        "VFSInvalidNameError",
        "VFSItemNotFoundError",
        "VFSNameConflictError",
        "VFSParentNotFolderError",
        "VFSParentNotFoundError",
    ],
    "arvis.kernel_core.vfs.models": [
        "VFSItem",
    ],
    "arvis.knowledge.knowledge_event": [
        "KnowledgeEvent",
    ],
    "arvis.knowledge.knowledge_signal": [
        "KnowledgeSignal",
    ],
    "arvis.knowledge.knowledge_snapshot": [
        "KnowledgeSnapshot",
    ],
    "arvis.knowledge.knowledge_state": [
        "KnowledgeState",
    ],
    "arvis.math.core.contraction_monitor_core": [
        "ContractionMonitorCore",
        "MonitorConfig",
    ],
    "arvis.math.lyapunov.lyapunov_gate": [
        "lyapunov_gate",
    ],
    "arvis.memory.governance": [
        "Governance",
        "GovernanceEncryption",
        "GovernancePrincipal",
        "GovernanceRetention",
        "GovernanceSharing",
        "GovernanceVisibility",
    ],
    "arvis.memory.memory_long_entry": [
        "MemoryLongEntry",
        "MemoryLongType",
    ],
    "arvis.memory.memory_long_policy_gate": [
        "MemoryLongPolicyGate",
    ],
    "arvis.memory.memory_long_projector": [
        "MemoryLongContextProjector",
    ],
    "arvis.memory.memory_long_record": [
        "MemoryLongRecord",
    ],
    "arvis.memory.memory_long_registry": [
        "DEFAULT_MEMORY_LONG_REGISTRY",
    ],
    "arvis.memory.memory_long_repository": [
        "MemoryLongRepository",
    ],
    "arvis.memory.memory_long_snapshot": [
        "MemoryLongSnapshot",
    ],
    "arvis.telemetry": [
        "InMemoryTelemetrySink",
        "TelemetryKind",
    ],
    "arvis.tools.base": [
        "BaseTool",
    ],
    "arvis.tools.executor": [
        "ToolExecutor",
    ],
    "arvis.tools.manager": [
        "ToolManager",
    ],
    "arvis.tools.registry": [
        "ToolRegistry",
    ],
    "arvis.tools.spec": [
        "ToolSpec",
    ],
}


_PAIRS: list[tuple[str, str]] = [
    (module, symbol)
    for module, symbols in CONSUMED_SURFACE.items()
    for symbol in symbols
]


@pytest.mark.parametrize(
    ("module", "symbol"),
    _PAIRS,
    ids=[f"{module}:{symbol}" for module, symbol in _PAIRS],
)
def test_consumed_symbol_resolves(module: str, symbol: str) -> None:
    """`from module import symbol` must still resolve in arvis.

    Mirrors Python import semantics: the name resolves if it is an
    attribute of the module, or (for submodule imports) if
    `module.symbol` is itself importable.
    """
    mod = importlib.import_module(module)
    if hasattr(mod, symbol):
        return
    try:
        importlib.import_module(f"{module}.{symbol}")
    except ImportError as exc:
        pytest.fail(
            f"veramem relies on `from {module} import {symbol}` but it no "
            f"longer resolves in arvis ({exc!r}); this breaks veramem prod."
        )
