"""Production durability manifest and receipt/store integrity."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from types import SimpleNamespace

from arvis.kernel_core.access.models import AccessContext, Principal
from arvis.kernel_core.syscalls.audit_sink import (
    AuditReceipt,
    AuditSinkDurabilityClass,
    AuditSinkManifest,
    InMemoryAuditSink,
    production_sink_manifest,
)
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.kernel_core.syscalls.syscall_registry import (
    SYSCALL_DESCRIPTORS,
    SYSCALL_REGISTRY,
    SyscallEffect,
    register_syscall,
)

_PROBE = "test.audit.manifest.effect"


def _manifest(
    fingerprint: str,
    *,
    durability: AuditSinkDurabilityClass = AuditSinkDurabilityClass.DATABASE,
    transactional: bool = True,
    append_only: bool = True,
) -> AuditSinkManifest:
    return AuditSinkManifest(
        sink_kind="test_sink",
        durability_class=durability,
        transactional=transactional,
        append_only=append_only,
        store_fingerprint=fingerprint,
        implementation_version="1",
    )


class _DatabaseSink(InMemoryAuditSink):
    def __init__(self) -> None:
        super().__init__()
        self.manifest = _manifest(self._store_fingerprint)


class _FixedPositionSink:
    def __init__(self, *, receipt_fingerprint: str = "db:fixed") -> None:
        self.manifest = _manifest("db:fixed")
        self.receipt_fingerprint = receipt_fingerprint

    def append(self, intent):
        return AuditReceipt(
            receipt_id=secrets.token_hex(8),
            run_id=intent.get("run_id"),
            causal_id=str(intent.get("causal_id", "")),
            intent_sha256=str(intent.get("commitment_sha256", "")),
            durable_position="same-position",
            store_fingerprint=self.receipt_fingerprint,
            committed_at=datetime.now(UTC).isoformat(),
        )


def _register(calls: list[str]) -> None:
    def _resolve(args, services):
        return AccessContext(
            principal=Principal(user_id="u1"),
            effect=SyscallEffect.EFFECT,
            resource_owner_id="u1",
            syscall_name=_PROBE,
        )

    @register_syscall(_PROBE, effect=SyscallEffect.EFFECT, access=_resolve)
    def _probe(handler, ctx=None, causal_id=None):
        calls.append(str(causal_id))
        return SyscallResult(success=True, result={"ok": True})


def _cleanup() -> None:
    SYSCALL_REGISTRY.pop(_PROBE, None)
    SYSCALL_DESCRIPTORS.pop(_PROBE, None)


def _handler(sink) -> SyscallHandler:
    return SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            audit_intent_sink=sink,
            require_durable_intent_sink=True,
        ),
    )


def _ctx():
    return SimpleNamespace(extra={}, user_id="u1")


def test_production_manifest_accepts_only_qualified_classes() -> None:
    database = _DatabaseSink()
    assert production_sink_manifest(database) == (database.manifest, None)

    memory = InMemoryAuditSink()
    assert production_sink_manifest(memory)[1] == "audit_sink_durability_class_refused"

    for transactional, append_only, reason in (
        (False, True, "audit_sink_transaction_required"),
        (True, False, "audit_sink_append_only_required"),
    ):
        sink = _DatabaseSink()
        sink.manifest = _manifest(
            sink._store_fingerprint,
            transactional=transactional,
            append_only=append_only,
        )
        assert production_sink_manifest(sink)[1] == reason


def test_sink_without_manifest_is_refused_before_effect() -> None:
    calls: list[str] = []
    _register(calls)
    try:
        sink = SimpleNamespace(append=lambda intent: None)
        result = _handler(sink).handle(Syscall(name=_PROBE, args={"ctx": _ctx()}))
        assert result.success is False
        assert result.error is not None
        assert result.error.details["reason_code"] == "audit_sink_manifest_required"
        assert calls == []
    finally:
        _cleanup()


def test_receipt_fingerprint_must_match_manifest() -> None:
    calls: list[str] = []
    _register(calls)
    try:
        result = _handler(_FixedPositionSink(receipt_fingerprint="db:other")).handle(
            Syscall(name=_PROBE, args={"ctx": _ctx()})
        )
        assert result.success is False
        assert result.error is not None
        assert result.error.details["reason_code"] == "invalid_audit_receipt"
        assert (
            result.error.details["receipt_reason"]
            == "receipt_store_fingerprint_mismatch"
        )
        assert calls == []
    finally:
        _cleanup()


def test_durable_position_cannot_be_reused() -> None:
    calls: list[str] = []
    _register(calls)
    try:
        handler = _handler(_FixedPositionSink())
        first_ctx = _ctx()
        second_ctx = _ctx()
        assert handler.handle(Syscall(name=_PROBE, args={"ctx": first_ctx})).success
        second = handler.handle(Syscall(name=_PROBE, args={"ctx": second_ctx}))
        assert second.success is False
        assert second.error is not None
        assert second.error.details["reason_code"] == "audit_receipt_position_reused"
        assert len(calls) == 1
    finally:
        _cleanup()
