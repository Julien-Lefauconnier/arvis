"""RED contract for the VeraMem-facing ARVIS host surface 1.3.

This contract is intentionally host-facing only. It does not move VeraMem
business rules into ARVIS: it exposes the generic types a host must use to
compose ARVIS authorization and durable-audit boundaries without importing
kernel internals.
"""

from __future__ import annotations

import importlib


def test_host_api_version_advances_to_1_3() -> None:
    host_api = importlib.import_module("arvis.host_api")
    assert host_api.HOST_API_VERSION == "1.3"


def test_access_host_surface_exposes_generic_access_contract() -> None:
    public = importlib.import_module("arvis.host_api.access")
    decision = importlib.import_module("arvis.kernel_core.access.decision")
    models = importlib.import_module("arvis.kernel_core.access.models")

    expected = {
        "AccessContext": models.AccessContext,
        "AccessDecision": decision.AccessDecision,
        "AccessVerdict": decision.AccessVerdict,
        "ResolvedAccess": models.ResolvedAccess,
    }
    for name, internal in expected.items():
        assert getattr(public, name, None) is internal


def test_services_host_surface_exposes_syscall_effect_classification() -> None:
    public = importlib.import_module("arvis.host_api.services")
    registry = importlib.import_module("arvis.kernel_core.syscalls.syscall_registry")
    assert getattr(public, "SyscallEffect", None) is registry.SyscallEffect


def test_audit_host_surface_exposes_durable_sink_contract() -> None:
    public = importlib.import_module("arvis.host_api.audit")
    internal = importlib.import_module("arvis.kernel_core.syscalls.audit_sink")

    names = {
        "AuditReceipt",
        "AuditSinkDurabilityClass",
        "AuditSinkManifest",
        "DurableAuditSink",
        "InMemoryAuditSink",
    }
    assert set(public.__all__) == names
    for name in names:
        assert getattr(public, name, None) is getattr(internal, name)
