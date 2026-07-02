# tests/kernel_core/test_syscall_handler.py

from types import SimpleNamespace

from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry


def make_ctx():
    return SimpleNamespace(extra={})


class DummyTool(BaseTool):
    name = "dummy"

    def execute(self, input_data):
        assert input_data["tool_payload"]["x"] == 1
        return {"ok": True, "input": input_data}


class DummySpec:
    def __init__(self, name):
        self.name = name


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

    assert isinstance(entry["error"], dict)
    assert entry["error"]["code"] == "unknown_syscall"


def test_tool_execute_syscall_policy_denied():
    registry = ToolRegistry()
    registry.register(DummyTool())
    executor = ToolExecutor(registry)
    manager = ToolManager(
        registry=registry,
        executor=executor,
    )

    services = KernelServiceRegistry(
        tool_executor=executor,
        tool_manager=manager,
    )

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=services,
    )

    ctx = type("Ctx", (), {"extra": {}})()

    class DummyDecision:
        tool = "dummy"
        tool_payload = {"x": 1}
        spec = DummySpec("dummy")

    class DummyResult:
        action_decision = DummyDecision()
        spec = DummySpec(action_decision.tool)

    syscall = Syscall(
        name="tool.execute",
        args={
            "result": DummyResult(),
            "ctx": ctx,
        },
    )

    result = handler.handle(syscall)

    assert result.success is False
    assert result.error is not None

    entry = ctx.extra["syscall_results"][0]
    assert entry["syscall"] == "tool.execute"
    assert entry["success"] is False
    assert "syscall_id" in entry
    assert entry["replay_policy"] == "journal_only_replay"
    assert "error" in entry


def test_tool_execute_syscall_failure(monkeypatch):
    class FailingTool(BaseTool):
        name = "fail"

        def execute(self, input_data):
            raise ValueError("boom")

    registry = ToolRegistry()
    registry.register(FailingTool())
    executor = ToolExecutor(registry)
    manager = ToolManager(
        registry=registry,
        executor=executor,
    )

    services = KernelServiceRegistry(
        tool_executor=executor,
        tool_manager=manager,
    )

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=services,
    )

    monkeypatch.setattr(
        ToolPolicyEvaluator,
        "evaluate",
        lambda invocation, registry: SimpleNamespace(
            allowed=True,
            reason=None,
        ),
    )

    ctx = type("Ctx", (), {"extra": {}})()

    class DummyDecision:
        tool = "fail"
        tool_payload = {}
        spec = DummySpec("fail")

    class DummyResult:
        action_decision = DummyDecision()
        spec = DummySpec(action_decision.tool)

    syscall = Syscall(
        name="tool.execute",
        args={"result": DummyResult(), "ctx": ctx},
    )

    result = handler.handle(syscall)

    assert result.success is False
    assert result.error is not None

    assert result.error.code == "tool_execution_error"
    assert result.error.message == "boom"

    assert result.error.cause is not None
    assert result.error.cause.code == "ValueError"
    assert result.error.cause.message == "boom"

    entry = ctx.extra["syscall_results"][-1]

    assert entry["syscall"] == "tool.execute"
    assert entry["success"] is False

    assert "syscall_id" in entry
    assert entry["replay_policy"] == "journal_only_replay"

    assert isinstance(entry["error"], dict)

    assert entry["error"]["code"] == "tool_execution_error"
    assert entry["error"]["message"] == "boom"

    assert entry["error"]["domain"] == "tool"

    assert entry["error"]["details"]["classification"] == "external"

    assert "error" in entry


def test_tool_execute_syscall_success(monkeypatch):
    registry = ToolRegistry()
    registry.register(DummyTool())
    executor = ToolExecutor(registry)
    manager = ToolManager(
        registry=registry,
        executor=executor,
    )

    # --- FORCE POLICY ALLOWED ---
    from arvis.adapters.tools.policy import ToolPolicyEvaluator

    monkeypatch.setattr(
        ToolPolicyEvaluator,
        "evaluate",
        lambda invocation, registry: SimpleNamespace(
            allowed=True,
            reason=None,
        ),
    )

    services = KernelServiceRegistry(
        tool_executor=executor,
        tool_manager=manager,
    )

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=services,
    )

    ctx = make_ctx()

    class DummyDecision:
        tool = "dummy"
        tool_payload = {"x": 1}

    class DummyResult:
        action_decision = DummyDecision()

    result = handler.handle(
        Syscall(
            name="tool.execute",
            args={"result": DummyResult(), "ctx": ctx},
        )
    )

    assert result.success is True
    assert result.result.output["ok"] is True


def test_syscall_handler_suppresses_journal_failure(monkeypatch):
    ctx = make_ctx()
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(),
    )

    monkeypatch.setattr(
        handler,
        "_journal",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("journal boom")),
    )

    result = handler.handle(Syscall(name="unknown.test", args={"ctx": ctx}))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "unknown_syscall"

    errors = ctx.extra.get("errors", [])

    assert any(
        err.get("details", {}).get("component") == "SyscallHandler._journal"
        and err.get("details", {}).get("recovery") == "journal_failure_suppressed"
        for err in errors
        if isinstance(err, dict)
    )
