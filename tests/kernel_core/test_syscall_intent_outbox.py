# tests/kernel_core/test_syscall_intent_outbox.py
"""Durable audit intent before effect (F-008-a5, outbox).

The intent precedes the effect: for any EFFECT syscall, an intent entry
carrying structural metadata only is journaled BEFORE the call, paired
with the result journal through the shared causal id, and handed to the
host sink when configured. Any failure to record the intent refuses the
syscall (fail-closed). An intent without a paired artifact afterwards
signals a crash during the effect: bounded, visible uncertainty.
"""

from types import SimpleNamespace

import pytest

from arvis.kernel_core.access.models import AccessContext, Principal
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.kernel_core.syscalls.syscall_registry import (
    SYSCALL_DESCRIPTORS,
    SYSCALL_REGISTRY,
    SyscallEffect,
    register_syscall,
)

EFFECT_PROBE = "test.outbox.effect"
READ_PROBE = "test.outbox.read"


def _allow_all_resolver(name):
    def _resolve(args, services):
        return AccessContext(
            principal=Principal(user_id="u1"),
            effect=SyscallEffect.EFFECT,
            resource_owner_id="u1",
            syscall_name=name,
        )

    return _resolve


def _cleanup(name):
    SYSCALL_REGISTRY.pop(name, None)
    SYSCALL_DESCRIPTORS.pop(name, None)


@pytest.fixture
def effect_probe():
    calls = []

    def _fn(handler, ctx=None, **kwargs):
        # Order proof: the intent must already be journaled when the
        # effect body runs.
        intents = ctx.extra.get("syscall_intents", []) if ctx is not None else []
        calls.append(
            {
                "intents_at_execution": [dict(i) for i in intents],
                "causal_id": kwargs.get("causal_id"),
            }
        )
        return SyscallResult(success=True, result={"ok": True})

    register_syscall(
        EFFECT_PROBE,
        effect=SyscallEffect.EFFECT,
        access=_allow_all_resolver(EFFECT_PROBE),
    )(_fn)
    try:
        yield calls
    finally:
        _cleanup(EFFECT_PROBE)


@pytest.fixture
def read_probe():
    def _fn(handler, ctx=None, **kwargs):
        return SyscallResult(success=True, result={"ok": True})

    register_syscall(READ_PROBE, effect=SyscallEffect.READ)(_fn)
    try:
        yield READ_PROBE
    finally:
        _cleanup(READ_PROBE)


def _handler(sink=None):
    return SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(audit_intent_sink=sink),
    )


def _ctx():
    return SimpleNamespace(extra={}, user_id="u1")


def test_intent_is_journaled_before_the_effect_runs(effect_probe):
    ctx = _ctx()
    result = _handler().handle(Syscall(name=EFFECT_PROBE, args={"ctx": ctx}))
    assert result.success is True
    # The effect body observed its own intent already journaled.
    assert len(effect_probe) == 1
    seen = effect_probe[0]["intents_at_execution"]
    assert len(seen) == 1
    assert seen[0]["kind"] == "syscall_intent"
    assert seen[0]["syscall"] == EFFECT_PROBE


def test_intent_causal_id_pairs_with_the_result_journal(effect_probe):
    ctx = _ctx()
    _handler().handle(Syscall(name=EFFECT_PROBE, args={"ctx": ctx}))
    intent = ctx.extra["syscall_intents"][0]
    journaled = ctx.extra["syscall_results"][-1]
    assert intent["causal_id"] == journaled["syscall_id"]
    assert effect_probe[0]["causal_id"] == intent["causal_id"]


def test_read_syscall_records_no_intent(read_probe):
    ctx = _ctx()
    result = _handler().handle(Syscall(name=read_probe, args={"ctx": ctx}))
    assert result.success is True
    assert "syscall_intents" not in ctx.extra


