# arvis/host_api/__init__.py

"""The host integration surface of arvis.

A host (the application embedding arvis) integrates the kernel through
the thirteen capability modules of this package: engine, access,
services, vfs, tools, memory, knowledge, conversation, cognition,
control, llm, telemetry, errors. Each module is a pure re-export layer:
symbols stay defined where they live, host_api pins the import paths and
the compatibility promise.

Stability: every module is stable (beta contract, deprecation window per
VERSIONING.md) except the modules listed in PROVISIONAL_MODULES, whose
surface may change in a minor release with a changelog entry.
"""

# 1.2 (campaign HOST-SURFACE, 2026-09-04): additive only, and driven by
# measurement rather than guesswork. A cartography of the one real
# integration (veramem) showed 214 import lines against internal module
# paths, 57 of whose 61 symbols already had a home here; these are the
# four that did not, so the last reason to import an internal path is
# gone. conversation gains ContinuationResolver; memory gains
# MemoryLongContextProjector and DEFAULT_MEMORY_LONG_REGISTRY; a new
# errors module exposes the two exceptions a host catches.
#
# 1.1 (campaign SURFACE, DM-S2): additive only. engine gains
# CognitiveOS; access gains AuthenticatedPrincipal; tools gains
# ToolInvocation, ToolPolicyEvaluator, AuthorizedEffectContext.
HOST_API_VERSION = "1.2"

PROVISIONAL_MODULES: frozenset[str] = frozenset({"control"})

__all__ = [
    "HOST_API_VERSION",
    "PROVISIONAL_MODULES",
]
