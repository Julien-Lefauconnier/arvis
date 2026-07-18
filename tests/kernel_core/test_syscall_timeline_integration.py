# tests/kernel_core/test_syscall_timeline_integration.py

from __future__ import annotations

from types import SimpleNamespace

from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.kernel.execution.cognitive_execution_state import CognitiveExecutionState
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry


class DummyTool(BaseTool):
    name = "dummy"

    def execute(self, input_data):
        return {"ok": True}


class DummySpec:
    def __init__(self, name):
        self.name = name


def test_syscall_emits_runtime_signal(monkeypatch):
    monkeypatch.setattr(
        ToolPolicyEvaluator,
        "evaluate",
        lambda invocation, registry: SimpleNamespace(
            allowed=True,
            reason=None,
        ),
    )
    runtime_state = CognitiveRuntimeState()

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
        runtime_state=runtime_state,
        scheduler=None,
        services=services,
    )

    runtime = CognitiveExecutionState()
    ctx = SimpleNamespace(
        user_id="u1",
        extra={},
        execution=SimpleNamespace(execution_state=runtime),
    )

    class DummyDecision:
        tool = "dummy"
        tool_payload = {}
        spec = DummySpec("dummy")

    class DummyResult:
        action_decision = DummyDecision()
        spec = DummySpec(action_decision.tool)

    dummy_result = DummyResult()
    authorization = manager.authorize(dummy_result, ctx)
    syscall = Syscall(
        name="tool.execute",
        args={
            "result": dummy_result,
            "ctx": ctx,
            "process_id": "p1",
            "tick": 1,
            "authorization": authorization,
        },
    )

    result = handler.handle(syscall)

    assert result.success is True

    syscall_results = ctx.extra.get("syscall_results", [])
    assert len(syscall_results) == 1
    assert runtime.syscall_results is syscall_results
    assert runtime.metadata["last_syscall_result"] is syscall_results[0]

    entry = syscall_results[0]
    assert entry["syscall"] == "tool.execute"
    assert entry["success"] is True

    signals = runtime_state.timeline.list_signals()
    assert len(signals) >= 1

    last_signal = signals[-1]

    assert hasattr(last_signal, "key")
    assert hasattr(last_signal, "timestamp")
    assert hasattr(last_signal, "subject_ref")

    assert "process:p1" in last_signal.subject_ref

    code = getattr(last_signal.key, "code", "")
    assert code in {
        "decision_emitted",
        "ghost_signal",
    }
