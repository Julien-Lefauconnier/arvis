# tests/kernel_core/test_syscall_handler.py

from types import SimpleNamespace

from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry



def make_ctx():
    return SimpleNamespace(extra={})

class DummyTool(BaseTool):
    name = "dummy"

    def execute(self, input_data):
        assert input_data["tool_payload"]["x"] == 1
        return {"ok": True, "input": input_data}


def test_syscall_journal():
    ctx = type("Ctx", (), {"extra": {}})()

    services = KernelServiceRegistry()

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=services,
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

    services = KernelServiceRegistry(tool_executor=executor)

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=services,
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

    services = KernelServiceRegistry(tool_executor=executor)

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=services,
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


def test_memory_syscalls_replay_policy():
    handler = SyscallHandler(None, scheduler=None)

    assert handler._default_replay_policy("memory.get") == "journal_only_replay"
    assert handler._default_replay_policy("memory.list") == "journal_only_replay"
    assert handler._default_replay_policy("memory.snapshot") == "journal_only_replay"
    assert handler._default_replay_policy("memory.put") == "journal_only_replay"
    assert handler._default_replay_policy("memory.delete") == "journal_only_replay"


def test_memory_journal_metadata():
    ctx = make_ctx()
    handler = SyscallHandler(None, scheduler=None)

    syscall = Syscall(
        name="memory.get",
        args={"key": "k", "namespace": "n", "user_id": "u", "ctx": ctx},
    )

    handler.handle(syscall)

    entry = ctx.extra["syscall_results"][0]

    assert entry["memory_key"] == "k"
    assert entry["memory_namespace"] == "n"
    assert entry["memory_user_id"] == "u"


def test_memory_snapshot_journal_meta_only():
    ctx = make_ctx()
    handler = SyscallHandler(None, scheduler=None)

    # mock syscall to return snapshot
    result = SyscallResult(
        success=True,
        result={"total": 5, "active": 3, "entries": ["should_not_be_logged"]},
    )

    handler._journal(ctx, Syscall("memory.snapshot", {"ctx": ctx}), result, 0)

    entry = ctx.extra["syscall_results"][0]

    assert "memory_snapshot_meta" in entry
    assert entry["memory_snapshot_meta"]["total"] == 5

    # critical invariant
    assert "result" not in entry
