# tests/kernel_core/test_syscall_timeline_integration.py

from __future__ import annotations

from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.runtime.cognitive_runtime_state import CognitiveRuntimeState
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry


class DummyTool(BaseTool):
    name = "dummy"

    def execute(self, input_data):
        return {"ok": True}


def test_syscall_emits_runtime_signal():
    runtime_state = CognitiveRuntimeState()

    registry = ToolRegistry()
    registry.register(DummyTool())
    executor = ToolExecutor(registry)

    services = KernelServiceRegistry(tool_executor=executor)

    handler = SyscallHandler(
        runtime_state=runtime_state,
        scheduler=None,
        services=services,
    )

    ctx = type("Ctx", (), {"extra": {}})()

    class DummyDecision:
        tool = "dummy"
        tool_payload = {}

    class DummyResult:
        action_decision = DummyDecision()

    syscall = Syscall(
        name="tool.execute",
        args={
            "result": DummyResult(),
            "ctx": ctx,
            "process_id": "p1",
            "tick": 1,
        },
    )

    result = handler.handle(syscall)

    assert result.success is True

    syscall_results = ctx.extra.get("syscall_results", [])
    assert len(syscall_results) == 1

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