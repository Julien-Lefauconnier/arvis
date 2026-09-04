"""Contract test: the arvis surface consumed by veramem must keep resolving.

veramem (the proprietary product) imports arvis through 214 import
lines across 137 files, almost all of them deep-path
`from <module> import <symbol>` bindings on modules this repository
declares internal. This file freezes that exact surface so a
consolidation (removal, memory rework, gate or projection changes)
cannot silently break veramem in production.

Source of truth: a cartography of veramem's imports, re-measured from
the 2026-09-04 repomix. The previous one dated from 2026-07-02 and had
drifted in both directions: seven bindings veramem consumes were not
pinned here, including `AuthenticatedPrincipal` (the single most
imported arvis symbol in that product, 40 files) and
`ArvisSecurityError`, while six pins protected symbols veramem had
stopped using. A safety net with holes is worse than no net, because it
is trusted.

If arvis is refactored and one of these bindings stops resolving, this
test fails fail-closed and names the exact broken (module, symbol). It is
a pure arvis-side test: it does not import veramem, only asserts that
arvis still exposes what veramem relies on.

This file is a transitional obligation, not a second public surface.
Every symbol below now has a home in `arvis.host_api` (1.2 added the
four that did not), so the intended end state is a veramem that imports
the pinned surface and an arvis free to move its internals again. Until
that migration happens, merging micro-modules would break veramem in
production while every arvis gate stayed green: this file is what makes
that consequence visible instead of surprising.
"""

import importlib

import pytest

# THE CONTRACT. Any change here is a change to veramem's supported surface.
CONSUMED_SURFACE: dict[str, list[str]] = {
    "arvis": [
        "ArvisEngine",
        "CognitiveOSConfig",
        "CognitiveResultView",
        "DecisionStatus",
        "RESULT_SCHEMA_VERSION",
        "load_result_schema",
        "verify_reflexive_attestation",
    ],
    "arvis.adapters.llm.contracts": [
        "LLMResponse",
    ],
    "arvis.cognition.control.cognitive_control_engine": [
        "CognitiveControlDeps",
        "CognitiveControlEngine",
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
    "arvis.errors.base": [
        "ArvisSecurityError",
    ],
    "arvis.kernel_core.access.models": [
        "AuthenticatedPrincipal",
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


def test_every_consumed_symbol_has_a_public_home() -> None:
    """The migration out of this file stays possible at every commit.

    This contract exists because one host is pinned to internal paths.
    It stops being needed the day that host imports `arvis.host_api`
    instead, and that day only arrives if every symbol it depends on
    has a supported home to move to. Adding an internal binding here
    without a public equivalent would quietly extend the transition
    forever, so the obligation is checked rather than intended.
    """
    import pkgutil

    import arvis
    from arvis import host_api

    public: set[str] = set(arvis.__all__)
    for module_info in pkgutil.iter_modules(host_api.__path__):
        module = importlib.import_module(f"arvis.host_api.{module_info.name}")
        public |= set(getattr(module, "__all__", ()))

    homeless = sorted({symbol for _, symbol in _PAIRS if symbol not in public})
    assert not homeless, (
        f"these symbols are consumed through internal paths and have no "
        f"home on a public surface: {homeless}. Re-export them from the "
        "matching arvis.host_api module (additive, bump HOST_API_VERSION) "
        "so the host has somewhere supported to migrate to."
    )
