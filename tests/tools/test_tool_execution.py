# tests/tools/test_tool_execution.py

from arvis.tools.registry import ToolRegistry
from arvis.tools.executor import ToolExecutor
from arvis.tools.base import BaseTool


class DummyTool(BaseTool):
    name = "dummy"

    def execute(self, input_data):
        return {"ok": True, "input": input_data}


def test_tool_execution():
    registry = ToolRegistry()
    registry.register(DummyTool())

    executor = ToolExecutor(registry)

    result = executor.execute("dummy", {"x": 1})

    assert result["ok"] is True
    assert result["input"]["x"] == 1


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