# tests/kernel_core/test_kernel_syscalls_end_to_end.py
"""Kernel-internal syscalls, end to end on the real registry (P0-4-a6).

Campaign-3 lesson applied: the governed invariants are exercised on the
REAL registered syscalls with real runtime objects, not on probes. The
uniform contract (`ctx=None, causal_id=None`) makes the four
kernel-internal syscalls functionally reachable under their governance:
kernel principal on the trusted context channel succeeds with a paired
intent, anything else is denied, and a failing resolver or policy is
normalized at the boundary (P1-13-a6), never leaked.
"""

from types import SimpleNamespace

import pytest

from arvis.kernel_core.access.models import (
    KERNEL_PRINCIPAL,
    AccessContext,
    Principal,
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
from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState


class _SchedulerStub:
    def __init__(self) -> None:
        self.enqueued: list = []
        self.suspended: list = []
        self.resumed: list = []

    def enqueue(self, process) -> None:
        self.enqueued.append(process)

    def suspend(self, process_id) -> None:
        self.suspended.append(process_id)

    def resume(self, process_id) -> None:
        self.resumed.append(process_id)


def _handler(services: KernelServiceRegistry | None = None):
    scheduler = _SchedulerStub()
    handler = SyscallHandler(
        runtime_state=CognitiveRuntimeState(),
        scheduler=scheduler,
        services=services or KernelServiceRegistry(),
    )
    return handler, scheduler


def _kernel_ctx():
    return SimpleNamespace(extra={}, principal=KERNEL_PRINCIPAL)


def _user_ctx():
    return SimpleNamespace(extra={}, principal=Principal(user_id="u1"))


# ---------------------------------------------------------------
# Happy path: kernel principal, real syscalls, intent paired
# ---------------------------------------------------------------


def test_process_spawn_succeeds_with_kernel_context():
    handler, scheduler = _handler()
    ctx = _kernel_ctx()
    process = SimpleNamespace(process_id="p1")
    result = handler.handle(
        Syscall(name="process.spawn", args={"process": process, "ctx": ctx})
    )
    assert result.success is True
    assert scheduler.enqueued == [process]
    intent = ctx.extra["syscall_intents"][0]
    journaled = ctx.extra["syscall_results"][-1]
    assert intent["syscall"] == "process.spawn"
    assert intent["causal_id"] == journaled["syscall_id"]


@pytest.mark.parametrize(
    ("name", "args_key", "value", "attr"),
    [
        ("process.suspend", "process_id", "p1", "suspended"),
        ("process.resume", "process_id", "p1", "resumed"),
    ],
)
def test_process_lifecycle_syscalls_succeed_with_kernel_context(
    name, args_key, value, attr
):
    handler, scheduler = _handler()
    ctx = _kernel_ctx()
    result = handler.handle(Syscall(name=name, args={args_key: value, "ctx": ctx}))
    assert result.success is True
    assert getattr(scheduler, attr) == [value]
    assert ctx.extra["syscall_intents"][0]["syscall"] == name


def test_interrupt_emit_succeeds_with_kernel_context():
    handler, _ = _handler()
    ctx = _kernel_ctx()
    interrupt = SimpleNamespace(kind="test_interrupt")
    result = handler.handle(
        Syscall(name="interrupt.emit", args={"interrupt": interrupt, "ctx": ctx})
    )
    assert result.success is True
    intent = ctx.extra["syscall_intents"][0]
    journaled = ctx.extra["syscall_results"][-1]
    assert intent["causal_id"] == journaled["syscall_id"]


# ---------------------------------------------------------------
# Denials: no principal, user principal
# ---------------------------------------------------------------


def test_process_spawn_denied_without_principal():
    handler, scheduler = _handler()
    ctx = SimpleNamespace(extra={})
    result = handler.handle(
        Syscall(
            name="process.spawn",
            args={"process": SimpleNamespace(), "ctx": ctx},
        )
    )
    assert result.success is False
    assert scheduler.enqueued == []
    assert "syscall_intents" not in ctx.extra  # denied before the outbox


def test_process_spawn_denied_for_user_principal():
    handler, scheduler = _handler()
    ctx = _user_ctx()
    result = handler.handle(
        Syscall(
            name="process.spawn",
            args={"process": SimpleNamespace(), "ctx": ctx},
        )
    )
    assert result.success is False
    assert scheduler.enqueued == []


@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("process.suspend", {"process_id": "p1"}),
        ("process.resume", {"process_id": "p1"}),
        ("interrupt.emit", {"interrupt": SimpleNamespace()}),
    ],
)
def test_other_kernel_syscalls_denied_without_kernel_principal(name, args):
    handler, _ = _handler()
    result = handler.handle(Syscall(name=name, args={**args, "ctx": _user_ctx()}))
    assert result.success is False


# ---------------------------------------------------------------
# Normalized boundary (P1-13-a6)
# ---------------------------------------------------------------

_PROBE = "test.boundary.effect"


def _register_probe(access):
    def _fn(handler, ctx=None, **kwargs):  # pragma: no cover - refused before
        raise AssertionError("must not run")

    register_syscall(_PROBE, effect=SyscallEffect.EFFECT, access=access)(_fn)


def _cleanup_probe():
    SYSCALL_REGISTRY.pop(_PROBE, None)
    SYSCALL_DESCRIPTORS.pop(_PROBE, None)


def test_raising_resolver_is_normalized_to_authorization_failure():
    def _raising(args, services):
        raise RuntimeError("resolver crashed")

    _register_probe(_raising)
    try:
        handler, _ = _handler()
        result = handler.handle(Syscall(name=_PROBE, args={"ctx": _kernel_ctx()}))
        assert isinstance(result, SyscallResult)
        assert result.success is False
        assert result.error is not None
        assert result.error.details.get("reason_code") == "authorization_failure"
    finally:
        _cleanup_probe()


def test_raising_authorization_policy_is_normalized():
    def _resolver(args, services):
        return AccessContext(
            principal=KERNEL_PRINCIPAL,
            effect=SyscallEffect.EFFECT,
            resource_owner_id="__kernel__",
            syscall_name=_PROBE,
        )

    class _RaisingPolicy:
        def decide(self, context):
            raise RuntimeError("policy crashed")

    _register_probe(_resolver)
    try:
        handler, _ = _handler(
            KernelServiceRegistry(authorization_service=_RaisingPolicy())
        )
        result = handler.handle(Syscall(name=_PROBE, args={"ctx": _kernel_ctx()}))
        assert result.success is False
        assert result.error.details.get("reason_code") == "authorization_failure"
    finally:
        _cleanup_probe()


def test_normalized_refusal_is_journaled():
    def _raising(args, services):
        raise RuntimeError("resolver crashed")

    _register_probe(_raising)
    try:
        handler, _ = _handler()
        ctx = _kernel_ctx()
        handler.handle(Syscall(name=_PROBE, args={"ctx": ctx}))
        journaled = ctx.extra["syscall_results"][-1]
        assert journaled["syscall"] == _PROBE
        assert journaled["success"] is False
    finally:
        _cleanup_probe()