def test_sink_is_called_before_the_effect(effect_probe):
    sink_calls = []

    def sink(entry):
        sink_calls.append(dict(entry))

    ctx = _ctx()
    _handler(sink).handle(Syscall(name=EFFECT_PROBE, args={"ctx": ctx}))
    assert len(sink_calls) == 1
    assert sink_calls[0]["syscall"] == EFFECT_PROBE
    # Order proof: the effect body ran after the intent existed, and the
    # sink received the same causal id the body saw.
    assert sink_calls[0]["causal_id"] == effect_probe[0]["causal_id"]


def test_failing_sink_refuses_the_syscall_and_skips_the_effect(effect_probe):
    def sink(entry):
        raise RuntimeError("durable store unavailable")

    ctx = _ctx()
    result = _handler(sink).handle(Syscall(name=EFFECT_PROBE, args={"ctx": ctx}))
    assert result.success is False
    assert result.error is not None
    assert result.error.details.get("reason_code") == "audit_intent_failed"
    # Fail-closed: the effect body never ran.
    assert effect_probe == []


def test_sink_receives_a_copy_of_the_intent(effect_probe):
    def sink(entry):
        entry["syscall"] = "rewritten"

    ctx = _ctx()
    _handler(sink).handle(Syscall(name=EFFECT_PROBE, args={"ctx": ctx}))
    assert ctx.extra["syscall_intents"][0]["syscall"] == EFFECT_PROBE


def test_intent_carries_structural_metadata_only(effect_probe):
    ctx = _ctx()
    _handler().handle(
        Syscall(
            name=EFFECT_PROBE,
            args={"ctx": ctx, "secret_payload_content": "do not journal"},
        )
    )
    intent = ctx.extra["syscall_intents"][0]
    assert set(intent.keys()) == {
        "kind",
        "syscall",
        "causal_id",
        "tick",
        "process_id",
        "commitment_sha256",
    }
    # P0-3-a6: the engagement digest binds the parameters by hash only.
    assert len(intent["commitment_sha256"]) == 64
    assert "secret_payload_content" not in str(intent)


def test_denied_syscall_records_no_intent():
    # Authorization runs before the intent: a denied effect never
    # reaches the outbox.
    def _fn(handler, ctx=None, **kwargs):  # pragma: no cover
        raise AssertionError("must not run")

    def _deny_resolver(args, services):
        return AccessContext(
            principal=Principal(user_id="intruder"),
            effect=SyscallEffect.EFFECT,
            resource_owner_id="owner",
            syscall_name=EFFECT_PROBE,
        )

    register_syscall(EFFECT_PROBE, effect=SyscallEffect.EFFECT, access=_deny_resolver)(
        _fn
    )
    try:
        ctx = _ctx()
        result = _handler().handle(Syscall(name=EFFECT_PROBE, args={"ctx": ctx}))
        assert result.success is False
        assert "syscall_intents" not in ctx.extra
    finally:
        _cleanup(EFFECT_PROBE)


def test_real_tool_execution_pairs_intent_and_artifact():
    # Integration through the real tool.execute syscall.
    from arvis.tools.base import BaseTool
    from arvis.tools.executor import ToolExecutor
    from arvis.tools.manager import ToolManager
    from arvis.tools.registry import ToolRegistry
    from arvis.tools.spec import ToolSpec

    class _Tool(BaseTool):
        name = "outbox_tool"
        spec = ToolSpec(name="outbox_tool", description="outbox probe")

        def execute(self, input_data):
            return {"ok": True}

    registry = ToolRegistry()
    registry.register(_Tool())
    executor = ToolExecutor(registry)
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            tool_executor=executor,
            tool_manager=ToolManager(registry, executor),
        ),
    )
    ctx = _ctx()
    decision = SimpleNamespace(tool="outbox_tool", tool_payload={})
    result = handler.handle(
        Syscall(
            name="tool.execute",
            args={"result": SimpleNamespace(action_decision=decision), "ctx": ctx},
        )
    )
    assert result.success is True
    intent = ctx.extra["syscall_intents"][0]
    journaled = ctx.extra["syscall_results"][-1]
    assert intent["syscall"] == "tool.execute"
    assert intent["causal_id"] == journaled["syscall_id"]
