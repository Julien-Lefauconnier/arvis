# tests/tools/test_tool_execution.py

import pytest

from arvis.tools.registry import ToolRegistry
from arvis.tools.executor import ToolExecutor
from arvis.tools.base import BaseTool


class DummyTool(BaseTool):
    name = "dummy"

    def execute(self, input_data):
        return {"ok": True, "input": input_data}


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
            input_data["context"].extra["called"] = True

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

    executor.execute(DummyResult(), ctx)

    assert ctx.extra.get("called") is True


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

    result = executor.execute_authorized(DummyResult(), ctx)

    assert result.success is True
    assert result.output["ok"] is True
    assert result.output["input"]["tool_payload"]["x"] == 1