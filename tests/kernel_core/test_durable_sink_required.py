# tests/kernel_core/test_durable_sink_required.py
"""Effectful production requires a durable intent sink (D4-e, P1-a6).

The refusal happens at the first EFFECT syscall, at the point of use:
before the intent is recorded and before the effect runs. A production
profile without effects stays valid without a sink; a local profile
never requires one (the in-memory journal stands).
"""

from types import SimpleNamespace

from arvis import CognitiveOS, CognitiveOSConfig
from arvis.kernel_core.access.models import (
    AccessContext,
    AuthenticatedPrincipal,
    Principal,
)
from arvis.kernel_core.syscalls.audit_sink import (
    AuditSinkDurabilityClass,
    AuditSinkManifest,
    InMemoryAuditSink,
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

_PROBE = "test.sink.effect"
_READ_PROBE = "test.sink.read"


def _allow_resolver(name):
    def _resolve(args, services):
        return AccessContext(
            principal=Principal(user_id="u1"),
            effect=SyscallEffect.EFFECT,
            resource_owner_id="u1",
            syscall_name=name,
        )

    return _resolve


def _register_effect_probe(calls):
    def _fn(handler, ctx=None, causal_id=None, **kwargs):
        calls.append(causal_id)
        return SyscallResult(success=True, result={"ok": True})

    register_syscall(
        _PROBE, effect=SyscallEffect.EFFECT, access=_allow_resolver(_PROBE)
    )(_fn)


def _cleanup():
    for name in (_PROBE, _READ_PROBE):
        SYSCALL_REGISTRY.pop(name, None)
        SYSCALL_DESCRIPTORS.pop(name, None)


def _handler(*, require_sink: bool, sink=None):
    return SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            audit_intent_sink=sink,
            require_durable_intent_sink=require_sink,
            require_authenticated_principal=require_sink,
        ),
    )


def _production_ctx():
    return SimpleNamespace(
        extra={},
        user_id="u1",
        principal=AuthenticatedPrincipal(
            user_id="u1",
            authentication_source="test",
            authentication_strength="strong",
        ),
    )


class _DatabaseSink(InMemoryAuditSink):
    def __init__(self) -> None:
        super().__init__()
        self.manifest = AuditSinkManifest(
            sink_kind="test_database",
            durability_class=AuditSinkDurabilityClass.DATABASE,
            transactional=True,
            append_only=True,
            store_fingerprint=self._store_fingerprint,
            implementation_version="1",
        )


def test_effect_without_sink_is_refused_under_production_posture():
    calls: list = []
    _register_effect_probe(calls)
    try:
        ctx = _production_ctx()
        result = _handler(require_sink=True).handle(
            Syscall(name=_PROBE, args={"ctx": ctx})
        )
        assert result.success is False
        assert result.error is not None
        assert result.error.details.get("reason_code") == "durable_sink_required"
        # Refused BEFORE anything ran or was recorded.
        assert calls == []
        assert "syscall_intents" not in ctx.extra
    finally:
        _cleanup()


def test_effect_with_durable_sink_succeeds_under_production_posture():
    # Campaign 6 (Lot 6, closes a8 section 14): a durability-requiring
    # profile needs a sink that PROVES persistence (receipts), so the
    # probe uses the reference DurableAuditSink; a bare callable is
    # refused below.
    calls: list = []
    sink = _DatabaseSink()
    _register_effect_probe(calls)
    try:
        ctx = _production_ctx()
        result = _handler(require_sink=True, sink=sink).handle(
            Syscall(name=_PROBE, args={"ctx": ctx})
        )
        assert result.success is True
        assert len(calls) == 1
        assert len(sink.entries) == 1
        assert len(sink.receipts) == 1
    finally:
        _cleanup()


def test_legacy_callable_sink_is_refused_under_production_posture():
    # The a8 section 14 finding verbatim: ``lambda intent: None``
    # satisfied every control. It no longer does where durability is
    # required.
    calls: list = []
    sink_entries: list = []
    _register_effect_probe(calls)
    try:
        ctx = _production_ctx()
        result = _handler(
            require_sink=True, sink=lambda entry: sink_entries.append(entry)
        ).handle(Syscall(name=_PROBE, args={"ctx": ctx}))
        assert result.success is False
        assert result.error is not None
        assert calls == []
        assert sink_entries == []
    finally:
        _cleanup()


def test_legacy_callable_sink_still_accepted_outside_durability_profiles():
    calls: list = []
    sink_entries: list = []
    _register_effect_probe(calls)
    try:
        ctx = SimpleNamespace(extra={}, user_id="u1")
        result = _handler(
            require_sink=False, sink=lambda entry: sink_entries.append(entry)
        ).handle(Syscall(name=_PROBE, args={"ctx": ctx}))
        assert result.success is True
        assert len(calls) == 1
        assert len(sink_entries) == 1
    finally:
        _cleanup()


def test_read_syscall_never_requires_a_sink():
    def _fn(handler, ctx=None, **kwargs):
        return SyscallResult(success=True, result={"ok": True})

    register_syscall(_READ_PROBE, effect=SyscallEffect.READ)(_fn)
    try:
        result = _handler(require_sink=True).handle(
            Syscall(name=_READ_PROBE, args={"ctx": SimpleNamespace(extra={})})
        )
        assert result.success is True
    finally:
        _cleanup()


def test_local_profile_never_requires_a_sink():
    calls: list = []
    _register_effect_probe(calls)
    try:
        ctx = SimpleNamespace(extra={}, user_id="u1")
        result = _handler(require_sink=False).handle(
            Syscall(name=_PROBE, args={"ctx": ctx})
        )
        assert result.success is True
        assert len(calls) == 1
    finally:
        _cleanup()


def test_production_run_without_effects_stays_valid_without_sink():
    # D4-e, second half: the refusal sits at the point of use, so a
    # production profile whose turns produce no effect keeps its
    # REQUIRED commitment without any sink configured.
    os_ = CognitiveOS(config=CognitiveOSConfig.production())
    view = os_.run("u1", {"risk": 0.9})
    assert view.global_commitment is not None
    assert view.to_dict()["audit_incomplete"] is False
