# tests/kernel_core/test_syscall_handler.py

from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.kernel_core.syscalls.syscall import Syscall

from arvis.tools.registry import ToolRegistry
from arvis.tools.executor import ToolExecutor
from arvis.tools.base import BaseTool


class DummyTool(BaseTool):
    name = "dummy"

    def execute(self, input_data):
        assert input_data["tool_payload"]["x"] == 1
        return {"ok": True, "input": input_data}


def test_syscall_journal():
    ctx = type("Ctx", (), {"extra": {}})()

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        tool_executor=None,
    )

    syscall = Syscall(
        name="unknown.test",
        args={"ctx": ctx},
    )

    result = handler.handle(syscall)

    assert result.success is False

    assert "syscall_results" in ctx.extra
    entry = ctx.extra["syscall_results"][0]

    assert entry["syscall"] == "unknown.test"
    assert entry["success"] is False
    assert "syscall_id" in entry
    assert entry["replay_policy"] == "unknown"
    assert entry["error"] == "unknown_syscall:unknown.test"


def test_tool_execute_syscall():
    registry = ToolRegistry()

    registry.register(DummyTool())

    executor = ToolExecutor(registry)

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        tool_executor=executor,
    )

    ctx = type("Ctx", (), {"extra": {}})()

    class DummyDecision:
        tool = "dummy"
        tool_payload = {"x": 1}

    class DummyResult:
        action_decision = DummyDecision()

    syscall = Syscall(
        name="tool.execute",
        args={
            "result": DummyResult(),
            "ctx": ctx,
        },
    )

    result = handler.handle(syscall)
    print(type(result.result))

    assert result.success is True
    assert result.result is not None
    assert result.result.output["ok"] is True
    assert result.result.output["input"]["tool_payload"]["x"] == 1

    entry = ctx.extra["syscall_results"][0]
    assert entry["syscall"] == "tool.execute"
    assert entry["success"] is True
    assert "syscall_id" in entry
    assert entry["replay_policy"] == "journal_only_replay"


def test_tool_execute_syscall_failure():
    class FailingTool(BaseTool):
        name = "fail"

        def execute(self, input_data):
            raise ValueError("boom")

    registry = ToolRegistry()
    registry.register(FailingTool())

    executor = ToolExecutor(registry)

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        tool_executor=executor,
    )

    ctx = type("Ctx", (), {"extra": {}})()

    class DummyDecision:
        tool = "fail"

    class DummyResult:
        action_decision = DummyDecision()

    syscall = Syscall(
        name="tool.execute",
        args={"result": DummyResult(), "ctx": ctx},
    )

    result = handler.handle(syscall)

    assert result.success is False
    assert result.error == "boom"

    entry = ctx.extra["syscall_results"][0]
    assert entry["syscall"] == "tool.execute"
    assert entry["success"] is False
    assert "syscall_id" in entry
    assert entry["replay_policy"] == "journal_only_replay"
    assert entry["error"] == "boom"