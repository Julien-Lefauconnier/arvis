# tests/tools/test_tool_execution.py

import pytest

from arvis.adapters.tools.invocation import ToolInvocation
from arvis.tools.authorized_invocation import CapabilityActivationBinding
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry
from tests.fixtures.builders.effect_context_builder import build_effect_context


class DummyTool(BaseTool):
    name = "dummy"

    def execute(self, input_data):
        return {"ok": True, "input": input_data}


def _activate(authority, invocation):
    capability = authority.authorize(invocation)
    binding = CapabilityActivationBinding(
        receipt_id=f"receipt:{capability.nonce}",
        intent_sha256="a" * 64,
        run_id="run-1",
        causal_id=f"causal:{capability.nonce}",
        durable_position="1",
        store_fingerprint="db:test",
        committed_at="2026-07-19T00:00:00+00:00",
    )
    assert authority.activate(capability, binding) is True
    return capability


def test_direct_tool_execution_forbidden():
    registry = ToolRegistry()
    registry.register(DummyTool())

    executor = ToolExecutor(registry)

    with pytest.raises(RuntimeError, match="direct_tool_execution_forbidden"):
        executor.execute("dummy", {"x": 1})


def test_tool_called_from_runtime():
    registry = ToolRegistry()

    class DummyTool(BaseTool):
        name = "dummy"

        def execute(self, input_data):
            assert "context" not in input_data
            self.seen_context = input_data["effect_context"]

    registry.register(DummyTool())

    executor = ToolExecutor(registry)

    class DummyDecision:
        tool = "dummy"

    class DummyResult:
        action_decision = DummyDecision()

    class DummyCtx:
        def __init__(self):
            self.extra = {}

    ctx = DummyCtx()

    effect_context = build_effect_context(process_id="p")
    invocation = ToolInvocation(
        tool_name="dummy",
        payload={},
        effect_context=effect_context,
    )
    authority = executor._claim_minting_authority()
    authorized = _activate(authority, invocation)
    executor._execute_invocation(authorized, DummyResult(), ctx)

    tool = registry.get("dummy")
    assert tool is not None
    assert tool.seen_context is effect_context
    assert ctx.extra == {}


def test_tool_execution_authorized():
    registry = ToolRegistry()
    registry.register(DummyTool())

    executor = ToolExecutor(registry)

    class DummyDecision:
        tool = "dummy"
        tool_payload = {"x": 1}

    class DummyResult:
        action_decision = DummyDecision()

    class DummyCtx:
        def __init__(self):
            self.extra = {}

    ctx = DummyCtx()

    invocation = ToolInvocation(
        tool_name="dummy",
        payload={"x": 1},
        effect_context=build_effect_context(process_id="p"),
    )
    authority = executor._claim_minting_authority()
    authorized = _activate(authority, invocation)
    result = executor._execute_invocation(authorized, DummyResult(), ctx)

    assert result.success is True
    assert result.output["ok"] is True
    assert result.output["input"]["tool_payload"]["x"] == 1
    assert "context" not in result.output["input"]
    assert result.output["input"]["effect_context"] is invocation.effect_context


def test_tool_validation_and_execution_receive_no_runtime_context():
    class InspectingTool(BaseTool):
        name = "inspect"

        def __init__(self):
            self.seen = []

        def validate(self, input_data):
            assert "context" not in input_data
            self.seen.append(input_data["effect_context"])

        def execute(self, input_data):
            assert "context" not in input_data
            self.seen.append(input_data["effect_context"])
            return {"ok": True}

    registry = ToolRegistry()
    tool = InspectingTool()
    registry.register(tool)
    executor = ToolExecutor(registry)
    runtime_context = type("RuntimeContext", (), {"extra": {}})()
    effect_context = build_effect_context(process_id="p")
    invocation = ToolInvocation(
        tool_name="inspect",
        payload={},
        effect_context=effect_context,
    )

    class Result:
        action_decision = type("Decision", (), {"tool": "inspect"})()

    authority = executor._claim_minting_authority()
    authorized = _activate(authority, invocation)
    result = executor._execute_invocation(authorized, Result(), runtime_context)

    assert result is not None and result.success is True
    assert tool.seen == [effect_context, effect_context]
