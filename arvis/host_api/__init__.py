# arvis/host_api/__init__.py

"""The host integration surface of arvis.

A host (the application embedding arvis) integrates the kernel through
the twelve capability modules of this package: engine, access, services,
vfs, tools, memory, knowledge, conversation, cognition, control, llm,
telemetry. Each module is a pure re-export layer: symbols stay defined
where they live, host_api pins the import paths and the compatibility
promise.

Stability: every module is stable (beta contract, deprecation window per
VERSIONING.md) except the modules listed in PROVISIONAL_MODULES, whose
surface may change in a minor release with a changelog entry.
"""

HOST_API_VERSION = "1.0"

PROVISIONAL_MODULES: frozenset[str] = frozenset({"control"})

__all__ = [
    "HOST_API_VERSION",
    "PROVISIONAL_MODULES",
]
